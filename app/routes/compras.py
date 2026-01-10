from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (Proveedor, PedidoCompra, PedidoCompraDetalle,
                        PresupuestoProveedor, OrdenCompra, Compra, CompraDetalle,
                        CuentaPorPagar, PagoProveedor, Producto, PagoCompra, 
                        MovimientoCaja, AperturaCaja, MovimientoProducto, HistorialPrecio)
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
from sqlalchemy import or_

bp = Blueprint('compras', __name__, url_prefix='/compras')

# ===== PROVEEDORES =====
@bp.route('/proveedores')
@login_required
def proveedores():
    page = request.args.get('page', 1, type=int)
    proveedores = Proveedor.query.filter_by(activo=True).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('compras/proveedores.html', proveedores=proveedores)

@bp.route('/api/proveedores')
@login_required
def api_proveedores():
    """Búsqueda de proveedores por nombre o RUC (AJAX)."""
    term = (request.args.get('term', '') or '').strip()
    query = Proveedor.query.filter(Proveedor.activo == True)
    if term:
        like = f"%{term}%"
        query = query.filter(or_(Proveedor.razon_social.ilike(like), Proveedor.ruc.ilike(like)))
    proveedores = query.order_by(Proveedor.razon_social.asc()).limit(10).all()
    return jsonify([
        {
            'id': p.id,
            'razon_social': p.razon_social,
            'ruc': p.ruc,
            'telefono': p.telefono or '',
            'email': p.email or ''
        } for p in proveedores
    ])

