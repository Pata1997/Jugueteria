from app import db
from datetime import datetime

class NotaDebitoDetalle(db.Model):
    __tablename__ = 'notas_debito_detalle'
    id = db.Column(db.Integer, primary_key=True)
    nota_debito_id = db.Column(db.Integer, db.ForeignKey('notas_debito.id'), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NotaDebitoDetalle {self.id}>'
