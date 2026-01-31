from app import db
from datetime import datetime

class PagoNotaDebito(db.Model):
    __tablename__ = 'pagos_nota_debito'
    id = db.Column(db.Integer, primary_key=True)
    nota_debito_id = db.Column(db.Integer, db.ForeignKey('notas_debito.id'), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    forma_pago_id = db.Column(db.Integer, db.ForeignKey('formas_pago.id'), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    referencia = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='confirmado')
    observaciones = db.Column(db.Text)

    forma_pago = db.relationship('FormaPago')

    def __repr__(self):
        return f'<PagoNotaDebito {self.id}>'