@bp.route('/proveedores/crear', methods=['GET', 'POST'])
@login_required
def crear_proveedor():
    if request.method == 'POST':
        try:
            ultimo = Proveedor.query.order_by(Proveedor.id.desc()).first()
            codigo = f"PROV-{(ultimo.id + 1 if ultimo else 1):04d}"
            
            proveedor = Proveedor(
                codigo=codigo,
                razon_social=request.form.get('razon_social'),
                ruc=request.form.get('ruc'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                email=request.form.get('email'),
                contacto_nombre=request.form.get('contacto_nombre'),
                contacto_telefono=request.form.get('contacto_telefono'),
                tipo_proveedor=request.form.get('tipo_proveedor'),
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(proveedor)
            db.session.commit()
            
            flash('Proveedor creado correctamente', 'success')
            return redirect(url_for('compras.proveedores'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('compras/crear_proveedor.html')

# ===== PROVEEDOR - VER Y EDITAR =====
@bp.route('/proveedores/<int:id>')
@login_required
def ver_proveedor(id):
    """Detalle del proveedor con historial"""
    proveedor = Proveedor.query.get_or_404(id)

    page_comp = request.args.get('page_comp', 1, type=int)
    page_pres = request.args.get('page_pres', 1, type=int)

    compras_pag = Compra.query.filter_by(proveedor_id=proveedor.id).order_by(
        Compra.fecha_compra.desc()).paginate(page=page_comp, per_page=10, error_out=False)

    presupuestos_pag = PresupuestoProveedor.query.filter_by(proveedor_id=proveedor.id).order_by(
        PresupuestoProveedor.fecha_recepcion.desc()).paginate(page=page_pres, per_page=10, error_out=False)

    return render_template('compras/ver_proveedor.html',
                           proveedor=proveedor,
                           compras=compras_pag,
                           presupuestos=presupuestos_pag)


@bp.route('/proveedores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        try:
            proveedor.razon_social = request.form.get('razon_social')
            proveedor.ruc = request.form.get('ruc')
            proveedor.direccion = request.form.get('direccion')
            proveedor.telefono = request.form.get('telefono')
            proveedor.email = request.form.get('email')
            proveedor.contacto_nombre = request.form.get('contacto_nombre')
            proveedor.contacto_telefono = request.form.get('contacto_telefono')
            proveedor.tipo_proveedor = request.form.get('tipo_proveedor')
            proveedor.observaciones = request.form.get('observaciones')

            db.session.commit()
            flash('Proveedor actualizado correctamente', 'success')
            return redirect(url_for('compras.ver_proveedor', id=proveedor.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('compras/editar_proveedor.html', proveedor=proveedor)

# ===== PEDIDOS DE COMPRA =====
@bp.route('/pedidos')
@login_required
def pedidos():
    page = request.args.get('page', 1, type=int)
    pedidos = PedidoCompra.query.order_by(PedidoCompra.fecha_pedido.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('compras/pedidos.html', pedidos=pedidos)

@bp.route('/pedidos/crear', methods=['GET', 'POST'])
@login_required
def crear_pedido():
    if request.method == 'POST':
        try:
            ultimo = PedidoCompra.query.order_by(PedidoCompra.id.desc()).first()
            numero = f"PED-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            pedido = PedidoCompra(
                numero_pedido=numero,
                proveedor_id=request.form.get('proveedor_id'),
                fecha_entrega_estimada=request.form.get('fecha_entrega_estimada'),
                usuario_solicita_id=current_user.id,
                observaciones=request.form.get('observaciones')
            )
            
            # Agregar detalles
            import json
            detalles_json = request.form.get('detalles_json')
            detalles = json.loads(detalles_json)
            
            for det in detalles:
                detalle = PedidoCompraDetalle(
                    pedido=pedido,
                    producto_id=det['producto_id'],
                    cantidad_solicitada=det['cantidad']
                )
                db.session.add(detalle)
            
            db.session.add(pedido)
            db.session.commit()
            
            flash('Pedido creado correctamente', 'success')
            return redirect(url_for('compras.ver_pedido', id=pedido.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    proveedores = Proveedor.query.filter_by(activo=True).all()
    return render_template('compras/crear_pedido.html', proveedores=proveedores)

@bp.route('/pedidos/<int:id>')
@login_required
def ver_pedido(id):
    pedido = PedidoCompra.query.get_or_404(id)
    return render_template('compras/ver_pedido.html', pedido=pedido)

# ===== PRESUPUESTOS DE PROVEEDORES =====
@bp.route('/presupuestos/crear/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
def crear_presupuesto_proveedor(pedido_id):
    pedido = PedidoCompra.query.get_or_404(pedido_id)
    
    if request.method == 'POST':
        try:
            ultimo = PresupuestoProveedor.query.order_by(PresupuestoProveedor.id.desc()).first()
            numero = f"PRES-PROV-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            presupuesto = PresupuestoProveedor(
                numero_presupuesto=numero,
                pedido_id=pedido.id,
                proveedor_id=request.form.get('proveedor_id'),
                subtotal=request.form.get('subtotal'),
                iva=request.form.get('iva'),
                total=request.form.get('total'),
                dias_entrega=request.form.get('dias_entrega'),
                condiciones_pago=request.form.get('condiciones_pago'),
                fecha_validez=request.form.get('fecha_validez'),
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(presupuesto)
            pedido.estado = 'presupuestado'
            db.session.commit()
            
            flash('Presupuesto registrado correctamente', 'success')
            return redirect(url_for('compras.ver_pedido', id=pedido.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    proveedores = Proveedor.query.filter_by(activo=True).all()
    return render_template('compras/crear_presupuesto_proveedor.html', 
                         pedido=pedido, proveedores=proveedores)

# ===== ÓRDENES DE COMPRA =====
@bp.route('/ordenes')
@login_required
def ordenes():
    page = request.args.get('page', 1, type=int)
    ordenes = OrdenCompra.query.order_by(OrdenCompra.fecha_orden.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('compras/ordenes.html', ordenes=ordenes)

@bp.route('/ordenes/crear/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
def crear_orden(pedido_id):
    pedido = PedidoCompra.query.get_or_404(pedido_id)
    
    if request.method == 'POST':
        try:
            ultimo = OrdenCompra.query.order_by(OrdenCompra.id.desc()).first()
            numero = f"OC-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            orden = OrdenCompra(
                numero_orden=numero,
                pedido_id=pedido.id,
                presupuesto_proveedor_id=request.form.get('presupuesto_proveedor_id'),
                proveedor_id=pedido.proveedor_id,
                subtotal=request.form.get('subtotal'),
                iva=request.form.get('iva'),
                total=request.form.get('total'),
                fecha_entrega_estimada=request.form.get('fecha_entrega_estimada'),
                usuario_autoriza_id=current_user.id,
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(orden)
            pedido.estado = 'aprobado'
            db.session.commit()
            
            flash('Orden de compra creada correctamente', 'success')
            return redirect(url_for('compras.ver_orden', id=orden.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    presupuestos = pedido.presupuestos.all()
    return render_template('compras/crear_orden.html', pedido=pedido, presupuestos=presupuestos)

@bp.route('/ordenes/<int:id>')
@login_required
def ver_orden(id):
    orden = OrdenCompra.query.get_or_404(id)
    return render_template('compras/ver_orden.html', orden=orden)

# ===== COMPRAS =====
@bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    compras = Compra.query.order_by(Compra.fecha_compra.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('compras/listar.html', compras=compras)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_compra():
    """Redirige a la nueva ruta de registrar compra"""
    return redirect(url_for('compras.registrar_compra'))

@bp.route('/<int:id>')
@login_required
def ver(id):
    compra = Compra.query.get_or_404(id)
    return render_template('compras/ver.html', compra=compra)

# ===== CUENTAS POR PAGAR =====
@bp.route('/cuentas-por-pagar')
@login_required
def cuentas_por_pagar():
    page = request.args.get('page', 1, type=int)
    
    cuentas = CuentaPorPagar.query.filter(
        CuentaPorPagar.estado.in_(['pendiente', 'parcial', 'vencida'])
    ).order_by(CuentaPorPagar.fecha_vencimiento).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compras/cuentas_por_pagar.html', cuentas=cuentas)

@bp.route('/registrar-pago-proveedor/<int:cuenta_id>', methods=['POST'])
@login_required
def registrar_pago_proveedor(cuenta_id):
    cuenta = CuentaPorPagar.query.get_or_404(cuenta_id)
    
    try:
        pago = PagoProveedor(
            cuenta_id=cuenta.id,
            monto=request.form.get('monto'),
            forma_pago=request.form.get('forma_pago'),
            referencia=request.form.get('referencia'),
            banco=request.form.get('banco'),
            usuario_registra_id=current_user.id,
            observaciones=request.form.get('observaciones')
        )
        
        cuenta.monto_pagado += pago.monto
        cuenta.actualizar_estado()
        
        db.session.add(pago)
        db.session.commit()
        
        flash('Pago registrado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('compras.cuentas_por_pagar'))


# ===== NUEVO FLUJO SIMPLIFICADO DE COMPRAS =====

@bp.route('/registrar-compra', methods=['GET', 'POST'])
@login_required
def registrar_compra():
    """Registra compra sin pagar (estado=registrada)"""
    if request.method == 'POST':
        try:
            # Generar número de compra
            ultimo = Compra.query.filter(Compra.numero_compra.isnot(None)).order_by(
                Compra.id.desc()).first()
            numero = f"C-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            numero_factura = request.form.get('numero_factura') or None
            fecha_factura_str = request.form.get('fecha_factura') or None
            fecha_factura = None
            if fecha_factura_str:
                try:
                    fecha_factura = datetime.strptime(fecha_factura_str, '%Y-%m-%d').date()
                except ValueError:
                    fecha_factura = None

            # Crear compra en estado registrada (sin pagar)
            compra = Compra(
                numero_compra=numero,
                proveedor_id=request.form.get('proveedor_id'),
                tipo=request.form.get('tipo'),  # producto, servicio, factura, gasto
                descripcion=request.form.get('descripcion'),
                numero_factura=numero_factura,
                fecha_factura=fecha_factura,
                estado='registrada',  # Siempre empieza en registrada
                usuario_registra_id=current_user.id,
                fecha_compra=datetime.utcnow()
            )
            
            # Procesar detalles
            detalles_json = request.form.get('detalles_json')
            if not detalles_json:
                detalles_json = '[]'
            detalles = json.loads(detalles_json)
            
            subtotal = 0
            for det in detalles:
                cantidad = float(det.get('cantidad', 0))
                precio_unitario = float(det.get('precio_unitario', 0))
                subtotal_det = cantidad * precio_unitario
                subtotal += subtotal_det
                
                # Crear detalle de compra (stock se actualiza al PAGAR, no al registrar)
                detalle = CompraDetalle(
                    compra=compra,
                    producto_id=det.get('producto_id') if compra.tipo == 'producto' else None,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal_det,
                    concepto=det.get('concepto', '')  # Para servicios/facturas
                )
                db.session.add(detalle)
            
            # Calcular totales (IVA INCLUIDO)
            # Si el precio ya incluye IVA 10%, entonces:
            # Total = subtotal (con IVA incluido)
            # IVA = Total / 11 (porque 100% + 10% = 110% = 11/10)
            # Subtotal sin IVA = Total - IVA
            total = subtotal  # El precio ingresado ya incluye IVA
            iva = total / 11  # IVA incluido
            subtotal_sin_iva = total - iva
            
            compra.subtotal = subtotal_sin_iva
            compra.iva = iva
            compra.total = total
            
            # Stock se actualiza SOLO al pagar, no al registrar
            compra.stock_actualizado = False
            
            db.session.add(compra)
            db.session.commit()
            
            flash('Compra registrada correctamente', 'success')
            return redirect(url_for('compras.pendientes_pago'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar compra: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
    proveedores = Proveedor.query.filter_by(activo=True).all()
    return render_template('compras/registrar_compra.html', proveedores=proveedores)


@bp.route('/pendientes-pago')
@login_required
def pendientes_pago():
    """Lista compras sin pagar o parcialmente pagadas"""
    page = request.args.get('page', 1, type=int)
    
    # Mostrar compras registradas o parcialmente pagadas
    compras = Compra.query.filter(
        Compra.estado.in_(['registrada', 'parcial_pagada'])
    ).order_by(Compra.fecha_compra.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compras/pendientes_pago.html', compras=compras)


@bp.route('/get-caja-abierta', methods=['GET'])
@login_required
def get_caja_abierta():
    """Obtiene la apertura de caja activa"""
    apertura = AperturaCaja.query.filter_by(estado='abierto').first()
    if apertura:
        return jsonify({
            'id': apertura.id,
            'numero_caja': apertura.caja.numero_caja,
            'monto_inicial': float(apertura.monto_inicial or 0)
        })
    return jsonify({'error': 'No hay caja abierta'}), 404


@bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def pagar_compra(id):
    """Registra pago de compra con origen flexible y actualiza stock"""
    import sys
    compra = Compra.query.get_or_404(id)
    
    try:
        monto = Decimal(str(request.form.get('monto', 0) or 0))
        origen_pago = request.form.get('origen_pago')  # caja_chica, otra_fuente, dejar_credito
        print(f"DEBUG pagar_compra: compra={id}, origen={origen_pago}, monto={monto}", file=sys.stderr, flush=True)
        
        # Validar monto solo cuando NO es crédito
        if origen_pago != 'dejar_credito':
            if monto <= 0:
                flash('El monto debe ser mayor a 0', 'danger')
                return redirect(url_for('compras.pendientes_pago'))
        
        # Actualizar stock SOLO al pagar (si es tipo producto y no se ha actualizado)
        if compra.tipo == 'producto' and not compra.stock_actualizado:
            for det in compra.detalles:
                if det.producto_id:
                    producto = Producto.query.get(det.producto_id)
                    if producto:
                        stock_anterior = int(producto.stock_actual or 0)
                        cantidad_int = int(round(det.cantidad))
                        stock_nuevo = stock_anterior + cantidad_int
                        producto.stock_actual = stock_nuevo
                        
                        # Registrar movimiento de stock
                        movimiento = MovimientoProducto(
                            producto_id=producto.id,
                            tipo_movimiento='entrada',
                            cantidad=cantidad_int,
                            stock_anterior=stock_anterior,
                            stock_actual=stock_nuevo,
                            motivo='compra_pagada',
                            referencia_tipo='compra',
                            referencia_id=compra.id,
                            costo_unitario=det.precio_unitario,
                            usuario_id=current_user.id
                        )
                        db.session.add(movimiento)
                        
                        # Actualizar precio de compra si es diferente
                        if det.precio_unitario != (producto.precio_compra or Decimal('0')):
                            historial = HistorialPrecio(
                                producto_id=producto.id,
                                precio_compra_anterior=producto.precio_compra,
                                precio_compra_nuevo=det.precio_unitario,
                                usuario_id=current_user.id,
                                motivo='Actualización por compra pagada'
                            )
                            db.session.add(historial)
                            producto.precio_compra = det.precio_unitario
            
            compra.stock_actualizado = True
        
        
        if origen_pago == 'dejar_credito':
            # Parámetros de crédito
            try:
                plazo_credito_dias = int(request.form.get('plazo_credito_dias') or 0)
            except ValueError:
                plazo_credito_dias = 0
            fecha_base = datetime.utcnow().date()
            fecha_venc = fecha_base + timedelta(days=plazo_credito_dias) if plazo_credito_dias > 0 else None
            obs_credito = request.form.get('observaciones_credito', '')
            
            # Guardar en la compra
            compra.plazo_credito_dias = plazo_credito_dias or None
            compra.fecha_vencimiento_credito = fecha_venc
            compra.observaciones_credito = obs_credito
            
            # Crear cuenta por pagar completa (no registra pago)
            cuenta = CuentaPorPagar(
                compra_id=compra.id,
                proveedor_id=compra.proveedor_id,
                monto_adeudado=compra.total,
                estado='pendiente',
                fecha_vencimiento=fecha_venc,
                observaciones=obs_credito
            )
            db.session.add(cuenta)
            compra.estado = 'registrada'  # Queda registrada sin pagar (a crédito)
            
        elif origen_pago == 'caja_chica':
            # Descuenta de apertura de caja
            print(f"DEBUG: entró a caja_chica", file=sys.stderr, flush=True)
            apertura = AperturaCaja.query.filter_by(estado='abierto').first()
            if not apertura:
                flash('Debe abrir una caja primero', 'danger')
                return redirect(url_for('compras.pendientes_pago'))

            # Verificar fondos suficientes en caja
            disponible = apertura.monto_final if apertura.monto_final is not None else (apertura.monto_inicial or Decimal('0'))
            print(f"DEBUG: disponible={disponible}, monto={monto}", file=sys.stderr, flush=True)
            if disponible < monto:
                flash('Fondos insuficientes en caja', 'danger')
                return redirect(url_for('compras.pendientes_pago'))

            # Crear movimiento de egreso (salida) por compra
            print(f"DEBUG: creando MovimientoCaja", file=sys.stderr, flush=True)
            movimiento = MovimientoCaja(
                apertura_caja_id=apertura.id,
                tipo='egreso',
                concepto='Compra',
                monto=monto,
                referencia_tipo='compra',
                referencia_id=compra.id,
                usuario_id=current_user.id
            )
            db.session.add(movimiento)
            db.session.flush()  # Obtener ID del movimiento

            # Crear registro de pago
            print(f"DEBUG: creando PagoCompra", file=sys.stderr, flush=True)
            pago = PagoCompra(
                compra_id=compra.id,
                monto=monto,
                origen_pago='caja_chica',
                apertura_caja_id=apertura.id,
                movimiento_caja_id=movimiento.id,
                referencia=request.form.get('referencia', ''),
                usuario_paga_id=current_user.id
            )

            # Actualizar monto en apertura caja (efectivo disponible)
            apertura.monto_final = disponible - monto

            # Actualizar estado de compra
            saldo_pendiente = compra.total - monto
            if saldo_pendiente <= 0:
                compra.estado = 'pagada'
            else:
                compra.estado = 'parcial_pagada'
                # Crear CxP por la diferencia
                cuenta = CuentaPorPagar(
                    compra_id=compra.id,
                    proveedor_id=compra.proveedor_id,
                    monto_total=compra.total,
                    monto_adeudado=saldo_pendiente,
                    estado='pendiente'
                )
                db.session.add(cuenta)

            db.session.add(pago)
            print(f"DEBUG: pago agregado a sesión, estado compra={compra.estado}", file=sys.stderr, flush=True)
            
        elif origen_pago == 'otra_fuente':
            # Pago externo, no afecta caja
            pago = PagoCompra(
                compra_id=compra.id,
                monto=monto,
                origen_pago='otra_fuente',
                referencia=request.form.get('referencia', ''),
                usuario_paga_id=current_user.id
            )
            
            # Actualizar estado de compra
            saldo_pendiente = compra.total - monto
            if saldo_pendiente <= 0:
                compra.estado = 'pagada'
            else:
                compra.estado = 'parcial_pagada'
                # Crear CxP por la diferencia
                cuenta = CuentaPorPagar(
                    compra_id=compra.id,
                    proveedor_id=compra.proveedor_id,
                    monto_total=compra.total,
                    monto_adeudado=saldo_pendiente,
                    estado='pendiente'
                )
                db.session.add(cuenta)
            
            db.session.add(pago)
        
        print(f"DEBUG: before commit, pago estado={getattr(pago, 'id', 'no-id')}", file=sys.stderr, flush=True)
        db.session.commit()
        print(f"DEBUG: after commit, pago id={pago.id if 'pago' in locals() else 'N/A'}", file=sys.stderr, flush=True)
        if origen_pago == 'dejar_credito':
            flash('Compra dejada a crédito. Stock actualizado y CxP creada.', 'success')
        else:
            flash('Pago registrado correctamente', 'success')
        return redirect(url_for('compras.pendientes_pago'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar pago: {str(e)}', 'danger')
        return redirect(url_for('compras.pendientes_pago'))


@bp.route('/cuentas-por-pagar-compras')
@login_required
def cuentas_por_pagar_compras():
    """Lista cuentas por pagar de compras"""
    page = request.args.get('page', 1, type=int)
    
    cuentas = CuentaPorPagar.query.filter(
        CuentaPorPagar.estado.in_(['pendiente', 'parcial'])
    ).order_by(CuentaPorPagar.fecha_vencimiento.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compras/cuentas_por_pagar_compras.html', cuentas=cuentas)


@bp.route('/api/compra/<int:id>')
@login_required
def get_compra_api(id):
    """API endpoint para obtener datos de una compra"""
    compra = Compra.query.get_or_404(id)
    
    return jsonify({
        'id': compra.id,
        'numero_compra': compra.numero_compra,
        'proveedor': compra.proveedor.razon_social if compra.proveedor else 'N/A',
        'tipo': compra.tipo,
        'total': float(compra.total or 0),
        'subtotal': float(compra.subtotal or 0),
        'iva': float(compra.iva or 0),
        'estado': compra.estado
    })

