from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils.roles import require_roles
from app import db
from app.models import Proveedor
from app.routes.compras import bp

@bp.route('/proveedores/crear', methods=['GET', 'POST'])
@login_required
@require_roles('admin', 'caja')
def crear_proveedor():
    if request.method == 'POST':
        razon_social = request.form.get('razon_social')
        ruc = request.form.get('ruc')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        contacto_nombre = request.form.get('contacto_nombre')
        contacto_telefono = request.form.get('contacto_telefono')
        tipo_proveedor = request.form.get('tipo_proveedor')
        observaciones = request.form.get('observaciones')
        proveedor = Proveedor(
            razon_social=razon_social,
            ruc=ruc,
            telefono=telefono,
            email=email,
            contacto_nombre=contacto_nombre,
            contacto_telefono=contacto_telefono,
            tipo_proveedor=tipo_proveedor,
            observaciones=observaciones,
            activo=True
        )
        db.session.add(proveedor)
        db.session.commit()
        flash('Proveedor creado correctamente', 'success')
        return redirect(url_for('compras.proveedores'))
    return render_template('compras/crear_proveedor.html')

@bp.route('/proveedores/<int:id>')
@login_required
@require_roles('admin', 'caja')
def ver_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    return render_template('compras/ver_proveedor.html', proveedor=proveedor)

@bp.route('/proveedores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_roles('admin', 'caja')
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    if request.method == 'POST':
        proveedor.razon_social = request.form.get('razon_social')
        proveedor.ruc = request.form.get('ruc')
        proveedor.telefono = request.form.get('telefono')
        proveedor.email = request.form.get('email')
        proveedor.contacto_nombre = request.form.get('contacto_nombre')
        proveedor.contacto_telefono = request.form.get('contacto_telefono')
        proveedor.tipo_proveedor = request.form.get('tipo_proveedor')
        proveedor.observaciones = request.form.get('observaciones')
        proveedor.activo = request.form.get('activo') == '1'
        db.session.commit()
        flash('Proveedor actualizado correctamente', 'success')
        return redirect(url_for('compras.proveedores'))
    return render_template('compras/editar_proveedor.html', proveedor=proveedor)
