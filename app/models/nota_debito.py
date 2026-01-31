from app import db
from datetime import datetime

class NotaDebito(db.Model):
    __tablename__ = 'notas_debito'
    id = db.Column(db.Integer, primary_key=True)
    # ...otros campos...
    detalles = db.relationship('NotaDebitoDetalle', backref='nota_debito', lazy='select')