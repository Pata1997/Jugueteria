from app import db
from datetime import datetime

class NotaDebitoDetalle(db.Model):
    __tablename__ = 'notas_debito_detalle'
    id = db.Column(db.Integer, primary_key=True)
    nota_debito_id = db.Column(db.Integer, db.ForeignKey('notas_debito.id'), nullable=False)
    
    # Para DEVOLUCIONES: referencia a artículo de venta original
    venta_detalle_id = db.Column(db.Integer, db.ForeignKey('venta_detalles.id'), nullable=True)
    
    # Para CARGOS: descripción genérica
    descripcion = db.Column(db.String(255), nullable=True)
    
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con venta_detalle para devoluciones
    venta_detalle = db.relationship('VentaDetalle', backref='notas_debito_detalles')

    def __repr__(self):
        return f'<NotaDebitoDetalle {self.id}>'
