from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.bitacora import Bitacora
from app.models.usuario import Usuario

print('Bitacora blueprint loaded')

bp = Blueprint('bitacora', __name__, url_prefix='/bitacora')

@bp.route('/')
@login_required
def ver_bitacora():
    if not hasattr(current_user, 'rol') or current_user.rol != 'admin':
        return render_template('errors/404.html'), 404
    registros = Bitacora.query.order_by(Bitacora.fecha.desc()).limit(500).all()
    return render_template('bitacora/listar.html', registros=registros)
