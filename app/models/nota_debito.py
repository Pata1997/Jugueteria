from app import db
from datetime import datetime

class NotaDebito(db.Model):
    __tablename__ = 'notas_debito'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_nota = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    
    # TIPO DE NOTA DE DÉBITO
    tipo = db.Column(db.String(20), nullable=False)  # 'cargo' o 'devolución_producto'
    motivo = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    
    # ESTADO (columna antigua, se mantiene por compatibilidad)
    estado = db.Column(db.String(20))  # Obsoleta, usar estado_emision
    
    # ESTADO (nuevas columnas)
    estado_emision = db.Column(db.String(20), default='activa')  # activa, anulada
    estado_pago = db.Column(db.String(20), default='pendiente')  # pendiente, parcialmente_pagado, pagado
    
    # AUDITORÍA
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # RELACIONES
    venta = db.relationship('Venta', backref='notas_debito')
    usuario = db.relationship('Usuario', backref='notas_debito')
    detalles = db.relationship('NotaDebitoDetalle', backref='nota_debito', lazy='select', cascade='all, delete-orphan')
    pagos = db.relationship('PagoNotaDebito', backref='nota_debito', lazy='select', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<NotaDebito {self.numero_nota}>'
    
    @property
    def monto_pagado(self):
        """Calcula total pagado"""
        from app.models.pago_nota_debito import PagoNotaDebito
        total = db.session.query(db.func.sum(PagoNotaDebito.monto)).filter_by(nota_debito_id=self.id).scalar() or 0
        return float(total)
    
    @property
    def monto_pendiente(self):
        """Calcula monto aún pendiente"""
        return float(self.monto) - self.monto_pagado
    
    def actualizar_estado_pago(self):
        """Actualiza automáticamente el estado de pago"""
        if self.monto_pagado == 0:
            self.estado_pago = 'pendiente'
        elif self.monto_pagado >= float(self.monto):
            self.estado_pago = 'pagado'
        else:
            self.estado_pago = 'parcialmente_pagado'