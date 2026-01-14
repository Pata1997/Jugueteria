"""
Rutas para la gestión de caja
Incluye: apertura, cierre, arqueo y consulta de estado
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.utils.roles import require_roles
from app import db
from app.models import Caja, AperturaCaja, Venta, Pago, FormaPago
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, and_
from decimal import Decimal
from app.utils.reports import generar_reporte_arqueo
from app.models import ConfiguracionEmpresa
from app.utils import registrar_bitacora

bp = Blueprint('caja', __name__, url_prefix='/caja')

def calcular_totales_por_forma_pago(apertura_id):
    """
    Calcula los totales esperados por forma de pago para una apertura de caja
    """
    ventas = Venta.query.filter_by(
        apertura_caja_id=apertura_id,
        estado='completada'
    ).all()
    
    totales = {
        'efectivo': Decimal('0'),
        'tarjeta': Decimal('0'),
        'transferencia': Decimal('0'),
        'cheque': Decimal('0')
    }
    
    # Agrupar pagos confirmados por forma de pago
    for venta in ventas:
        total_venta = Decimal(venta.total)
        pagado = Decimal('0')
        for pago in venta.pagos:
            if pago.estado == 'confirmado':
                forma_nombre = pago.forma_pago.nombre.lower() if pago.forma_pago else 'otros'
                monto_pago = Decimal(pago.monto)
                if 'efectivo' in forma_nombre:
                    # Solo sumar el neto de efectivo que queda en caja (no el vuelto)
                    neto_efectivo = min(monto_pago, total_venta - pagado)
                    totales['efectivo'] += neto_efectivo
                    pagado += neto_efectivo
                elif 'tarjeta' in forma_nombre or 'débito' in forma_nombre or 'crédito' in forma_nombre:
                    totales['tarjeta'] += monto_pago
                    pagado += monto_pago
                elif 'transferencia' in forma_nombre:
                    totales['transferencia'] += monto_pago
                    pagado += monto_pago
                elif 'cheque' in forma_nombre:
                    totales['cheque'] += monto_pago
                    pagado += monto_pago
    
    totales['total'] = totales['efectivo'] + totales['tarjeta'] + totales['transferencia'] + totales['cheque']
    
    return totales

@bp.route('/estado')
@login_required
def estado():
    """
    Muestra el estado actual de la caja del usuario
    """
    from app.models import MovimientoCaja, PagoCompra
    
    # Buscar si hay una caja abierta por el usuario actual
    apertura_actual = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    
    # Obtener todas las cajas disponibles
    cajas = Caja.query.filter_by(activo=True).all()
    
    # Si hay apertura, calcular totales por forma de pago
    total_ventas = Decimal('0')
    total_efectivo = Decimal('0')
    total_tarjeta = Decimal('0')
    total_transferencias = Decimal('0')
    total_cheques = Decimal('0')
    total_otros = Decimal('0')
    ventas_list = []
    pagos_compras = []
    total_egresos = Decimal('0')
    monto_esperado = Decimal('0')
    
    if apertura_actual:
        # Ventas de esta apertura
        ventas_list = Venta.query.filter_by(
            apertura_caja_id=apertura_actual.id,
            estado='completada'
        ).all()
        total_ventas = sum(v.total for v in ventas_list)
        # Usar la función helper para calcular totales por forma de pago
        totales = calcular_totales_por_forma_pago(apertura_actual.id)
        # Calcular egresos (compras pagadas desde caja chica)
        egresos = MovimientoCaja.query.filter_by(
            apertura_caja_id=apertura_actual.id,
            tipo='egreso'
        ).all()
        total_egresos = sum(m.monto for m in egresos)
        # Sumar el monto inicial al total efectivo y descontar egresos
        total_efectivo = apertura_actual.monto_inicial + totales['efectivo'] - total_egresos
        total_tarjeta = totales['tarjeta']
        total_transferencias = totales['transferencia']
        total_cheques = totales['cheque']
        total_otros = total_transferencias + total_cheques
        # Obtener pagos de compras de esta apertura
        pagos_compras = PagoCompra.query.filter_by(
            apertura_caja_id=apertura_actual.id,
            origen_pago='caja_chica'
        ).order_by(PagoCompra.fecha_pago.desc()).all()
        # El monto esperado es igual al efectivo disponible
        monto_esperado = total_efectivo
    
    return render_template('caja/estado.html',
                         apertura_actual=apertura_actual,
                         cajas=cajas,
                         total_ventas=total_ventas,
                         total_efectivo=total_efectivo,
                         total_tarjeta=total_tarjeta,
                         total_transferencias=total_transferencias,
                         total_cheques=total_cheques,
                         total_otros=total_otros,
                         ventas_list=ventas_list,
                         pagos_compras=pagos_compras,
                         total_egresos=total_egresos,
                         monto_esperado=monto_esperado)

@bp.route('/abrir', methods=['POST'])
@login_required
def abrir():
    """
    Abre una nueva caja
    """
    try:
        apertura_existente = AperturaCaja.query.filter_by(
            cajero_id=current_user.id,
            estado='abierto'
        ).first()
        
        if apertura_existente:
            flash('Ya tienes una caja abierta', 'warning')
            return redirect(url_for('caja.estado'))
        
        caja_id = request.form.get('caja_id')
        monto_inicial = Decimal(str(request.form.get('monto_inicial', 0)))
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
        
        registrar_bitacora('abrir-caja', f'Apertura de caja: {caja_id} por usuario {current_user.username}')
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
    Procesa el arqueo desde el modal y cierra la caja completamente
    Genera PDF del reporte de arqueo y lo descarga
    """
    try:
        apertura = AperturaCaja.query.filter_by(
            cajero_id=current_user.id,
            estado='abierto'
        ).first()
        
        if not apertura:
            flash('No tienes una caja abierta', 'warning')
            return redirect(url_for('caja.estado'))
        
        # Función auxiliar para limpiar y convertir valores
        def limpiar_monto(valor):
            if not valor:
                return 0
            # Eliminar puntos y comas, convertir a int
            limpio = str(valor).replace('.', '').replace(',', '')
            try:
                return int(limpio)
            except:
                return 0
        
        # Obtener los valores del formulario del modal
        monto_efectivo_real = limpiar_monto(request.form.get('monto_efectivo', 0))
        monto_tarjeta_real = limpiar_monto(request.form.get('monto_tarjeta', 0))
        monto_transferencias_real = limpiar_monto(request.form.get('monto_transferencias', 0))
        monto_cheques_real = limpiar_monto(request.form.get('monto_cheques', 0))
        observaciones_cierre = request.form.get('observaciones_cierre', '')
        
        # Calcular totales esperados por forma de pago
        totales = calcular_totales_por_forma_pago(apertura.id)
        
        # Calcular egresos (compras pagadas desde caja chica)
        from app.models import MovimientoCaja
        egresos = MovimientoCaja.query.filter_by(
            apertura_caja_id=apertura.id,
            tipo='egreso'
        ).all()
        total_egresos = sum(m.monto for m in egresos)
        # Calcular efectivo esperado en caja (monto inicial + ventas efectivo - egresos)
        efectivo_esperado = apertura.monto_inicial + totales['efectivo'] - total_egresos
        # Guardar valores en la apertura
        apertura.monto_efectivo_real = monto_efectivo_real
        apertura.monto_tarjeta_real = monto_tarjeta_real
        apertura.monto_transferencias_real = monto_transferencias_real
        apertura.monto_cheques_real = monto_cheques_real
        apertura.monto_efectivo_esperado = efectivo_esperado
        apertura.monto_tarjeta_esperado = totales['tarjeta']
        apertura.monto_transferencias_esperado = totales['transferencia']
        apertura.monto_cheques_esperado = totales['cheque']
        # Calcular totales reales y esperados
        total_real = monto_efectivo_real + monto_tarjeta_real + monto_transferencias_real + monto_cheques_real
        total_esperado = efectivo_esperado + totales['tarjeta'] + totales['transferencia'] + totales['cheque']
        diferencia_total = total_real - total_esperado
        # Guardar el monto_sistema correctamente (para arqueo y reportes)
        apertura.monto_sistema = efectivo_esperado + totales['tarjeta'] + totales['transferencia'] + totales['cheque']
        
        apertura.observaciones_cierre = observaciones_cierre
        apertura.diferencia_total = diferencia_total
        apertura.estado = 'cerrada'
        apertura.fecha_cierre = datetime.now()
        
        db.session.commit()
        
        # ===== GENERAR PDF =====
        try:
            # Obtener configuración de la empresa
            empresa = ConfiguracionEmpresa.query.first()
            empresa_config = {
                'nombre': empresa.nombre_empresa if empresa else 'JUGUETERÍA',
                'subtitulo': 'El Mundo Feliz',
                'ruc': empresa.ruc if empresa else 'N/A',
                'direccion': empresa.direccion if empresa else ''
            }
            
            # Generar PDF
            # Los totales esperados deben incluir el monto_inicial en efectivo
            totales_con_inicial = totales.copy()
            totales_con_inicial['efectivo'] = apertura.monto_inicial + totales['efectivo']
            totales_con_inicial['total'] = apertura.monto_inicial + totales['total']
            
            pdf_buffer = generar_reporte_arqueo(apertura, totales_con_inicial, empresa_config)
            
            # Nombre del archivo
            fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Arqueo_Caja_{apertura.caja.nombre}_{fecha_str}.pdf"
            
            # Mensaje de éxito
            if abs(diferencia_total) < 1:
                flash(f'✓ Caja cerrada correctamente. Arqueo cuadrado.', 'success')
            elif diferencia_total > 0:
                flash(f'⚠ Caja cerrada con sobrante: Gs. {diferencia_total:,.0f}', 'warning')
            else:
                flash(f'⚠ Caja cerrada con faltante: Gs. {abs(diferencia_total):,.0f}', 'warning')
            
            # Descargar PDF
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        except Exception as pdf_error:
            # Si hay error en el PDF, redirigir igual pero con advertencia
            flash(f'⚠ Caja cerrada pero error al generar PDF: {str(pdf_error)}', 'warning')
            return redirect(url_for('caja.estado'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cerrar caja: {str(e)}', 'danger')
        return redirect(url_for('caja.estado'))

@bp.route('/realizar-arqueo/<int:id>', methods=['GET', 'POST'])
@login_required
def realizar_arqueo(id):
    """
    Formulario para realizar arqueo detallado de caja
    GET: muestra el formulario con los totales esperados
    POST: guarda los totales reales contados y cierra la caja
    """
    apertura = AperturaCaja.query.get_or_404(id)
    
    # Verificar permisos
    if apertura.cajero_id != current_user.id and current_user.rol != 'admin':
        flash('No tienes permiso para arquear esta caja', 'danger')
        return redirect(url_for('caja.estado'))
    
    if apertura.estado != 'en_arqueo':
        flash('Esta caja no está en proceso de arqueo', 'warning')
        return redirect(url_for('caja.ver_apertura', id=id))
    
    if request.method == 'GET':
        # Calcular totales esperados por forma de pago
        totales_sistema = calcular_totales_por_forma_pago(apertura.id)
        
        return render_template('caja/realizar_arqueo.html',
                             apertura=apertura,
                             totales_sistema=totales_sistema)
    
    else:  # POST
        try:
            # Recalcular totales esperados para guardarlos
            totales_sistema = calcular_totales_por_forma_pago(apertura.id)
            
            # Obtener valores contados del formulario
            monto_efectivo_real = Decimal(request.form.get('monto_efectivo_real', '0'))
            monto_tarjeta_real = Decimal(request.form.get('monto_tarjeta_real', '0'))
            monto_transferencias_real = Decimal(request.form.get('monto_transferencias_real', '0'))
            monto_cheques_real = Decimal(request.form.get('monto_cheques_real', '0'))
            observaciones = request.form.get('observaciones', '')
            
            # Guardar valores reales
            apertura.monto_efectivo_real = monto_efectivo_real
            apertura.monto_tarjeta_real = monto_tarjeta_real
            apertura.monto_transferencias_real = monto_transferencias_real
            apertura.monto_cheques_real = monto_cheques_real
            
            # Guardar valores esperados
            apertura.monto_efectivo_esperado = totales_sistema['efectivo']
            apertura.monto_tarjeta_esperado = totales_sistema['tarjeta']
            apertura.monto_transferencias_esperado = totales_sistema['transferencia']
            apertura.monto_cheques_esperado = totales_sistema['cheque']
            
            # Calcular total real
            total_real = monto_efectivo_real + monto_tarjeta_real + monto_transferencias_real + monto_cheques_real
            apertura.monto_final = total_real
            
            # Cerrar la caja
            apertura.fecha_cierre = datetime.now()
            apertura.estado = 'cerrada'
            
            if observaciones:
                apertura.observaciones = (apertura.observaciones or '') + f"\n{observaciones}"
            
            db.session.commit()
            
            registrar_bitacora('cerrar-caja', f'Cierre de caja: {apertura.caja_id} por usuario {current_user.username}')
            
            # Calcular diferencia total
            diferencia_total = total_real - (apertura.monto_sistema or Decimal('0'))
            
            if diferencia_total == 0:
                flash('Caja cerrada exitosamente. ¡Arqueo cuadrado!', 'success')
            elif abs(diferencia_total) <= 1000:
                flash(f'Caja cerrada. Diferencia menor: Gs. {diferencia_total:,.0f}', 'info')
            else:
                flash(f'Caja cerrada con diferencia: Gs. {diferencia_total:,.0f}', 'warning')
            
            return redirect(url_for('caja.ver_apertura', id=apertura.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar arqueo: {str(e)}', 'danger')
            return redirect(url_for('caja.realizar_arqueo', id=id))

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
    
    # Calcular total de caja (todos los pagos confirmados)
    total_caja = Decimal('0')
    
    for venta in ventas:
        for pago in venta.pagos:
            if pago.estado == 'confirmado':
                total_caja += pago.monto
    
    total_ventas = sum(v.total for v in ventas)
    
    return render_template('caja/ver_apertura.html',
                         apertura=apertura,
                         ventas=ventas,
                         total_ventas=total_ventas,
                         total_caja=total_caja)

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
    # Permitir acceso a admin o al cajero dueño
    if apertura.cajero_id != current_user.id and current_user.rol != 'admin':
        flash('No tienes permiso para ver este arqueo', 'danger')
        return redirect(url_for('caja.historial'))
    if apertura.estado != 'cerrada':
        flash('Esta caja aún no ha sido cerrada', 'warning')
        return redirect(url_for('caja.ver_apertura', id=id))

    # Si se solicita PDF profesional
    if request.args.get('pdf') == '1':
        # Generar PDF profesional usando el generador existente
        from app.utils.reports import generar_reporte_arqueo
        empresa = ConfiguracionEmpresa.query.first()
        empresa_config = {
            'nombre': empresa.nombre_empresa if empresa else 'JUGUETERÍA',
            'subtitulo': 'El Mundo Feliz',
            'ruc': empresa.ruc if empresa else 'N/A',
            'direccion': empresa.direccion if empresa else ''
        }
        # Calcular totales esperados
        from app.routes.caja import calcular_totales_por_forma_pago
        totales = calcular_totales_por_forma_pago(apertura.id)
        totales_con_inicial = totales.copy()
        totales_con_inicial['efectivo'] = apertura.monto_inicial + totales['efectivo']
        totales_con_inicial['total'] = apertura.monto_inicial + totales['total']
        pdf_buffer = generar_reporte_arqueo(apertura, totales_con_inicial, empresa_config)
        fecha_str = apertura.fecha_cierre.strftime('%Y%m%d_%H%M') if apertura.fecha_cierre else ''
        filename = f"Arqueo_Caja_{apertura.caja.nombre}_{fecha_str}.pdf"
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    # Renderizado HTML normal
    ventas = Venta.query.filter_by(apertura_caja_id=apertura.id).all()
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
                         ventas=ventas,
                         total_efectivo=apertura.monto_efectivo_esperado or 0)
