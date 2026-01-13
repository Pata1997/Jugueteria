from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Categoria, MovimientoProducto, HistorialPrecio
from app.utils import registrar_bitacora
from datetime import datetime

bp = Blueprint('productos', __name__, url_prefix='/productos')

# ===== CATEGORÍAS =====
@bp.route('/categorias')
@login_required
def categorias():
    categorias = Categoria.query.filter_by(activo=True).all()
    return render_template('productos/categorias.html', categorias=categorias)

@bp.route('/categorias/crear', methods=['POST'])
@login_required
def crear_categoria():
    try:
        categoria = Categoria(
            codigo=request.form.get('codigo'),
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion')
        )
        db.session.add(categoria)
        db.session.commit()
        flash('Categoría creada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear categoría: {str(e)}', 'danger')
    
    return redirect(url_for('productos.categorias'))

# ===== PRODUCTOS =====
@bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    categoria_id = request.args.get('categoria_id', type=int)
    tipo = request.args.get('tipo', '')
    
    query = Producto.query
    
    if search:
        query = query.filter(
            (Producto.nombre.ilike(f'%{search}%')) |
            (Producto.codigo.ilike(f'%{search}%'))
        )
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    if tipo:
        query = query.filter_by(tipo_producto=tipo)
    
    productos = query.order_by(Producto.nombre).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categorias = Categoria.query.filter_by(activo=True).all()
    
    return render_template('productos/listar.html', 
                         productos=productos, 
                         categorias=categorias,
                         search=search)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            codigo = Producto.generar_proximo_codigo()
            producto = Producto(
                codigo=codigo,
                nombre=request.form.get('nombre'),
                descripcion=request.form.get('descripcion'),
                categoria_id=request.form.get('categoria_id'),
                tipo_producto=request.form.get('tipo_producto'),
                unidad_medida=request.form.get('unidad_medida'),
                precio_compra=request.form.get('precio_compra', 0),
                precio_venta=request.form.get('precio_venta', 0),
                stock_actual=request.form.get('stock_actual', 0),
                stock_minimo=request.form.get('stock_minimo', 0),
                stock_maximo=request.form.get('stock_maximo', 0),
                tipo_iva=request.form.get('tipo_iva', 'exenta'),
                es_importado=request.form.get('es_importado') == 'on'
            )
            db.session.add(producto)
            db.session.commit()
            registrar_bitacora('crear-producto', f'Producto creado: {producto.nombre} ({producto.codigo})')
            flash('Producto creado correctamente', 'success')
            return redirect(url_for('productos.ver', id=producto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'danger')
    categorias = Categoria.query.filter_by(activo=True).all()
    proximo_codigo = Producto.generar_proximo_codigo()
    return render_template('productos/crear.html', categorias=categorias, proximo_codigo=proximo_codigo)

@bp.route('/<int:id>')
@login_required
def ver(id):
    producto = Producto.query.get_or_404(id)
    movimientos = producto.movimientos.order_by(MovimientoProducto.fecha.desc()).limit(20).all()
    return render_template('productos/ver.html', producto=producto, movimientos=movimientos)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        try:
            precio_compra_nuevo = float(request.form.get('precio_compra', 0))
            precio_venta_nuevo = float(request.form.get('precio_venta', 0))
            if precio_compra_nuevo != float(producto.precio_compra) or \
               precio_venta_nuevo != float(producto.precio_venta):
                historial = HistorialPrecio(
                    producto_id=producto.id,
                    precio_compra_anterior=producto.precio_compra,
                    precio_compra_nuevo=precio_compra_nuevo,
                    precio_venta_anterior=producto.precio_venta,
                    precio_venta_nuevo=precio_venta_nuevo,
                    usuario_id=current_user.id,
                    motivo=request.form.get('motivo_cambio_precio', 'Actualización manual')
                )
                db.session.add(historial)
            producto.codigo = request.form.get('codigo')
            producto.nombre = request.form.get('nombre')
            producto.descripcion = request.form.get('descripcion')
            producto.categoria_id = request.form.get('categoria_id')
            producto.tipo_producto = request.form.get('tipo_producto')
            producto.unidad_medida = request.form.get('unidad_medida')
            producto.precio_compra = precio_compra_nuevo
            producto.precio_venta = precio_venta_nuevo
            producto.stock_minimo = request.form.get('stock_minimo', 0)
            producto.stock_maximo = request.form.get('stock_maximo', 0)
            producto.tipo_iva = request.form.get('tipo_iva', 'exenta')
            producto.es_importado = request.form.get('es_importado') == 'on'
            producto.activo = request.form.get('activo') == 'on'
            db.session.commit()
            registrar_bitacora('editar-producto', f'Producto editado: {producto.nombre} ({producto.codigo})')
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('productos.ver', id=producto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
    categorias = Categoria.query.filter_by(activo=True).all()
    return render_template('productos/editar.html', producto=producto, categorias=categorias)

@bp.route('/<int:id>/ajustar-stock', methods=['POST'])
@login_required
def ajustar_stock(id):
    producto = Producto.query.get_or_404(id)
    try:
        tipo_ajuste = request.form.get('tipo_ajuste')
        cantidad = int(request.form.get('cantidad'))
        observaciones = request.form.get('observaciones')
        stock_anterior = producto.stock_actual
        if tipo_ajuste == 'entrada':
            producto.stock_actual += cantidad
        else:
            producto.stock_actual -= cantidad
        movimiento = MovimientoProducto(
            producto_id=producto.id,
            tipo_movimiento=tipo_ajuste,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_actual=producto.stock_actual,
            motivo='ajuste',
            usuario_id=current_user.id,
            observaciones=observaciones
        )
        db.session.add(movimiento)
        db.session.commit()
        registrar_bitacora('ajustar-stock', f'Stock ajustado: {producto.nombre} ({producto.codigo}), tipo: {tipo_ajuste}, cantidad: {cantidad}')
        flash('Stock ajustado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al ajustar stock: {str(e)}', 'danger')
    return redirect(url_for('productos.ver', id=id))

@bp.route('/stock-bajo')
@login_required
def stock_bajo():
    productos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).all()
    
    return render_template('productos/stock_bajo.html', productos=productos)

@bp.route('/buscar')
@login_required
def buscar():
    """Endpoint para búsqueda AJAX"""
    term = request.args.get('term', '')
    tipo = request.args.get('tipo', '')
    
    query = Producto.query.filter(
        Producto.activo == True,
        (Producto.nombre.ilike(f'%{term}%')) |
        (Producto.codigo.ilike(f'%{term}%'))
    )
    
    if tipo:
        query = query.filter_by(tipo_producto=tipo)
    
    productos = query.limit(10).all()
    
    resultados = [{
        'id': p.id,
        'label': f'{p.codigo} - {p.nombre}',
        'value': p.nombre,
        'codigo': p.codigo,
        'precio_venta': float(p.precio_venta),
        'precio_compra': float(p.precio_compra),
        'tipo_iva': p.tipo_iva,
        'stock_actual': p.stock_actual,
        'unidad_medida': p.unidad_medida
    } for p in productos]
    
    return jsonify(resultados)


@bp.route('/api/productos')
@login_required
def api_productos():
    """API endpoint para obtener todos los productos activos"""
    productos = Producto.query.filter_by(activo=True).all()
    
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'precio_compra': float(p.precio_compra or 0),
        'precio_venta': float(p.precio_venta or 0),
        'stock_actual': float(p.stock_actual or 0),
        'unidad_medida': p.unidad_medida or 'und'
    } for p in productos])

