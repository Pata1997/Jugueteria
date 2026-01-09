from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.usuario import Usuario
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('No tiene permisos para acceder a esta página', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    from app.models.configuracion import ConfiguracionEmpresa
    config = ConfiguracionEmpresa.get_config()
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Su cuenta ha sido desactivada. Contacte al administrador.', 'danger')
                return render_template('auth/login.html')
            
            login_user(usuario, remember=remember)
            
            from datetime import datetime
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html', config=config)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/perfil')
@login_required
def perfil():
    return render_template('auth/perfil.html')

@bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')
        
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta', 'danger')
        elif password_nueva != password_confirmar:
            flash('Las contraseñas nuevas no coinciden', 'danger')
        elif len(password_nueva) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
        else:
            current_user.set_password(password_nueva)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')
            return redirect(url_for('auth.perfil'))
    
    return render_template('auth/cambiar_password.html')
