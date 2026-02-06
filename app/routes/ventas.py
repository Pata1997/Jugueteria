
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.utils.roles import require_roles
from app import db
from app.models import (Caja, AperturaCaja, Venta, VentaDetalle, Pago, 
                        NotaCredito, NotaDebito, Cliente, Producto, OrdenServicio)
from datetime import datetime, date
from decimal import Decimal
from app.utils import registrar_bitacora
from app.routes.notas_credito_pdf import descargar_nota_credito_pdf as descargar_nota_credito_pdf_func

bp = Blueprint('ventas', __name__, url_prefix='/ventas')

# Registrar la ruta en este blueprint para que url_for('ventas.descargar_nota_credito_pdf') funcione
bp.add_url_rule(
    '/notas-credito/pdf/<int:nota_id>',
    view_func=descargar_nota_credito_pdf_func,
    endpoint='descargar_nota_credito_pdf',
    methods=['GET']
)


# ===== EMITIR NOTA DE CRÉDITO (FLUJO COMPLETO) =====
@bp.route('/notas-credito/emitir/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def emitir_nota_credito(venta_id):
    from app.models import Venta, NotaCredito, NotaCreditoDetalle, ConfiguracionEmpresa
    import datetime, json
    venta = Venta.query.get_or_404(venta_id)
    cliente = venta.cliente
    emisor = ConfiguracionEmpresa.get_config().nombre_empresa
    fecha_emision = datetime.date.today().strftime('%d/%m/%Y')
    factura_original = f"{venta.numero_factura} - {venta.fecha_venta.strftime('%d/%m/%Y')}"
    # Validar si ya existe una Nota de Crédito para esta venta
    nota_existente = NotaCredito.query.filter_by(venta_id=venta.id).first()
    if nota_existente:
        flash('Ya existe una Nota de Crédito para esta factura. No se puede emitir otra.', 'warning')
        return redirect(url_for('ventas.ver', id=venta.id))
    # Calcular el número de Nota de Crédito que se mostraría
    ultimo = NotaCredito.query.order_by(NotaCredito.id.desc()).first()
    numero_nc = f"NC-{'%07d' % (ultimo.id + 1 if ultimo else 1)}"
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo')
            observaciones = request.form.get('observaciones')
            # Tomar los detalles seleccionados desde el JSON oculto generado por JS
            detalle_json = request.form.get('detalleNcJson')
            detalles = []
            if detalle_json:
                import json
                detalles = json.loads(detalle_json)
            monto = sum(float(d['cantidad']) * float(d['precio_unitario']) for d in detalles)
            # Crear la nota de crédito
            nota = NotaCredito(
                numero_nota=numero_nc,
                venta_id=venta.id,
                motivo=motivo,
                monto=monto,
                usuario_id=current_user.id,
                observaciones=observaciones
            )
            db.session.add(nota)
            db.session.flush()  # Para obtener el id
            # Guardar solo los detalles seleccionados
            for d in detalles:
                if float(d['cantidad']) > 0:
                    subtotal = float(d['cantidad']) * float(d['precio_unitario'])
                    detalle = NotaCreditoDetalle(
                        nota_credito_id=nota.id,
                        venta_detalle_id=int(d['id_detalle']),
                        cantidad=d['cantidad'],
                        precio_unitario=d['precio_unitario'],
                        subtotal=subtotal
                    )
                    db.session.add(detalle)
            db.session.commit()
            flash('Nota de Crédito emitida correctamente', 'success')
            # Página intermedia: descarga PDF y redirige a la venta
            return render_template('ventas/descargar_y_redirigir.html',
                                   pdf_url=url_for('ventas.descargar_nota_credito_pdf', nota_id=nota.id),
                                   venta_url=url_for('ventas.ver', id=venta.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al emitir Nota de Crédito: {str(e)}', 'danger')
    return render_template('ventas/emitir_nota_credito.html', venta=venta, cliente=cliente, emisor=emisor, fecha_emision=fecha_emision, factura_original=factura_original, numero_nc=numero_nc)

# ===== CAJAS =====
@bp.route('/cajas')
@login_required
@require_roles('admin', 'caja')
def cajas():
    cajas = Caja.query.all()
    return render_template('ventas/cajas.html', cajas=cajas)

@bp.route('/apertura', methods=['GET', 'POST'])
@login_required
@require_roles('admin', 'caja')
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
            registrar_bitacora('apertura-caja', f'Apertura de caja: {apertura.caja_id} por usuario {current_user.username}')
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
    total_ventas = sum(Decimal(v.total or 0) for v in ventas)
    total_pagadas = sum(Decimal(v.total or 0) for v in ventas if v.estado_pago == 'pagado')
    total_pendientes = sum(Decimal(v.total or 0) for v in ventas if v.estado_pago != 'pagado')
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
            print("[CERRAR CAJA] POST data:", dict(request.form))
            apertura.monto_final = Decimal(str(request.form.get('monto_final') or 0))
            apertura.monto_efectivo_real = Decimal(str(request.form.get('monto_final') or 0))
            apertura.monto_tarjeta_real = Decimal(str(request.form.get('monto_tarjeta_real') or 0))
            apertura.monto_transferencias_real = Decimal(str(request.form.get('monto_transferencias_real') or 0))
            apertura.monto_cheques_real = Decimal(str(request.form.get('monto_cheques_real') or 0))
            apertura.fecha_cierre = datetime.utcnow()
            apertura.estado = 'cerrado'
            apertura.observaciones = request.form.get('observaciones')
            print(f"[CERRAR CAJA] Valores guardados: monto_final={apertura.monto_final}, efectivo_real={apertura.monto_efectivo_real}, tarjeta_real={apertura.monto_tarjeta_real}, transferencias_real={apertura.monto_transferencias_real}, cheques_real={apertura.monto_cheques_real}, observaciones={apertura.observaciones}")
            apertura.calcular_cierre()
            print(f"[CERRAR CAJA] monto_sistema={apertura.monto_sistema}, diferencia={apertura.diferencia}")
            db.session.commit()
            print(f"[CERRAR CAJA] Commit exitoso para apertura {apertura.id}")
            registrar_bitacora('cierre-caja', f'Cierre de caja: {apertura.caja_id} por usuario {current_user.username}')
            flash('Caja cerrada correctamente', 'success')
            # Página intermedia: descarga PDF de arqueo y redirige
            arqueo_url = url_for('ventas.arqueo_caja', id=id)
            pdf_url = url_for('reportes.ventas_diarias_pdf') + f'?desde={apertura.fecha_apertura.strftime("%Y-%m-%d")}'
            return render_template('ventas/descargar_arqueo_y_redirigir.html', pdf_url=pdf_url, arqueo_url=arqueo_url, error=None)
        except Exception as e:
            db.session.rollback()
            print(f"[CERRAR CAJA] ERROR: {e}")
            import traceback
            traceback.print_exc()
            # Mostrar el error en la página intermedia
            arqueo_url = url_for('ventas.arqueo_caja', id=id)
            pdf_url = None
            return render_template('ventas/descargar_arqueo_y_redirigir.html', pdf_url=pdf_url, arqueo_url=arqueo_url, error=str(e))
    # Si la caja ya está cerrada, redirigir directo al arqueo
    if apertura.estado == 'cerrado':
        return redirect(url_for('ventas.arqueo_caja', id=id))
    # Si es GET, mostrar el formulario de cierre
    return render_template('ventas/cerrar_caja.html', apertura=apertura)

@bp.route('/arqueo/<int:id>')
@login_required
def arqueo_caja(id):
    apertura = AperturaCaja.query.get_or_404(id)
    from app.utils.reports import calcular_totales_esperados_apertura
    totales_esperados = calcular_totales_esperados_apertura(apertura)
    return render_template('ventas/arqueo_caja.html', 
                         apertura=apertura, 
                         totales_esperados=totales_esperados)

# ===== VENTAS =====
@bp.route('/')
@login_required
@require_roles('admin', 'caja', 'vendedor')
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
    total_ventas = sum(Decimal(v.total or 0) for v in ventas.items)
    total_pagado = sum(Decimal(getattr(v, 'monto_pagado', 0) or 0) for v in ventas.items)
    total_saldo = sum(Decimal(getattr(v, 'saldo_pendiente', 0) or 0) for v in ventas.items)
    
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
            registrar_bitacora('crear-venta', f'Venta creada: {venta.numero_factura} para cliente {venta.cliente_id}')
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
            from app.models.venta import FormaPago
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
            
            total_pagado = Decimal(0)
            total_efectivo_entregado = Decimal(0)
            efectivo_forma_ids = [fp.id for fp in FormaPago.query.filter(FormaPago.nombre.ilike('%efectivo%')).all()]
            print(f"[DEBUG] efectivo_forma_ids: {efectivo_forma_ids}")
            print(f"[DEBUG] pagos_list: {pagos_list}")
            for pag in pagos_list:
                monto_pago = Decimal(str(pag['monto']))
                forma_pago_id = int(pag.get('forma_pago_id')) if pag.get('forma_pago_id') is not None else None
                print(f"[DEBUG] Procesando pago: {pag}, monto_pago: {monto_pago}, forma_pago_id: {forma_pago_id}")
                if forma_pago_id in efectivo_forma_ids:
                    total_efectivo_entregado += monto_pago
                    # Registrar el pago completo entregado en efectivo, aunque sea mayor al total
                    pago = Pago(
                        venta_id=venta.id,
                        forma_pago_id=forma_pago_id,
                        monto=monto_pago,
                        referencia=pag.get('referencia'),
                        banco=pag.get('banco'),
                        estado='confirmado'
                    )
                    db.session.add(pago)
                    total_pagado += monto_pago
                else:
                    pago = Pago(
                        venta_id=venta.id,
                        forma_pago_id=forma_pago_id,
                        monto=monto_pago,
                        referencia=pag.get('referencia'),
                        banco=pag.get('banco'),
                        estado='confirmado'
                    )
                    db.session.add(pago)
                    total_pagado += monto_pago
                print(f"[DEBUG] total_pagado: {total_pagado}")
            # Calcular vuelto: solo se puede devolver hasta el efectivo entregado, y solo si el total pagado supera el total de la venta
            excedente = total_pagado - Decimal(venta.total)
            if excedente > 0:
                vuelto = min(total_efectivo_entregado, excedente)
            else:
                vuelto = Decimal(0)
            print(f"[DEBUG] total_efectivo_entregado: {total_efectivo_entregado}, venta.total: {venta.total}, total_pagado: {total_pagado}, excedente: {excedente}, vuelto: {vuelto}")
            
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
            print(f"[DEBUG] session vuelto: {session.get('vuelto')}, venta_id: {session.get('venta_id')}, numero_factura: {session.get('numero_factura')}, apertura_caja_id: {session.get('apertura_caja_id')}")
            
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
    print(f"[DEBUG] confirmar_vuelto - vuelto recuperado de session: {vuelto}")
    try:
        vuelto = float(vuelto)
    except Exception as e:
        print(f"[DEBUG] Error convirtiendo vuelto a float: {e}")
        vuelto = 0
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
            import json
            from app.models.nota_debito_detalle import NotaDebitoDetalle
            from app.models.producto import Producto
            
            # VALIDACIONES
            tipo_nd = 'cargo'  # Siempre es cargo
            motivo_tipo = request.form.get('motivo_tipo', '').strip()
            motivo_otro = request.form.get('motivo_otro', '').strip()
            
            # Determinar el motivo final
            if motivo_tipo == 'otro':
                motivo = motivo_otro
            else:
                motivo = motivo_tipo
            
            if not motivo:
                flash('El motivo es obligatorio', 'warning')
                raise ValueError('Motivo vacío')
            
            # Obtener detalles del JSON
            detalle_json = request.form.get('detalle_nd_json')
            detalle = json.loads(detalle_json) if detalle_json else []
            
            if not detalle:
                flash('Debe agregar al menos un detalle a la nota', 'warning')
                raise ValueError('Sin detalles')
            
            # Calcular monto total
            monto_total = sum(float(item['cantidad']) * float(item['precio_unitario']) for item in detalle)
            
            # VALIDAR QUE MONTO NO SUPERE VENTA ORIGINAL
            if monto_total > float(venta.total):
                flash(f'El monto ND (Gs. {monto_total:,.0f}) no puede superar la venta (Gs. {venta.total:,.0f})', 'danger')
                raise ValueError('Monto excesivo')
            
            # VALIDAR DUPLICADOS: No crear dos ND iguales en el mismo día
            hoy = datetime.utcnow().date()
            duplicado = NotaDebito.query.filter(
                NotaDebito.venta_id == venta.id,
                NotaDebito.motivo == motivo,
                db.func.date(NotaDebito.fecha_emision) == hoy
            ).first()
            if duplicado:
                flash('Ya existe una ND con el mismo motivo hoy. Verifique duplicados.', 'warning')
                raise ValueError('Duplicado detectado')
            
            # Generar número secuencial
            ultimo = NotaDebito.query.order_by(NotaDebito.id.desc()).first()
            numero = f"ND-{(ultimo.id + 1 if ultimo else 1):07d}"
            
            # CREAR NOTA DE DÉBITO
            nota = NotaDebito(
                numero_nota=numero,
                venta_id=venta.id,
                tipo=tipo_nd,  # 'cargo' o 'devolución_producto'
                motivo=motivo,
                monto=Decimal(str(monto_total)),
                usuario_id=current_user.id,
                observaciones=request.form.get('observaciones', ''),
                estado_emision='activa',
                estado_pago='pendiente'
            )
            db.session.add(nota)
            db.session.flush()  # Para obtener el id
            
            # GUARDAR DETALLES
            for item in detalle:
                cantidad = float(item['cantidad'])
                precio_unitario = float(item['precio_unitario'])
                subtotal = cantidad * precio_unitario
                
                detalle_nd = NotaDebitoDetalle(
                    nota_debito_id=nota.id,
                    descripcion=item.get('descripcion', ''),
                    cantidad=Decimal(str(cantidad)),
                    precio_unitario=Decimal(str(precio_unitario)),
                    subtotal=Decimal(str(subtotal))
                )
                db.session.add(detalle_nd)
            
            db.session.commit()
            registrar_bitacora('crear-nota-debito', f'Nota de Débito creada: {numero}')
            flash(f'Nota de débito {numero} creada correctamente', 'success')
            return redirect(url_for('ventas.ver', id=venta.id))
            
        except ValueError as e:
            db.session.rollback()
            # Flash ya registrado en validación
            pass
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
    # GET: Mostrar formulario
    ultimo = NotaDebito.query.order_by(NotaDebito.id.desc()).first()
    numero_nota = f"ND-{(ultimo.id + 1 if ultimo else 1):07d}"
    fecha_emision = datetime.now().strftime('%d/%m/%Y')
    
    return render_template('ventas/crear_nota_debito.html', 
                          venta=venta, 
                          numero_nota=numero_nota, 
                          fecha_emision=fecha_emision)

## ===== LISTAR NOTAS DE CRÉDITO Y DÉBITO =====
@bp.route('/notas')
@login_required
def listar_nc_nd():
    from app.models import NotaCredito, NotaDebito
    notas_credito = NotaCredito.query.order_by(NotaCredito.fecha_emision.desc()).all()
    notas_debito = NotaDebito.query.order_by(NotaDebito.fecha_emision.desc()).all()
    return render_template('ventas/listar_nc_nd.html', notas_credito=notas_credito, notas_debito=notas_debito)

# ===== DESCARGAR PDF NOTA DE DÉBITO =====
@bp.route('/notas-debito/pdf/<int:nota_id>')
@login_required
def descargar_nota_debito_pdf(nota_id):
    from app.models import NotaDebito
    from app.utils.nota_debito_ticket import generar_nota_debito_ticket_pdf
    from flask import send_file
    from io import BytesIO
    
    nota = NotaDebito.query.get_or_404(nota_id)
    
    # Generar PDF con el nuevo generador SET-compliant
    pdf_bytes = generar_nota_debito_ticket_pdf(nota)
    
    pdf_buffer = BytesIO(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'nota_debito_{nota.numero_nota}.pdf'
    )

# ===== COBRAR NOTA DE DÉBITO =====
@bp.route('/notas-debito/cobrar/<int:nota_id>', methods=['GET', 'POST'])
@login_required
def cobrar_nota_debito(nota_id):
    from app.models import NotaDebito, PagoNotaDebito, FormaPago
    from decimal import Decimal
    import json
    
    nota = NotaDebito.query.get_or_404(nota_id)
    formas_pago = FormaPago.query.all()

    # Verificar apertura de caja
    apertura = AperturaCaja.query.filter_by(
        cajero_id=current_user.id,
        estado='abierto'
    ).first()
    if not apertura:
        flash('Debes abrir una caja antes de cobrar una Nota de Débito', 'danger')
        return redirect(url_for('caja.estado'))
    
    if request.method == 'POST':
        try:
            # RECIBIR MÚLTIPLES PAGOS DESDE JSON
            pagos_json = request.form.get('pagos_json', '[]')
            pagos = json.loads(pagos_json)
            
            if not pagos:
                flash('Agregue al menos una forma de pago', 'warning')
                raise ValueError('Sin pagos')
            
            # CALCULAR TOTAL DE PAGOS
            total_pagos = sum(Decimal(str(p['monto'])) for p in pagos)
            
            if total_pagos <= 0:
                flash('El total de pagos debe ser mayor a 0', 'warning')
                raise ValueError('Total inválido')

            if total_pagos < Decimal(str(nota.monto_pendiente)):
                flash('El total de pagos es menor al saldo pendiente', 'warning')
                raise ValueError('Saldo incompleto')

            # Validar vuelto: solo se puede devolver hasta el efectivo entregado
            forma_ids = [int(p['forma_pago_id']) for p in pagos if p.get('forma_pago_id') is not None]
            formas = {fp.id: fp.nombre.lower() for fp in FormaPago.query.filter(FormaPago.id.in_(forma_ids)).all()}
            total_efectivo = sum(
                Decimal(str(p['monto']))
                for p in pagos
                if 'efectivo' in (formas.get(int(p['forma_pago_id']), '') or '')
            )
            excedente = total_pagos - Decimal(str(nota.monto_pendiente))
            if excedente > 0 and total_efectivo < excedente:
                flash('El vuelto excede el efectivo entregado. Ajuste los montos.', 'warning')
                raise ValueError('Vuelto sin efectivo')
            
            # REGISTRAR CADA PAGO
            for pago_data in pagos:
                # Validar forma_pago_id
                forma_pago_id = pago_data.get('forma_pago_id')
                try:
                    forma_pago_id = int(forma_pago_id)
                except (TypeError, ValueError):
                    flash('La forma de pago es obligatoria y debe ser válida.', 'danger')
                    registrar_bitacora('pago-nota-debito-error', f"Forma de pago inválida: {forma_pago_id}")
                    raise ValueError('Forma de pago no seleccionada o inválida')
                # Verificar que la FormaPago exista
                forma_pago_obj = FormaPago.query.get(forma_pago_id)
                if not forma_pago_obj:
                    flash('La forma de pago seleccionada no existe.', 'danger')
                    registrar_bitacora('pago-nota-debito-error', f"Forma de pago inexistente: {forma_pago_id}")
                    raise ValueError('Forma de pago no encontrada')
                registrar_bitacora('pago-nota-debito-debug', f"Registrando ND pago: forma_pago_id={forma_pago_id}, monto={pago_data['monto']}")
                pago = PagoNotaDebito(
                    nota_debito_id=nota.id,
                    apertura_caja_id=apertura.id,
                    fecha_pago=datetime.utcnow(),
                    forma_pago_id=forma_pago_id,
                    monto=Decimal(str(pago_data['monto'])),
                    referencia=pago_data.get('referencia', ''),
                    banco=pago_data.get('banco', ''),
                    estado='confirmado'
                )
                db.session.add(pago)
            
            # ACTUALIZAR ESTADO DE PAGO AUTOMÁTICAMENTE
            nota.actualizar_estado_pago()
            
            db.session.commit()
            registrar_bitacora('pago-nota-debito', f'Cobro registrado para ND {nota.numero_nota}: Gs. {total_pagos:,.0f}')
            
            if nota.estado_pago == 'pagado':
                if excedente > 0:
                    flash(f'Nota de Débito {nota.numero_nota} pagada. Vuelto: Gs. {excedente:,.0f}', 'success')
                else:
                    flash(f'Nota de Débito {nota.numero_nota} completamente pagada', 'success')
            else:
                flash(f'Pago parcial registrado. Saldo pendiente: Gs. {nota.monto_pendiente:,.0f}', 'success')
            
            return redirect(url_for('ventas.listar_nc_nd'))
            
        except ValueError as e:
            db.session.rollback()
            pass
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
    return render_template('ventas/cobrar_nota_debito.html', nota=nota, formas_pago=formas_pago)

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
