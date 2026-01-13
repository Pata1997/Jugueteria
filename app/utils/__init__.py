# Utilidad para registrar en bitácora
from flask import request
from flask_login import current_user
from app import db
from app.models.bitacora import Bitacora

def registrar_bitacora(accion, descripcion=None):
	try:
		usuario_id = current_user.id if hasattr(current_user, 'id') else None
		ip = request.remote_addr if request else None
		bitacora = Bitacora(
			usuario_id=usuario_id,
			accion=accion,
			descripcion=descripcion,
			ip=ip
		)
		print(f"Registrando en bitácora: usuario_id={usuario_id}, accion={accion}, descripcion={descripcion}, ip={ip}")
		db.session.add(bitacora)
		db.session.commit()
		print("Registro de bitácora guardado correctamente.")
	except Exception as e:
		print(f"Error al registrar en bitácora: {e}")
		db.session.rollback()
"""
Utilidades del sistema
"""
from .ticket import GeneradorTicket

__all__ = ['GeneradorTicket']
