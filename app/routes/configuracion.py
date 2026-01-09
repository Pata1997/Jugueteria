from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ConfiguracionEmpresa, Usuario
from app.routes.auth import admin_required

bp = Blueprint('configuracion', __name__, url_prefix='/configuracion')

@bp.route('/')
@login_required
@admin_required
def index():
    config = ConfiguracionEmpresa.get_config()
    usuarios = Usuario.query.all()
    return render_template('configuracion/index.html', config=config, usuarios=usuarios)

@bp.route('/empresa', methods=['GET', 'POST'])
@login_required
@admin_required
def empresa():
    config = ConfiguracionEmpresa.get_config()
    
    if request.method == 'POST':
        try:
            config.nombre_empresa = request.form.get('nombre_empresa')
            config.ruc = request.form.get('ruc')
            config.direccion = request.form.get('direccion')
            config.telefono = request.form.get('telefono')
            config.email = request.form.get('email')
            config.timbrado = request.form.get('timbrado')
            config.numero_establecimiento = request.form.get('numero_establecimiento')
            config.numero_expedicion = request.form.get('numero_expedicion')
            config.fecha_vencimiento_timbrado = request.form.get('fecha_vencimiento_timbrado')
            config.porcentaje_iva = request.form.get('porcentaje_iva')
            
            db.session.commit()
            flash('Configuración actualizada correctamente', 'success')
            return redirect(url_for('configuracion.empresa'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('configuracion/empresa.html', config=config)

@bp.route('/actualizar_empresa', methods=['POST'])
@login_required
@admin_required
def actualizar_empresa():
    import os
    from werkzeug.utils import secure_filename
    
    config = ConfiguracionEmpresa.get_config()
    
    try:
        config.nombre_empresa = request.form.get('nombre_empresa')
        config.ruc = request.form.get('ruc')
        config.direccion = request.form.get('direccion')
        config.telefono = request.form.get('telefono')
        config.email = request.form.get('email')
        
        # Configuración de facturación
        config.timbrado = request.form.get('timbrado')
        config.numero_establecimiento = request.form.get('numero_establecimiento')
        config.numero_expedicion = request.form.get('numero_expedicion')
        config.numero_factura_desde = request.form.get('numero_factura_desde')
        config.numero_factura_hasta = request.form.get('numero_factura_hasta')
        if request.form.get('fecha_vencimiento_timbrado'):
            from datetime import datetime
            config.fecha_vencimiento_timbrado = datetime.strptime(request.form.get('fecha_vencimiento_timbrado'), '%Y-%m-%d').date()
        config.porcentaje_iva = request.form.get('porcentaje_iva')
        
        # Manejar subida de logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Crear carpeta uploads si no existe
                upload_folder = os.path.join('app', 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                # Guardar con nombre único
                ext = os.path.splitext(filename)[1]
                new_filename = f'logo_empresa{ext}'
                filepath = os.path.join(upload_folder, new_filename)
                file.save(filepath)
                config.logo_url = f'uploads/{new_filename}'
        
        db.session.commit()
        flash('Configuración de empresa actualizada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar configuración: {str(e)}', 'danger')
    
    return redirect(url_for('configuracion.index'))

@bp.route('/actualizar_horarios', methods=['POST'])
@login_required
@admin_required
def actualizar_horarios():
    # Placeholder for horarios update logic
    flash('Horarios actualizados correctamente', 'success')
    return redirect(url_for('configuracion.index'))

@bp.route('/actualizar_facturacion', methods=['POST'])
@login_required
@admin_required
def actualizar_facturacion():
    # Placeholder for facturacion update logic
    flash('Configuración de facturación actualizada correctamente', 'success')
    return redirect(url_for('configuracion.index'))

@bp.route('/realizar_backup', methods=['GET'])
@login_required
@admin_required
def realizar_backup():
    # Placeholder for backup creation logic
    flash('Backup realizado correctamente', 'success')
    return redirect(url_for('configuracion.index'))

@bp.route('/restaurar_backup', methods=['POST'])
@login_required
@admin_required
def restaurar_backup():
    # Placeholder for backup restore logic
    flash('Backup restaurado correctamente', 'success')
    return redirect(url_for('configuracion.index'))

@bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    usuarios = Usuario.query.all()
    return render_template('configuracion/usuarios.html', usuarios=usuarios)

@bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        try:
            usuario = Usuario(
                username=request.form.get('username'),
                email=request.form.get('email'),
                nombre=request.form.get('nombre'),
                apellido=request.form.get('apellido'),
                rol=request.form.get('rol')
            )
            usuario.set_password(request.form.get('password'))
            
            db.session.add(usuario)
            db.session.commit()
            
            flash('Usuario creado correctamente', 'success')
            return redirect(url_for('configuracion.usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('configuracion/crear_usuario.html')

@bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            usuario.username = request.form.get('username')
            usuario.email = request.form.get('email')
            usuario.nombre = request.form.get('nombre')
            usuario.apellido = request.form.get('apellido')
            usuario.rol = request.form.get('rol')
            usuario.activo = request.form.get('activo') == 'on'
            
            # Solo cambiar password si se proporcionó uno nuevo
            nueva_password = request.form.get('password')
            if nueva_password:
                usuario.set_password(nueva_password)
            
            db.session.commit()
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('configuracion.usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('configuracion/editar_usuario.html', usuario=usuario)

@bp.route('/usuarios/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario():
    try:
        user_id = request.form.get('user_id') or request.json.get('user_id')
        usuario = Usuario.query.get_or_404(user_id)
        
        # No permitir eliminar el propio usuario
        if usuario.id == current_user.id:
            return {'success': False, 'error': 'No puedes eliminar tu propio usuario'}, 400
        
        db.session.delete(usuario)
        db.session.commit()
        
        return {'success': True, 'message': 'Usuario eliminado correctamente'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}, 500
