from app import db
from datetime import datetime

class NotaCreditoDetalle(db.Model):
    __tablename__ = 'notas_credito_detalle'
    id = db.Column(db.Integer, primary_key=True)
    nota_credito_id = db.Column(db.Integer, db.ForeignKey('notas_credito.id'), nullable=False)
    venta_detalle_id = db.Column(db.Integer, db.ForeignKey('venta_detalles.id'), nullable=False)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NotaCreditoDetalle {self.id}>'
