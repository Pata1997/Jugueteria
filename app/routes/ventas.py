from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import (Caja, AperturaCaja, Venta, VentaDetalle, Pago, 
                        NotaCredito, NotaDebito, Cliente, Producto, OrdenServicio)
from datetime import datetime, date
from decimal import Decimal

bp = Blueprint('ventas', __name__, url_prefix='/ventas')

# ===== CAJAS =====
@bp.route('/cajas')
@login_required
def cajas():
    cajas = Caja.query.all()
    return render_template('ventas/cajas.html', cajas=cajas)

@bp.route('/apertura', methods=['GET', 'POST'])
@login_required
def apertura_caja():
    # Verificar si ya hay una caja abierta
    caja_abierta = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    
    if caja_abierta:
        flash('Ya tiene una caja abierta', 'warning')
        return redirect(url_for('ventas.ver_apertura', id=caja_abierta.id))
    
    if request.method == 'POST':
        try:
            apertura = AperturaCaja(
                caja_id=request.form.get('caja_id'),
                cajero_id=current_user.id,
                monto_inicial=request.form.get('monto_inicial'),
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(apertura)
            db.session.commit()
            
            flash('Caja abierta correctamente', 'success')
            return redirect(url_for('ventas.ver_apertura', id=apertura.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    cajas = Caja.query.filter_by(activo=True).all()
    return render_template('ventas/apertura_caja.html', cajas=cajas)

@bp.route('/apertura/<int:id>')
@login_required
def ver_apertura(id):
    apertura = AperturaCaja.query.get_or_404(id)
    ventas = apertura.ventas.all()
    total_ventas = sum(float(v.total or 0) for v in ventas)
    total_pagadas = sum(float(v.total or 0) for v in ventas if v.estado_pago == 'pagado')
    total_pendientes = sum(float(v.total or 0) for v in ventas if v.estado_pago != 'pagado')
    return render_template(
        'ventas/ver_apertura.html',
        apertura=apertura,
        ventas=ventas,
        total_ventas=total_ventas,
        total_pagadas=total_pagadas,
        total_pendientes=total_pendientes
    )

@bp.route('/apertura/<int:id>/cerrar', methods=['GET', 'POST'])
@login_required
def cerrar_caja(id):
    apertura = AperturaCaja.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            apertura.monto_final = Decimal(str(request.form.get('monto_final') or 0))
            apertura.fecha_cierre = datetime.utcnow()
            apertura.estado = 'cerrado'
            apertura.observaciones = request.form.get('observaciones')
            apertura.calcular_cierre()
            
            db.session.commit()
            
            flash('Caja cerrada correctamente', 'success')
            return redirect(url_for('ventas.arqueo_caja', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # Calcular totales para mostrar
    apertura.calcular_cierre()
    return render_template('ventas/cerrar_caja.html', apertura=apertura)

@bp.route('/arqueo/<int:id>')
@login_required
def arqueo_caja(id):
    apertura = AperturaCaja.query.get_or_404(id)
    
    # Totales por forma de pago
    totales_por_forma = {}
    for venta in apertura.ventas:
        for pago in venta.pagos:
            if pago.forma_pago not in totales_por_forma:
                totales_por_forma[pago.forma_pago] = 0
            totales_por_forma[pago.forma_pago] += float(pago.monto)
    
    return render_template('ventas/arqueo_caja.html', 
                         apertura=apertura, 
                         totales_por_forma=totales_por_forma)

# ===== VENTAS =====
@bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    fecha_desde = request.form.get('fecha_desde')
    fecha_hasta = request.form.get('fecha_hasta')
    
    query = Venta.query
    
    if fecha_desde:
        query = query.filter(Venta.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Venta.fecha_venta <= fecha_hasta)
    
    ventas = query.order_by(Venta.fecha_venta.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Totales para el pie de tabla
    total_ventas = sum(float(v.total or 0) for v in ventas.items)
    total_pagado = sum(float(getattr(v, 'monto_pagado', 0) or 0) for v in ventas.items)
    total_saldo = sum(float(getattr(v, 'saldo_pendiente', 0) or 0) for v in ventas.items)
    
    return render_template(
        'ventas/listar.html',
        ventas=ventas,
        total_ventas=total_ventas,
        total_pagado=total_pagado,
        total_saldo=total_saldo
    )

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            # Verificar caja abierta
            apertura = AperturaCaja.query.filter_by(
                cajero_id=current_user.id,
                estado='abierto'
            ).first()
            
            if not apertura:
                flash('Debe abrir una caja antes de realizar ventas', 'warning')
                return redirect(url_for('ventas.apertura_caja'))
            
            # Generar número de factura
            from app.models import ConfiguracionEmpresa
            config = ConfiguracionEmpresa.get_config()
            numero_factura = f"{config.numero_establecimiento}-{config.numero_expedicion}-{config.numero_factura_actual:07d}"
            config.numero_factura_actual += 1
            
            venta = Venta(
                numero_factura=numero_factura,
                tipo_venta=request.form.get('tipo_venta'),
                cliente_id=request.form.get('cliente_id'),
                orden_servicio_id=request.form.get('orden_servicio_id'),
                apertura_caja_id=apertura.id,
                vendedor_id=current_user.id,
                subtotal=request.form.get('subtotal'),
                descuento=request.form.get('descuento', 0),
                iva=request.form.get('iva'),
                total=request.form.get('total'),
                dias_credito=request.form.get('dias_credito', 0),
                observaciones=request.form.get('observaciones')
            )
            
            # Calcular fecha de vencimiento si es a crédito
            if venta.dias_credito > 0:
                from datetime import timedelta
                venta.fecha_vencimiento = date.today() + timedelta(days=venta.dias_credito)
                venta.estado_pago = 'pendiente'
            
            # Agregar detalles
            import json
            detalles_json = request.form.get('detalles_json')
            detalles = json.loads(detalles_json)
            
            for det in detalles:
                detalle = VentaDetalle(
                    venta=venta,
                    tipo_item=det['tipo_item'],
                    producto_id=det.get('producto_id'),
                    descripcion=det['descripcion'],
                    cantidad=det['cantidad'],
                    precio_unitario=det['precio_unitario'],
                    subtotal=det['subtotal'],
                    descuento=det.get('descuento', 0),
                    total=det['total']
                )
                db.session.add(detalle)
                
                # Descontar stock si es producto
                if det.get('producto_id') and det['tipo_item'] == 'producto':
                    producto = Producto.query.get(det['producto_id'])
                    cantidad = float(det['cantidad'])
                    
                    from app.models import MovimientoProducto
                    producto.stock_actual -= cantidad
                    
                    movimiento = MovimientoProducto(
                        producto_id=producto.id,
                        tipo_movimiento='salida',
                        cantidad=cantidad,
                        stock_anterior=producto.stock_actual + cantidad,
                        stock_actual=producto.stock_actual,
                        motivo='venta',
                        referencia_tipo='venta',
                        referencia_id=venta.id,
                        costo_unitario=producto.precio_compra,
                        usuario_id=current_user.id
                    )
                    db.session.add(movimiento)
            
            # Agregar pagos
            pagos_json = request.form.get('pagos_json')
            pagos = json.loads(pagos_json)
            
            for pag in pagos:
                pago = Pago(
                    venta=venta,
                    forma_pago=pag['forma_pago'],
                    monto=pag['monto'],
                    referencia=pag.get('referencia'),
                    banco=pag.get('banco')
                )
                db.session.add(pago)
            
            venta.actualizar_estado_pago()
            
            db.session.add(venta)
            db.session.commit()
            
            flash('Venta registrada correctamente', 'success')
            return redirect(url_for('ventas.ver', id=venta.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # Verificar caja abierta
    apertura = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    
    if not apertura:
        flash('Debe abrir una caja antes de realizar ventas', 'warning')
        return redirect(url_for('ventas.apertura_caja'))
    
    return render_template('ventas/crear.html')

@bp.route('/<int:id>')
@login_required
def ver(id):
    venta = Venta.query.get_or_404(id)
    
    # Parsear desglose de IVA si existe
    desglose_iva = None
    if venta.observaciones and '[DESGLOSE_IVA]' in venta.observaciones:
        try:
            import json
            partes = venta.observaciones.split('[DESGLOSE_IVA]')
            if len(partes) > 1:
                json_str = partes[1].strip()
                desglose_iva = json.loads(json_str)
        except:
            pass
    
    return render_template('ventas/ver.html', venta=venta, desglose_iva=desglose_iva)

@bp.route('/<int:id>/ticket')
@login_required
def descargar_ticket(id):
    """Genera y descarga el ticket de la venta en PDF (ReportLab)."""
    venta = Venta.query.get_or_404(id)
    
    from app.models import ConfiguracionEmpresa
    from app.utils.ticket import GeneradorTicket
    from flask import send_file
    import io
    import sys
    
    try:
        config = ConfiguracionEmpresa.get_config()
        print(f"[ticket] ===== INICIANDO DESCARGAR TICKET venta_id={venta.id} ====", file=sys.stderr, flush=True)
        generador = GeneradorTicket(config, venta, venta.detalles.all())
        pdf_bytes = generador.generar_ticket_pdf()
        
        print(f"[ticket] PDF con {len(pdf_bytes)} bytes, sirviendo...", file=sys.stderr, flush=True)

        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        print(f"[ticket] Retornando send_file con {len(pdf_bytes)} bytes", file=sys.stderr, flush=True)
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ticket_{venta.numero_factura}.pdf'
        )
    except Exception as e:
        print(f"[ticket] !!!!! ERROR en descargar_ticket: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        flash(f'Error al generar ticket: {str(e)}', 'danger')
        return redirect(url_for('ventas.ver', id=id))

@bp.route('/<int:id>/facturar', methods=['GET', 'POST'])
@login_required
def facturar(id):
    """Cobrar una venta pendiente (TMP) y generar factura real."""
    venta = Venta.query.get_or_404(id)
    
    # Solo permitir facturar ventas pendientes con estado_pago != pagado
    if venta.estado == 'completada' or venta.estado_pago == 'pagado':
        flash('Esta venta ya está facturada/pagada', 'warning')
        return redirect(url_for('ventas.ver', id=id))
    
    # Verificar apertura de caja SIEMPRE (GET y POST)
    apertura = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    
    if not apertura:
        flash('Debes abrir una caja antes de facturar', 'danger')
        return redirect(url_for('caja.estado'))
    
    if request.method == 'POST':
        try:
            # Generar número de factura real
            from app.models import ConfiguracionEmpresa
            config = ConfiguracionEmpresa.get_config()
            numero_factura = config.generar_numero_factura()
            
            # Actualizar venta
            venta.numero_factura = numero_factura
            venta.apertura_caja_id = apertura.id
            venta.estado = 'completada'
            
            # Registrar pagos (al contado, múltiples formas de pago)
            import json
            pagos_json = request.form.get('pagos_json', '[]')
            pagos_list = json.loads(pagos_json)
            
            # Validar que haya pagos
            if not pagos_list:
                flash('Debe registrar al menos una forma de pago', 'warning')
                return redirect(url_for('ventas.facturar', id=id))
            
            total_pagado = 0
            for pag in pagos_list:
                pago = Pago(
                    venta_id=venta.id,
                    forma_pago_id=pag.get('forma_pago_id'),
                    monto=pag['monto'],
                    referencia=pag.get('referencia'),
                    banco=pag.get('banco'),
                    estado='confirmado'
                )
                db.session.add(pago)
                total_pagado += float(pag['monto'])
            
            # Calcular vuelto
            vuelto = max(0, total_pagado - float(venta.total))
            
            # Actualizar estado de pago
            venta.actualizar_estado_pago()
            
            db.session.commit()
            
            # Retornar con información del vuelto
            flash(f'Venta facturada correctamente. Factura: {numero_factura}', 'success')
            
            # Guardar vuelto en sesión para mostrar en modal
            from flask import session
            session['vuelto'] = float(vuelto)
            session['venta_id'] = venta.id
            session['numero_factura'] = numero_factura
            session['apertura_caja_id'] = apertura.id
            
            return redirect(url_for('ventas.confirmar_vuelto'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # Cargar formas de pago activas sin duplicados
    from app.models.venta import FormaPago
    formas_pago = FormaPago.activas_unicas()
    
    # Calcular efectivo disponible en la caja abierta actual
    efectivo_disponible = 0
    apertura = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    if apertura:
        efectivo_disponible = float(apertura.monto_inicial or 0)
        # Sumar efectivo de todas las ventas de esta apertura (solo pagos confirmados)
        for v in apertura.ventas:
            for p in v.pagos:
                if p.estado == 'confirmado' and p.forma_pago_id == 1:  # ID 1 = Efectivo (Efectivo es la forma_pago con id=1)
                    efectivo_disponible += float(p.monto)
    
    # Parsear desglose de IVA si existe
    desglose_iva = None
    if venta.observaciones and '[DESGLOSE_IVA]' in venta.observaciones:
        try:
            import json
            partes = venta.observaciones.split('[DESGLOSE_IVA]')
            if len(partes) > 1:
                json_str = partes[1].strip()
                desglose_iva = json.loads(json_str)
        except:
            pass
    
    return render_template('ventas/facturar.html', 
                         venta=venta, 
                         desglose_iva=desglose_iva,
                         formas_pago=formas_pago,
                         efectivo_disponible=efectivo_disponible)

@bp.route('/confirmar-vuelto')
@login_required
def confirmar_vuelto():
    """Mostrar modal de confirmación de vuelto y descargar ticket"""
    from flask import session
    
    vuelto = session.pop('vuelto', 0)
    venta_id = session.pop('venta_id', None)
    numero_factura = session.pop('numero_factura', None)
    apertura_caja_id = session.pop('apertura_caja_id', None)
    
    if not venta_id:
        flash('No hay información de venta para procesar', 'warning')
        return redirect(url_for('ventas.listar'))
    
    return render_template('ventas/confirmar_vuelto.html',
                         vuelto=vuelto,
                         venta_id=venta_id,
                         numero_factura=numero_factura,
                         apertura_caja_id=apertura_caja_id)

@bp.route('/<int:id>/anular', methods=['POST'])
@login_required
def anular(id):
    venta = Venta.query.get_or_404(id)
    
    try:
        venta.estado = 'anulada'
        
        # Revertir movimientos de stock
        for detalle in venta.detalles:
            if detalle.producto_id and detalle.tipo_item == 'producto':
                producto = Producto.query.get(detalle.producto_id)
                cantidad = float(detalle.cantidad)
                
                from app.models import MovimientoProducto
                producto.stock_actual += cantidad
                
                movimiento = MovimientoProducto(
                    producto_id=producto.id,
                    tipo_movimiento='entrada',
                    cantidad=cantidad,
                    stock_anterior=producto.stock_actual - cantidad,
                    stock_actual=producto.stock_actual,
                    motivo='devolucion',
                    referencia_tipo='venta',
                    referencia_id=venta.id,
                    usuario_id=current_user.id,
                    observaciones='Anulación de venta'
                )
                db.session.add(movimiento)
        
        db.session.commit()
        flash('Venta anulada correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('ventas.ver', id=id))

# ===== NOTAS DE CRÉDITO =====
@bp.route('/notas-credito/crear/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def crear_nota_credito(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    
    if request.method == 'POST':
        try:
            ultimo = NotaCredito.query.order_by(NotaCredito.id.desc()).first()
            numero = f"NC-{(ultimo.id + 1 if ultimo else 1):07d}"
            
            nota = NotaCredito(
                numero_nota=numero,
                venta_id=venta.id,
                motivo=request.form.get('motivo'),
                monto=request.form.get('monto'),
                usuario_id=current_user.id,
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(nota)
            db.session.commit()
            
            flash('Nota de crédito creada correctamente', 'success')
            return redirect(url_for('ventas.ver', id=venta.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('ventas/crear_nota_credito.html', venta=venta)

# ===== NOTAS DE DÉBITO =====
@bp.route('/notas-debito/crear/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def crear_nota_debito(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    
    if request.method == 'POST':
        try:
            ultimo = NotaDebito.query.order_by(NotaDebito.id.desc()).first()
            numero = f"ND-{(ultimo.id + 1 if ultimo else 1):07d}"
            
            nota = NotaDebito(
                numero_nota=numero,
                venta_id=venta.id,
                motivo=request.form.get('motivo'),
                monto=request.form.get('monto'),
                usuario_id=current_user.id,
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(nota)
            db.session.commit()
            
            flash('Nota de débito creada correctamente', 'success')
            return redirect(url_for('ventas.ver', id=venta.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('ventas/crear_nota_debito.html', venta=venta)

# ===== CUENTAS POR COBRAR =====
@bp.route('/cuentas-por-cobrar')
@login_required
def cuentas_por_cobrar():
    page = request.args.get('page', 1, type=int)
    
    ventas = Venta.query.filter(
        Venta.estado_pago.in_(['pendiente', 'parcial'])
    ).order_by(Venta.fecha_vencimiento).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('ventas/cuentas_por_cobrar.html', ventas=ventas)

@bp.route('/registrar-pago', methods=['POST'])
@login_required
def registrar_pago():
    venta_id = request.form.get('venta_id')
    venta = Venta.query.get_or_404(venta_id)
    
    try:
        pago = Pago(
            venta_id=venta.id,
            forma_pago=request.form.get('forma_pago'),
            monto=request.form.get('monto'),
            referencia=request.form.get('referencia'),
            banco=request.form.get('banco'),
            observaciones=request.form.get('observaciones')
        )
        
        db.session.add(pago)
        venta.actualizar_estado_pago()
        db.session.commit()
        
        flash('Pago registrado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('ventas.ver', id=venta_id))
