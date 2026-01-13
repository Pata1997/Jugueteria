from datetime import datetime
from app import db

class Bitacora(db.Model):
    __tablename__ = 'bitacora'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    accion = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(50))

    usuario = db.relationship('Usuario')  # Using string reference to avoid circular dependency

    def __repr__(self):
        return f'<Bitacora {self.usuario_id} {self.accion} {self.fecha}>'
