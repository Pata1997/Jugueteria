from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.roles import require_roles
from app import db
from app.models.reclamo import Reclamo, ReclamoHistorial
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.venta import Venta
from app.models.servicio import SolicitudServicio
from datetime import datetime

bp = Blueprint('reclamos', __name__, url_prefix='/servicios/reclamos')

# Utilidad para generar número de reclamo

def generar_numero_reclamo():
    ultimo = Reclamo.query.order_by(Reclamo.id.desc()).first()
    nro = f"REC-{(ultimo.id + 1 if ultimo else 1):06d}"
    return nro

@bp.route('/')
@login_required
@require_roles('admin', 'tecnico', 'recepcion')
def listar():
    reclamos = Reclamo.query.order_by(Reclamo.fecha_creacion.desc()).all()
    return render_template('reclamos/listar.html', reclamos=reclamos)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        numero = generar_numero_reclamo()
        cliente_id = request.form.get('cliente_id') or None
        documento_tipo = request.form.get('documento_tipo')
        documento_numero = request.form.get('documento_numero')
        documento_id = request.form.get('documento_id') or None
        tipo_reclamo = request.form.get('tipo_reclamo')
        descripcion = request.form.get('descripcion')
        prioridad = request.form.get('prioridad', 'media')
        fecha_estimada_resolucion = request.form.get('fecha_estimada_resolucion') or None
        reclamo = Reclamo(
            numero=numero,
            cliente_id=cliente_id,
            documento_tipo=documento_tipo,
            documento_numero=documento_numero,
            documento_id=documento_id,
            tipo_reclamo=tipo_reclamo,
            descripcion=descripcion,
            prioridad=prioridad,
            estado='registrado',
            fecha_estimada_resolucion=fecha_estimada_resolucion
        )
        db.session.add(reclamo)
        db.session.commit()
        # Historial inicial
        historial = ReclamoHistorial(
            reclamo_id=reclamo.id,
            estado_anterior=None,
            estado_nuevo='registrado',
            comentario='Reclamo creado',
            usuario_id=current_user.id
        )
        db.session.add(historial)
        db.session.commit()
        flash('Reclamo registrado correctamente', 'success')
        return redirect(url_for('reclamos.ver', id=reclamo.id))
    clientes = Cliente.query.filter_by(activo=True).all()
    return render_template('reclamos/crear.html', clientes=clientes)

@bp.route('/<int:id>')
@login_required
def ver(id):
    reclamo = Reclamo.query.get_or_404(id)
    return render_template('reclamos/ver.html', reclamo=reclamo)

@bp.route('/<int:id>/cambiar_estado', methods=['POST'])
@login_required
def cambiar_estado(id):
    reclamo = Reclamo.query.get_or_404(id)
    estado_nuevo = request.form.get('estado_nuevo')
    comentario = request.form.get('comentario', '')
    if reclamo.estado == 'cerrado':
        flash('No se puede modificar un reclamo cerrado.', 'danger')
        return redirect(url_for('reclamos.ver', id=id))
    estado_anterior = reclamo.estado
    reclamo.estado = estado_nuevo
    if estado_nuevo in ['resuelto', 'cerrado']:
        resolucion = request.form.get('resolucion', '').strip()
        if not resolucion:
            flash('Debe ingresar la resolución para cerrar o resolver el reclamo.', 'danger')
            return redirect(url_for('reclamos.ver', id=id))
        reclamo.resolucion = resolucion
        if estado_nuevo == 'cerrado':
            reclamo.fecha_cierre = datetime.utcnow()
    reclamo.responsable_id = current_user.id
    db.session.commit()
    historial = ReclamoHistorial(
        reclamo_id=reclamo.id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=comentario,
        usuario_id=current_user.id
    )
    db.session.add(historial)
    db.session.commit()
    flash('Estado actualizado correctamente', 'success')
    return redirect(url_for('reclamos.ver', id=id))

@bp.route('/buscar_documento')
@login_required
def buscar_documento():
    term = request.args.get('term', '').strip()
    resultados = []
    # Buscar en facturas
    facturas = Venta.query.filter(Venta.numero_factura.ilike(f'%{term}%')).limit(10).all()
    for f in facturas:
        resultados.append({
            'id': f.id,
            'numero': f.numero_factura,
            'tipo': 'factura',
            'cliente_id': f.cliente_id,
            'cliente_nombre': f.cliente.nombre if f.cliente else ''
        })
    # Buscar en servicios
    servicios = SolicitudServicio.query.filter(SolicitudServicio.numero_solicitud.ilike(f'%{term}%')).limit(10).all()
    for s in servicios:
        resultados.append({
            'id': s.id,
            'numero': s.numero_solicitud,
            'tipo': 'servicio',
            'cliente_id': s.cliente_id,
            'cliente_nombre': s.cliente.nombre if s.cliente else ''
        })
    return jsonify(resultados)
