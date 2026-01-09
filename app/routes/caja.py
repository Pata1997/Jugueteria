"""
Rutas para la gestión de caja
Incluye: apertura, cierre, arqueo y consulta de estado
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Caja, AperturaCaja, Venta, Pago, FormaPago
from datetime import datetime
from sqlalchemy import func, and_
from decimal import Decimal

bp = Blueprint('caja', __name__, url_prefix='/caja')

@bp.route('/estado')
@login_required
def estado():
    """
    Muestra el estado actual de la caja del usuario
    """
    # Buscar si hay una caja abierta por el usuario actual
    apertura_actual = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    
    # Obtener todas las cajas disponibles
    cajas = Caja.query.filter_by(activo=True).all()
    
    # Si hay apertura, calcular totales
    total_ventas = Decimal('0')
    total_efectivo = Decimal('0')
    total_tarjeta = Decimal('0')
    total_otros = Decimal('0')
    ventas_list = []
    
    if apertura_actual:
        # Ventas de esta apertura
        ventas_list = Venta.query.filter_by(
            apertura_caja_id=apertura_actual.id,
            estado='completada'
        ).all()
        
        total_ventas = sum(v.total for v in ventas_list)
        
        # Calcular totales por forma de pago
        for venta in ventas_list:
            for pago in venta.pagos:
                if pago.estado == 'confirmado':
                    if pago.forma_pago_id == 1:  # Efectivo
                        total_efectivo += pago.monto
                    elif pago.forma_pago_id in [2, 6]:  # Tarjetas
                        total_tarjeta += pago.monto
                    else:
                        total_otros += pago.monto
    
    return render_template('caja/estado.html',
                         apertura_actual=apertura_actual,
                         cajas=cajas,
                         total_ventas=total_ventas,
                         total_efectivo=total_efectivo,
                         total_tarjeta=total_tarjeta,
                         total_otros=total_otros,
                         ventas_list=ventas_list)

@bp.route('/abrir', methods=['POST'])
@login_required
def abrir():
    """
    Abre una nueva caja
    """
    try:
        # Verificar que no tenga una caja ya abierta
        apertura_existente = AperturaCaja.query.filter_by(
            cajero_id=current_user.id,
            estado='abierto'
        ).first()
        
        if apertura_existente:
            flash('Ya tienes una caja abierta', 'warning')
            return redirect(url_for('caja.estado'))
        
        caja_id = request.form.get('caja_id')
        monto_inicial = request.form.get('monto_inicial', 0)
        observaciones = request.form.get('observaciones', '')
        
        # Crear apertura
        apertura = AperturaCaja(
            caja_id=caja_id,
            cajero_id=current_user.id,
            monto_inicial=monto_inicial,
            observaciones=observaciones,
            estado='abierto'
        )
        
        db.session.add(apertura)
        db.session.commit()
        
        flash(f'Caja abierta exitosamente con Gs. {monto_inicial:,.0f}', 'success')
        return redirect(url_for('caja.estado'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al abrir caja: {str(e)}', 'danger')
        return redirect(url_for('caja.estado'))

@bp.route('/cerrar', methods=['POST'])
@login_required
def cerrar():
    """
    Cierra la caja actual y realiza el arqueo
    """
    try:
        apertura = AperturaCaja.query.filter_by(
            cajero_id=current_user.id,
            estado='abierto'
        ).first()
        
        if not apertura:
            flash('No tienes una caja abierta', 'warning')
            return redirect(url_for('caja.estado'))
        
        # Obtener montos del arqueo del formulario
        monto_efectivo_contado = Decimal(request.form.get('monto_efectivo', '0'))
        monto_tarjeta_contado = Decimal(request.form.get('monto_tarjeta', '0'))
        monto_otros_contado = Decimal(request.form.get('monto_otros', '0'))
        observaciones_cierre = request.form.get('observaciones_cierre', '')
        
        # Calcular el total contado
        monto_final = monto_efectivo_contado + monto_tarjeta_contado + monto_otros_contado
        
        # Calcular el total del sistema
        ventas = Venta.query.filter_by(
            apertura_caja_id=apertura.id,
            estado='completada'
        ).all()
        
        monto_sistema = apertura.monto_inicial
        for venta in ventas:
            for pago in venta.pagos:
                if pago.estado == 'confirmado' and pago.forma_pago_id == 1:  # Solo efectivo
                    monto_sistema += pago.monto
        
        # Calcular diferencia
        diferencia = monto_efectivo_contado - monto_sistema
        
        # Actualizar apertura
        apertura.fecha_cierre = datetime.now()
        apertura.monto_final = monto_final
        apertura.monto_sistema = monto_sistema
        apertura.diferencia = diferencia
        apertura.estado = 'cerrado'
        
        # Agregar observaciones si hay diferencia
        if diferencia != 0:
            obs_dif = f"\n[DIFERENCIA: Gs. {diferencia:,.0f}]"
            apertura.observaciones = (apertura.observaciones or '') + obs_dif
        
        if observaciones_cierre:
            apertura.observaciones = (apertura.observaciones or '') + f"\n{observaciones_cierre}"
        
        db.session.commit()
        
        if diferencia == 0:
            flash('Caja cerrada exitosamente. ¡Arqueo cuadrado!', 'success')
        elif abs(diferencia) <= 1000:
            flash(f'Caja cerrada. Diferencia menor: Gs. {diferencia:,.0f}', 'info')
        else:
            flash(f'Caja cerrada con diferencia: Gs. {diferencia:,.0f}', 'warning')
        
        return redirect(url_for('caja.ver_apertura', id=apertura.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cerrar caja: {str(e)}', 'danger')
        return redirect(url_for('caja.estado'))

@bp.route('/ver/<int:id>')
@login_required
def ver_apertura(id):
    """
    Ver detalles de una apertura de caja específica
    """
    apertura = AperturaCaja.query.get_or_404(id)
    
    # Verificar permisos
    if apertura.cajero_id != current_user.id and current_user.rol != 'admin':
        flash('No tienes permiso para ver esta apertura', 'danger')
        return redirect(url_for('caja.estado'))
    
    # Obtener ventas
    ventas = Venta.query.filter_by(
        apertura_caja_id=apertura.id,
        estado='completada'
    ).order_by(Venta.fecha_venta.desc()).all()
    
    # Calcular totales por forma de pago
    total_efectivo = Decimal('0')
    total_tarjeta = Decimal('0')
    total_otros = Decimal('0')
    
    for venta in ventas:
        for pago in venta.pagos:
            if pago.estado == 'confirmado':
                if pago.forma_pago_id == 1:  # Efectivo
                    total_efectivo += pago.monto
                elif pago.forma_pago_id in [2, 6]:  # Tarjetas
                    total_tarjeta += pago.monto
                else:
                    total_otros += pago.monto
    
    total_ventas = sum(v.total for v in ventas)
    
    return render_template('caja/ver_apertura.html',
                         apertura=apertura,
                         ventas=ventas,
                         total_ventas=total_ventas,
                         total_efectivo=total_efectivo,
                         total_tarjeta=total_tarjeta,
                         total_otros=total_otros)

@bp.route('/historial')
@login_required
def historial():
    """
    Ver historial de aperturas de caja
    """
    page = request.args.get('page', 1, type=int)
    
    # Si es admin, ver todas; si no, solo las propias
    if current_user.rol == 'admin':
        query = AperturaCaja.query
    else:
        query = AperturaCaja.query.filter_by(cajero_id=current_user.id)
    
    aperturas = query.order_by(AperturaCaja.fecha_apertura.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('caja/historial.html', aperturas=aperturas)

@bp.route('/arqueo/<int:id>')
@login_required
def arqueo(id):
    """
    Ver arqueo detallado de una caja cerrada
    """
    apertura = AperturaCaja.query.get_or_404(id)
    
    # Verificar permisos
    if apertura.cajero_id != current_user.id and current_user.rol != 'admin':
        flash('No tienes permiso para ver este arqueo', 'danger')
        return redirect(url_for('caja.historial'))
    
    if apertura.estado != 'cerrado':
        flash('Esta caja aún no ha sido cerrada', 'warning')
        return redirect(url_for('caja.ver_apertura', id=id))
    
    # Obtener detalles de pagos agrupados por forma de pago
    ventas = Venta.query.filter_by(apertura_caja_id=apertura.id).all()
    
    # Diccionario para agrupar por forma de pago
    detalle_pagos = {}
    
    for venta in ventas:
        for pago in venta.pagos:
            if pago.estado == 'confirmado':
                forma_nombre = pago.forma_pago.nombre if pago.forma_pago else 'Desconocido'
                
                if forma_nombre not in detalle_pagos:
                    detalle_pagos[forma_nombre] = {
                        'cantidad': 0,
                        'total': Decimal('0')
                    }
                
                detalle_pagos[forma_nombre]['cantidad'] += 1
                detalle_pagos[forma_nombre]['total'] += pago.monto
    
    return render_template('caja/arqueo.html',
                         apertura=apertura,
                         detalle_pagos=detalle_pagos,
                         ventas=ventas)
