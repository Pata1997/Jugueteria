

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.utils.roles import require_roles
from app import db
from app.models import (TipoServicio, SolicitudServicio, Presupuesto, PresupuestoDetalle,
                        OrdenServicio, OrdenServicioDetalle, Reclamo, ReclamoSeguimiento,
                        Cliente, Producto, Venta, VentaDetalle, Usuario)
from datetime import datetime, date
from app.utils import registrar_bitacora

bp = Blueprint('servicios', __name__, url_prefix='/servicios')





# Ruta para editar reclamo (POST)
@bp.route('/reclamos/<int:id>', methods=['POST'])
@login_required
def editar_reclamo(id):
    reclamo = Reclamo.query.get_or_404(id)
    estado = request.form.get('estado')
    solucion = request.form.get('solucion')
    reclamo.estado = estado
    reclamo.solucion = solucion
    db.session.commit()
    flash('Reclamo actualizado correctamente', 'success')
    return redirect(url_for('servicios.reclamos'))

# ...existing code...

@bp.route('/api/buscar_factura')
@login_required
def api_buscar_factura():
    q = request.args.get('q', '')
    facturas = Venta.query.filter(Venta.numero_factura.like(f'%{q}%')).limit(10).all()
    resultados = [
        {'id': f.id, 'numero': f.numero_factura, 'cliente': f.cliente.nombre}
        for f in facturas
    ]
    return jsonify(resultados)

@bp.route('/api/detalle_factura')
@login_required
def api_detalle_factura():
    id = request.args.get('id')
    factura = Venta.query.get_or_404(id)
    trabajos = []
    for d in factura.detalles:
        detalle = d.descripcion
        if hasattr(d, 'producto') and d.producto:
            detalle = f"{d.producto.nombre} ({d.descripcion})"
        trabajos.append({
            'detalle': detalle,
            'tipo': d.tipo_item,
            'precio': float(d.precio_unitario),
            'cantidad': float(d.cantidad)
        })
    data = {
        'cliente': factura.cliente.nombre,
        'fecha': factura.fecha_venta.strftime('%d/%m/%Y'),
        'total': float(factura.total),
        'trabajos': trabajos
    }
    return jsonify(data)
@bp.route('/reclamos/nuevo', methods=['GET'])
@login_required
def nuevo_reclamo():
    return render_template('servicios/nuevo_reclamo.html')

# ===== TIPOS DE SERVICIO =====
@bp.route('/tipos')
@login_required
@require_roles('admin', 'tecnico', 'recepcion')
def tipos():
    tipos = TipoServicio.query.filter_by(activo=True).all()
    from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
    from flask_login import login_required, current_user
    from app.utils.roles import require_roles
    from app import db
    from app.models import (TipoServicio, SolicitudServicio, Presupuesto, PresupuestoDetalle,
                            OrdenServicio, OrdenServicioDetalle, Reclamo, ReclamoSeguimiento,
                            Cliente, Producto, Venta, VentaDetalle, Usuario)
    from datetime import datetime, date
    from app.utils import registrar_bitacora

    bp = Blueprint('servicios', __name__, url_prefix='/servicios')


    # Ruta para editar reclamo (POST)
    @bp.route('/reclamos/<int:id>', methods=['POST'])
    @login_required
    def editar_reclamo(id):
        reclamo = Reclamo.query.get_or_404(id)
        estado = request.form.get('estado')
        solucion = request.form.get('solucion')
        reclamo.estado = estado
        reclamo.solucion = solucion
        db.session.commit()
        flash('Reclamo actualizado correctamente', 'success')
        return redirect(url_for('servicios.reclamos'))
    return render_template('servicios/tipos.html', tipos=tipos)

@bp.route('/tipos/crear', methods=['POST'])
@login_required
def crear_tipo():
    try:
        tipo = TipoServicio(
            codigo=request.form.get('codigo'),
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            precio_base=request.form.get('precio_base', 0),
            tiempo_estimado=request.form.get('tiempo_estimado', 1)
        )
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de servicio creado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.tipos'))

@bp.route('/tipos/<int:id>/editar', methods=['POST'])
@login_required
def editar_tipo(id):
    tipo = TipoServicio.query.get_or_404(id)
    try:
        tipo.codigo = request.form.get('codigo')
        tipo.nombre = request.form.get('nombre')
        tipo.descripcion = request.form.get('descripcion')
        tipo.precio_base = request.form.get('precio_base', 0)
        tipo.tiempo_estimado = request.form.get('tiempo_estimado', 1)
        
        db.session.commit()
        flash('Tipo de servicio actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.tipos'))

