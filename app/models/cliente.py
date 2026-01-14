from datetime import datetime
from app import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(20), nullable=False)  # RUC, CI
    numero_documento = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo_cliente = db.Column(db.String(20), nullable=False)  # particular, empresa, gobierno
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    descuento_especial = db.Column(db.Numeric(5, 2), default=0)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    solicitudes = db.relationship('SolicitudServicio', backref='cliente', lazy='dynamic')
    ventas = db.relationship('Venta', backref='cliente', lazy='dynamic')
    
    def __repr__(self):
        return f'<Cliente {self.numero_documento} - {self.nombre}>'
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente del cliente"""
        from app.models.venta import Venta
        ventas_pendientes = Venta.query.filter_by(
            cliente_id=self.id,
            estado_pago='pendiente'
        ).all()
        return sum(v.saldo_pendiente for v in ventas_pendientes)
