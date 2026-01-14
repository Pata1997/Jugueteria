from flask_login import current_user
from functools import wraps
from flask import abort

# Roles válidos en el sistema
ROLES = {
    'admin': 'Administrador',
    'recepcion': 'Recepcion',
    'caja': 'Caja',
    'tecnico': 'Tecnico',
}

def require_roles(*roles):
    """
    Decorador para restringir acceso según rol de usuario actual.
    Uso: @require_roles('admin', 'caja')
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.rol not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Ejemplo de uso en una ruta:
# from app.utils.roles import require_roles
# @bp.route('/ventas/')
# @login_required
# @require_roles('admin', 'caja')
# def ventas():
#     ...
