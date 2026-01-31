from app import db
from datetime import datetime

class NotaCredito(db.Model):
    __tablename__ = 'notas_credito'
    id = db.Column(db.Integer, primary_key=True)
    # ...otros campos...
    detalles = db.relationship('NotaCreditoDetalle', backref='nota_credito', lazy='select')
