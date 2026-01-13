from datetime import datetime
from app import db

class Reclamo(db.Model):
    __tablename__ = 'reclamos'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    documento_tipo = db.Column(db.String(20))  # factura | servicio | ticket
    documento_numero = db.Column(db.String(50))
    documento_id = db.Column(db.Integer, nullable=True)
    tipo_reclamo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    prioridad = db.Column(db.String(10), default='media')
    estado = db.Column(db.String(20), default='registrado')
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    resolucion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_estimada_resolucion = db.Column(db.DateTime, nullable=True)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    cliente = db.relationship('Cliente')
    responsable = db.relationship('Usuario')
    historial = db.relationship('ReclamoHistorial', backref='reclamo', lazy='dynamic')

class ReclamoHistorial(db.Model):
    __tablename__ = 'reclamo_historial'
    id = db.Column(db.Integer, primary_key=True)
    reclamo_id = db.Column(db.Integer, db.ForeignKey('reclamos.id'))
    estado_anterior = db.Column(db.String(20))
    estado_nuevo = db.Column(db.String(20))
    comentario = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