@bp.route('/tipos/<int:id>/inhabilitar', methods=['POST'])
@login_required
def inhabilitar_tipo(id):
    tipo = TipoServicio.query.get_or_404(id)
    try:
        tipo.activo = False
        db.session.commit()
        flash(f'Tipo de servicio "{tipo.nombre}" deshabilitado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.tipos'))

# ===== SOLICITUDES =====
@bp.route('/solicitudes')
@login_required
def solicitudes():
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = SolicitudServicio.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    solicitudes = query.order_by(SolicitudServicio.fecha_solicitud.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('servicios/solicitudes.html', solicitudes=solicitudes)

@bp.route('/solicitudes/crear', methods=['GET', 'POST'])
@login_required
def crear_solicitud():
    if request.method == 'POST':
        try:
            # Procesar líneas JSON y validar stock
            import json
            lineas_json = request.form.get('lineas_json', '[]')
            lineas = json.loads(lineas_json)
            
            # Validar stock de productos
            from app.models import Producto
            productos_sin_stock = []
            
            for linea in lineas:
                if linea.get('tipo_item') == 'producto':
                    producto_id = linea.get('item_id')
                    cantidad_requerida = int(linea.get('cantidad', 0))
                    
                    if producto_id and cantidad_requerida > 0:
                        producto = Producto.query.get(producto_id)
                        if producto:
                            if producto.stock_actual < cantidad_requerida:
                                productos_sin_stock.append({
                                    'nombre': producto.nombre,
                                    'codigo': producto.codigo,
                                    'requerido': cantidad_requerida,
                                    'disponible': producto.stock_actual
                                })
            
            # Si hay productos sin stock, mostrar error
            if productos_sin_stock:
                mensaje_error = 'No se puede crear la solicitud por falta de stock:\n'
                for p in productos_sin_stock:
                    mensaje_error += f"\n• {p['nombre']} (Código: {p['codigo']}) - Necesita: {p['requerido']} unidades, Disponible: {p['disponible']}"
                flash(mensaje_error, 'warning')
                
                # Retornar a formulario con datos
                clientes = Cliente.query.filter_by(activo=True).all()
                tipos = TipoServicio.query.filter_by(activo=True).all()
                return render_template('servicios/crear_solicitud.html', 
                                     clientes=clientes, 
                                     tipos=tipos, 
                                     tipos_servicio=tipos,
                                     form_data=request.form)
            
            # Si hay suficiente stock, continuar
            # Generar número de solicitud
            ultimo = SolicitudServicio.query.order_by(SolicitudServicio.id.desc()).first()
            numero = f"SOL-{(ultimo.id + 1 if ultimo else 1):06d}"

            # Procesar líneas
            cliente_id = request.form.get('cliente_id')
            cliente = Cliente.query.get(cliente_id)
            
            costo_estimado = 0
            for linea in lineas:
                costo_estimado += float(linea.get('subtotal', 0))
            
            descuento_estimado = 0
            if cliente and cliente.descuento_especial:
                descuento_estimado = costo_estimado * (float(cliente.descuento_especial) / 100)
            total_estimado = costo_estimado - descuento_estimado
            
            # Obtener primer servicio para tipo_servicio_id
            primer_servicio_id = None
            for linea in lineas:
                if linea.get('tipo_item') == 'servicio':
                    primer_servicio_id = linea.get('item_id')
                    break
            
            solicitud = SolicitudServicio(
                numero_solicitud=numero,
                cliente_id=cliente_id,
                tipo_servicio_id=primer_servicio_id or 1,
                descripcion=request.form.get('descripcion'),
                prioridad=request.form.get('prioridad', 'normal'),
                fecha_estimada=request.form.get('fecha_estimada') or None,
                usuario_registro_id=current_user.id,
                observaciones=request.form.get('observaciones'),
                costo_estimado=costo_estimado,
                descuento_estimado=descuento_estimado,
                total_estimado=total_estimado
            )
            
            db.session.add(solicitud)
            db.session.flush()
            
            # Guardar referencia de líneas separadas de observaciones usuario
            obs_usuario = request.form.get('observaciones', '').strip()
            lineas_json_str = json.dumps(lineas)
            if obs_usuario:
                solicitud.observaciones = f"{obs_usuario}\n\n[LÍNEAS]{lineas_json_str}"
            else:
                solicitud.observaciones = f"[LÍNEAS]{lineas_json_str}"
            
            db.session.commit()
            registrar_bitacora('crear-solicitud', f'Solicitud creada: {solicitud.numero_solicitud} para cliente {solicitud.cliente_id}')
            flash('Solicitud creada correctamente', 'success')
            return redirect(url_for('servicios.ver_solicitud', id=solicitud.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    clientes = Cliente.query.filter_by(activo=True).all()
    tipos = TipoServicio.query.filter_by(activo=True).all()
    return render_template('servicios/crear_solicitud.html', clientes=clientes, tipos=tipos, tipos_servicio=tipos)

@bp.route('/solicitudes/<int:id>')
@login_required
def ver_solicitud(id):
    solicitud = SolicitudServicio.query.get_or_404(id)
    # Pasar diccionarios de tipos y productos para resolver IDs en template
    tipos_servicio = {t.id: t for t in TipoServicio.query.all()}
    productos = {p.id: p for p in Producto.query.all()}
    
    # Parsear líneas desde observaciones
    lineas = []
    if solicitud.observaciones and '[LÍNEAS]' in solicitud.observaciones:
        try:
            import json
            partes = solicitud.observaciones.split('[LÍNEAS]')
            if len(partes) > 1:
                lineas_json_str = partes[1].strip()
                lineas = json.loads(lineas_json_str)
        except:
            pass
    
    return render_template('servicios/ver_solicitud.html', 
                          solicitud=solicitud,
                          tipos_servicio=tipos_servicio,
                          productos=productos,
                          lineas=lineas)

@bp.route('/solicitudes/<int:id>/aprobar', methods=['POST'])
@login_required
def aprobar_solicitud(id):
    solicitud = SolicitudServicio.query.get_or_404(id)
    try:
        solicitud.estado = 'en_proceso'
        
        # Parsear líneas desde observaciones
        lineas = []
        if solicitud.observaciones and '[LÍNEAS]' in solicitud.observaciones:
            import json
            partes = solicitud.observaciones.split('[LÍNEAS]')
            if len(partes) > 1:
                lineas_json_str = partes[1].strip()
                lineas = json.loads(lineas_json_str)
        
        # Si no hay líneas, usar el método viejo como fallback
        if not lineas:
            monto_servicio = float(solicitud.total_estimado or solicitud.costo_estimado or 0)
            lineas = [{
                'tipo_item': 'servicio',
                'item_id': solicitud.tipo_servicio_id,
                'cantidad': 1,
                'precio_unitario': monto_servicio,
                'subtotal': monto_servicio
            }]
        
        # Calcular totales desglosados (precios ya incluyen IVA)
        subtotal_general = 0  # Suma de precios IVA incluido
        iva_10_monto = 0
        iva_5_monto = 0
        subtotal_exentas = 0
        
        numero_provisorio = f"TMP-{solicitud.numero_solicitud}"
        venta = Venta(
            numero_factura=numero_provisorio,
            tipo_venta='servicio',
            cliente_id=solicitud.cliente_id,
            vendedor_id=current_user.id,
            estado='pendiente',
            estado_pago='pendiente',
            observaciones=f"Solicitud {solicitud.numero_solicitud} aprobada"
        )
        db.session.add(venta)
        db.session.flush()
        
        # Crear VentaDetalle por cada línea
        for linea in lineas:
            tipo_item = linea.get('tipo_item')
            item_id = int(linea.get('item_id'))
            cantidad = float(linea.get('cantidad', 1))
            precio_unit = float(linea.get('precio_unitario', 0))
            subtotal_linea = float(linea.get('subtotal', 0))
            
            # Obtener descripción e IVA
            tipo_iva = 'exenta'  # Por defecto productos/insumos
            descripcion = ''
            producto_id = None
            servicio_id = None
            
            if tipo_item == 'servicio':
                tipo_serv = TipoServicio.query.get(item_id)
                if tipo_serv:
                    descripcion = f"{tipo_serv.nombre}"
                    if tipo_serv.descripcion:
                        descripcion += f" - {tipo_serv.descripcion}"
                    servicio_id = item_id
                tipo_iva = '10'  # Servicios llevan IVA 10% en Paraguay
            else:  # producto
                producto = Producto.query.get(item_id)
                if producto:
                    descripcion = f"{producto.codigo} - {producto.nombre}"
                    tipo_iva = producto.tipo_iva or 'exenta'
                    producto_id = item_id
            
            # Calcular IVA de esta línea según tipo (IVA incluido en precio)
            iva_linea = 0
            if tipo_iva == '10':
                iva_linea = subtotal_linea / 11  # IVA incluido al 10%
                iva_10_monto += iva_linea
            elif tipo_iva == '5':
                iva_linea = subtotal_linea / 21  # IVA incluido al 5%
                iva_5_monto += iva_linea
            else:  # exenta
                subtotal_exentas += subtotal_linea
            
            subtotal_general += subtotal_linea
            
            # Crear detalle: total ya incluye IVA (no volver a sumar)
            detalle = VentaDetalle(
                venta_id=venta.id,
                producto_id=producto_id,
                tipo_item=tipo_item,
                descripcion=descripcion,
                cantidad=cantidad,
                precio_unitario=precio_unit,
                subtotal=subtotal_linea,
                descuento=0,
                total=subtotal_linea
            )
            db.session.add(detalle)
        
        # Actualizar totales de venta
        venta.subtotal = subtotal_general
        venta.descuento = float(solicitud.descuento_estimado or 0)
        venta.iva = iva_10_monto + iva_5_monto
        # Total ya incluye IVA en cada línea; no sumamos de nuevo
        venta.total = subtotal_general - venta.descuento
        
        # Guardar desglose de IVA en observaciones de venta (formato JSON para parsear fácil)
        import json
        desglose_iva = {
            'iva_10': iva_10_monto,
            'iva_5': iva_5_monto,
            'exentas': subtotal_exentas
        }
        venta.observaciones += f"\n[DESGLOSE_IVA]{json.dumps(desglose_iva)}"
        
        db.session.commit()
        registrar_bitacora('aprobar-solicitud', f'Solicitud aprobada: {solicitud.numero_solicitud} por usuario {current_user.username}')
        flash('Solicitud aprobada y venta pendiente creada con detalle completo', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('servicios.ver_solicitud', id=id))

@bp.route('/solicitudes/<int:id>/rechazar', methods=['POST'])
@login_required
def rechazar_solicitud(id):
    solicitud = SolicitudServicio.query.get_or_404(id)
    try:
        solicitud.estado = 'rechazado'
        db.session.commit()
        registrar_bitacora('rechazar-solicitud', f'Solicitud rechazada: {solicitud.numero_solicitud} por usuario {current_user.username}')
        flash('Solicitud rechazada', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('servicios.ver_solicitud', id=id))

@bp.route('/solicitudes/<int:id>/terminar', methods=['POST'])
@login_required
def terminar_solicitud(id):
    solicitud = SolicitudServicio.query.get_or_404(id)
    try:
        solicitud.estado = 'terminado'
        db.session.commit()
        registrar_bitacora('terminar-solicitud', f'Solicitud terminada: {solicitud.numero_solicitud} por usuario {current_user.username}')
        flash('Solicitud marcada como terminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('servicios.ver_solicitud', id=id))

# ===== PRESUPUESTOS =====
@bp.route('/presupuestos/crear/<int:solicitud_id>', methods=['GET', 'POST'])
@login_required
def crear_presupuesto(solicitud_id):
    solicitud = SolicitudServicio.query.get_or_404(solicitud_id)
    
    if request.method == 'POST':
        try:
            ultimo = Presupuesto.query.order_by(Presupuesto.id.desc()).first()
            numero = f"PRES-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            presupuesto = Presupuesto(
                numero_presupuesto=numero,
                solicitud_id=solicitud.id,
                descripcion_trabajo=request.form.get('descripcion_trabajo'),
                mano_obra=request.form.get('mano_obra', 0),
                costo_materiales=request.form.get('costo_materiales', 0),
                otros_costos=request.form.get('otros_costos', 0),
                descuento=request.form.get('descuento', 0),
                iva=request.form.get('iva', 0),
                dias_estimados=request.form.get('dias_estimados'),
                fecha_validez=request.form.get('fecha_validez'),
                usuario_elabora_id=current_user.id,
                observaciones=request.form.get('observaciones')
            )
            
            presupuesto.calcular_totales()
            
            # Agregar detalles
            detalles_json = request.form.get('detalles_json')
            if detalles_json:
                import json
                detalles = json.loads(detalles_json)
                for det in detalles:
                    detalle = PresupuestoDetalle(
                        presupuesto=presupuesto,
                        producto_id=det.get('producto_id'),
                        descripcion=det['descripcion'],
                        cantidad=det['cantidad'],
                        precio_unitario=det['precio_unitario'],
                        subtotal=det['subtotal']
                    )
                    db.session.add(detalle)
            
            solicitud.estado = 'presupuestado'
            
            db.session.add(presupuesto)
            db.session.commit()
            
            flash('Presupuesto creado correctamente', 'success')
            return redirect(url_for('servicios.ver_presupuesto', id=presupuesto.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('servicios/crear_presupuesto.html', solicitud=solicitud)

@bp.route('/presupuestos/<int:id>')
@login_required
def ver_presupuesto(id):
    presupuesto = Presupuesto.query.get_or_404(id)
    return render_template('servicios/ver_presupuesto.html', presupuesto=presupuesto)

@bp.route('/presupuestos/<int:id>/aprobar', methods=['POST'])
@login_required
def aprobar_presupuesto(id):
    presupuesto = Presupuesto.query.get_or_404(id)
    
    try:
        presupuesto.estado = 'aprobado'
        presupuesto.fecha_aprobacion = datetime.utcnow()
        presupuesto.solicitud.estado = 'aprobado'
        
        db.session.commit()
        flash('Presupuesto aprobado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.ver_presupuesto', id=id))

# ===== ÓRDENES DE SERVICIO =====
@bp.route('/ordenes')
@login_required
def ordenes():
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = OrdenServicio.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    ordenes = query.order_by(OrdenServicio.fecha_orden.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('servicios/ordenes.html', ordenes=ordenes)

@bp.route('/ordenes/crear/<int:solicitud_id>', methods=['GET', 'POST'])
@login_required
def crear_orden(solicitud_id):
    solicitud = SolicitudServicio.query.get_or_404(solicitud_id)
    presupuesto = solicitud.presupuestos.filter_by(estado='aprobado').first()
    
    if request.method == 'POST':
        try:
            ultimo = OrdenServicio.query.order_by(OrdenServicio.id.desc()).first()
            numero = f"OS-{(ultimo.id + 1 if ultimo else 1):06d}"
            
            orden = OrdenServicio(
                numero_orden=numero,
                solicitud_id=solicitud.id,
                presupuesto_id=presupuesto.id if presupuesto else None,
                tecnico_id=request.form.get('tecnico_id'),
                fecha_inicio=request.form.get('fecha_inicio'),
                fecha_fin_estimada=request.form.get('fecha_fin_estimada'),
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(orden)
            db.session.commit()
            
            flash('Orden de servicio creada correctamente', 'success')
            return redirect(url_for('servicios.ver_orden', id=orden.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # Obtener usuarios con rol 'tecnico' en lugar de empleados
    tecnicos = Usuario.query.filter_by(activo=True, rol='tecnico').all()
    return render_template('servicios/crear_orden.html', 
                         solicitud=solicitud, 
                         presupuesto=presupuesto,
                         tecnicos=tecnicos)

@bp.route('/ordenes/<int:id>')
@login_required
def ver_orden(id):
    orden = OrdenServicio.query.get_or_404(id)
    return render_template('servicios/ver_orden.html', orden=orden)

@bp.route('/ordenes/<int:id>/actualizar-estado', methods=['POST'])
@login_required
def actualizar_estado_orden(id):
    orden = OrdenServicio.query.get_or_404(id)
    
    try:
        estado_nuevo = request.form.get('estado')
        orden.estado = estado_nuevo
        
        if estado_nuevo == 'en_proceso' and not orden.fecha_inicio:
            orden.fecha_inicio = datetime.utcnow()
        elif estado_nuevo == 'finalizado':
            orden.fecha_fin_real = datetime.utcnow()
            orden.trabajo_realizado = request.form.get('trabajo_realizado')
        
        db.session.commit()
        flash('Estado actualizado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.ver_orden', id=id))

@bp.route('/ordenes/<int:id>/registrar-insumo', methods=['POST'])
@login_required
def registrar_insumo(id):
    orden = OrdenServicio.query.get_or_404(id)
    
    try:
        producto_id = request.form.get('producto_id')
        cantidad = float(request.form.get('cantidad'))
        
        producto = Producto.query.get(producto_id)
        
        detalle = OrdenServicioDetalle(
            orden_id=orden.id,
            producto_id=producto_id,
            cantidad_utilizada=cantidad,
            costo_unitario=producto.precio_compra
        )
        
        # Descontar del stock
        from app.models import MovimientoProducto
        producto.stock_actual -= cantidad
        
        movimiento = MovimientoProducto(
            producto_id=producto_id,
            tipo_movimiento='salida',
            cantidad=cantidad,
            stock_anterior=producto.stock_actual + cantidad,
            stock_actual=producto.stock_actual,
            motivo='servicio',
            referencia_tipo='orden_servicio',
            referencia_id=orden.id,
            costo_unitario=producto.precio_compra,
            usuario_id=current_user.id
        )
        
        db.session.add(detalle)
        db.session.add(movimiento)
        db.session.commit()
        
        flash('Insumo registrado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.ver_orden', id=id))

# ===== RECLAMOS =====
@bp.route('/reclamos')
@login_required
def reclamos():
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = Reclamo.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    reclamos_pagination = query.order_by(Reclamo.fecha_creacion.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    reclamos = reclamos_pagination.items
    return render_template('servicios/reclamos.html', reclamos=reclamos, reclamos_pagination=reclamos_pagination)

@bp.route('/reclamos/crear', methods=['GET', 'POST'])
@login_required
def crear_reclamo():
    if request.method == 'POST':
        try:
            ultimo = Reclamo.query.order_by(Reclamo.id.desc()).first()
            numero = f"REC-{(ultimo.id + 1 if ultimo else 1):06d}"
            factura_id = request.form.get('factura_id')
            factura = Venta.query.get(factura_id)
            reclamo = Reclamo(
                numero=numero,
                cliente_id=factura.cliente_id if factura else None,
                tipo_reclamo=request.form.get('tipo_reclamo'),
                descripcion=request.form.get('descripcion'),
                prioridad='media',
                estado='registrado',
                fecha_creacion=datetime.utcnow(),
                documento_tipo='factura',
                documento_numero=factura.numero_factura if factura else None,
                documento_id=factura.id if factura else None
            )
            db.session.add(reclamo)
            db.session.commit()
            flash('Reclamo registrado correctamente', 'success')
            return redirect(url_for('servicios.reclamos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    clientes = Cliente.query.filter_by(activo=True).all()
    from app.models import Usuario
    usuarios = Usuario.query.filter_by(activo=True).all()
    return render_template('servicios/crear_reclamo.html', clientes=clientes, usuarios=usuarios)

@bp.route('/tipos/buscar')
@login_required
def buscar_tipos():
    """Endpoint para búsqueda AJAX de tipos de servicio"""
    term = request.args.get('term', '')
    
    tipos = TipoServicio.query.filter(
        TipoServicio.activo == True,
        (TipoServicio.codigo.ilike(f'%{term}%')) |
        (TipoServicio.nombre.ilike(f'%{term}%')) |
        (TipoServicio.descripcion.ilike(f'%{term}%'))
    ).limit(10).all()
    
    resultados = [{
        'id': t.id,
        'label': f'{t.nombre} {t.descripcion or ""}',
        'value': t.nombre,
        'codigo': t.codigo,
        'nombre': t.nombre,
        'descripcion': t.descripcion or '',
        'precio_base': float(t.precio_base)
    } for t in tipos]
    
    return jsonify(resultados)

@bp.route('/reclamos/<int:id>')
@login_required
def ver_reclamo(id):
    reclamo = Reclamo.query.get_or_404(id)
    return render_template('servicios/ver_reclamo.html', reclamo=reclamo)

@bp.route('/reclamos/<int:id>/seguimiento', methods=['POST'])
@login_required
def agregar_seguimiento(id):
    reclamo = Reclamo.query.get_or_404(id)
    
    try:
        estado_anterior = reclamo.estado
        estado_nuevo = request.form.get('estado_nuevo', estado_anterior)
        
        seguimiento = ReclamoSeguimiento(
            reclamo_id=reclamo.id,
            usuario_id=current_user.id,
            descripcion=request.form.get('descripcion'),
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo
        )
        
        if estado_nuevo != estado_anterior:
            reclamo.estado = estado_nuevo
            
            if estado_nuevo == 'resuelto':
                reclamo.fecha_resolucion = datetime.utcnow()
                reclamo.solucion = request.form.get('descripcion')
        
        db.session.add(seguimiento)
        db.session.commit()
        
        flash('Seguimiento agregado correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('servicios.ver_reclamo', id=id))

@bp.route('/solicitudes/<int:id>/entregar', methods=['POST'])
@login_required
def entregar_solicitud(id):
    solicitud = SolicitudServicio.query.get_or_404(id)
    try:
        solicitud.estado = 'entregado'
        db.session.commit()
        registrar_bitacora('entregar-solicitud', f'Solicitud entregada: {solicitud.numero_solicitud} por usuario {current_user.username}')
        flash('Solicitud marcada como entregada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('servicios.ver_solicitud', id=id))
