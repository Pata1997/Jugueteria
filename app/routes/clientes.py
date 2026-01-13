from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Cliente
from datetime import datetime
from app.utils import registrar_bitacora

bp = Blueprint('clientes', __name__, url_prefix='/clientes')

@bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Cliente.query
    
    if search:
        query = query.filter(
            (Cliente.nombre.ilike(f'%{search}%')) |
            (Cliente.numero_documento.ilike(f'%{search}%'))
        )
    
    clientes = query.order_by(Cliente.fecha_registro.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('clientes/listar.html', clientes=clientes, search=search)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            cliente = Cliente(
                tipo_documento=request.form.get('tipo_documento'),
                numero_documento=request.form.get('numero_documento'),
                nombre=request.form.get('nombre'),
                tipo_cliente=request.form.get('tipo_cliente'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                email=request.form.get('email'),
                limite_credito=request.form.get('limite_credito', 0),
                descuento_especial=request.form.get('descuento_especial', 0),
                observaciones=request.form.get('observaciones')
            )
            db.session.add(cliente)
            db.session.commit()
            registrar_bitacora('crear-cliente', f'Cliente creado: {cliente.nombre} ({cliente.numero_documento})')
            flash('Cliente creado correctamente', 'success')
            return redirect(url_for('clientes.ver', id=cliente.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear cliente: {str(e)}', 'danger')
    return render_template('clientes/crear.html')

@bp.route('/<int:id>')
@login_required
def ver(id):
    from app.models.venta import Venta
    from app.models.servicio import SolicitudServicio
    cliente = Cliente.query.get_or_404(id)
    # Mostrar todas las ventas recientes, incluyendo anuladas/rechazadas
    ventas_recientes = Venta.query.filter_by(cliente_id=id).order_by(Venta.fecha_venta.desc()).limit(10).all()
    # Contador total de ventas (todas)
    total_ventas = Venta.query.filter_by(cliente_id=id).count()
    # Contador total de servicios (todas)
    total_servicios = SolicitudServicio.query.filter_by(cliente_id=id).count()
    # Reclamos
    total_reclamos = cliente.reclamos.count()
    return render_template('clientes/ver.html', cliente=cliente, ventas_recientes=ventas_recientes, total_ventas=total_ventas, total_servicios=total_servicios, total_reclamos=total_reclamos)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        try:
            cliente.tipo_documento = request.form.get('tipo_documento')
            cliente.numero_documento = request.form.get('numero_documento')
            cliente.nombre = request.form.get('nombre')
            cliente.tipo_cliente = request.form.get('tipo_cliente')
            cliente.direccion = request.form.get('direccion')
            cliente.telefono = request.form.get('telefono')
            cliente.email = request.form.get('email')
            cliente.limite_credito = request.form.get('limite_credito', 0)
            cliente.descuento_especial = request.form.get('descuento_especial', 0)
            cliente.observaciones = request.form.get('observaciones')
            cliente.activo = request.form.get('activo') == 'on'
            db.session.commit()
            registrar_bitacora('editar-cliente', f'Cliente editado: {cliente.nombre} ({cliente.numero_documento})')
            flash('Cliente actualizado correctamente', 'success')
            return redirect(url_for('clientes.ver', id=cliente.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar cliente: {str(e)}', 'danger')
    return render_template('clientes/editar.html', cliente=cliente)

@bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        cliente.activo = False
        db.session.commit()
        registrar_bitacora('eliminar-cliente', f'Cliente eliminado: {cliente.nombre} ({cliente.numero_documento})')
        flash('Cliente desactivado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar cliente: {str(e)}', 'danger')
    return redirect(url_for('clientes.listar'))

@bp.route('/buscar')
@login_required
def buscar():
    """Endpoint para búsqueda AJAX"""
    term = request.args.get('term', '')
    
    clientes = Cliente.query.filter(
        Cliente.activo == True,
        (Cliente.nombre.ilike(f'%{term}%')) |
        (Cliente.numero_documento.ilike(f'%{term}%'))
    ).limit(10).all()
    
    resultados = [{
        'id': c.id,
        'label': f'{c.numero_documento} - {c.nombre}',
        'value': c.nombre,
        'numero_documento': c.numero_documento,
        'direccion': c.direccion,
        'telefono': c.telefono,
        'limite_credito': float(c.limite_credito),
        'descuento_especial': float(c.descuento_especial)
    } for c in clientes]
    
    return jsonify(resultados)
