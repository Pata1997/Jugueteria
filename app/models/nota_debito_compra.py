from app import db
from datetime import datetime

class NotaDebitoCompra(db.Model):
    __tablename__ = 'notas_debito_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    # Número emitido por el proveedor
    numero_nota_proveedor = db.Column(db.String(50), nullable=False, index=True)
    # Fecha emitida por el proveedor
    fecha_nota_proveedor = db.Column(db.DateTime, nullable=False)
    # Fecha de registro en nuestro sistema
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    
    tipo = db.Column(db.String(20), nullable=False)  # 'flete', 'interes', 'recargo', 'otro'
    motivo = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    
    estado = db.Column(db.String(20), default='activa')  # activa, anulada
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    compra = db.relationship('Compra', backref='notas_debito')
    proveedor = db.relationship('Proveedor', backref='notas_debito_compra')
    usuario = db.relationship('Usuario', backref='notas_debito_compra')
    detalles = db.relationship('NotaDebitoCompraDetalle', backref='nota_debito', lazy='select', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<NotaDebitoCompra {self.numero_nota_proveedor}>'

class NotaDebitoCompraDetalle(db.Model):
    __tablename__ = 'nota_debito_compra_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    nota_debito_id = db.Column(db.Integer, db.ForeignKey('notas_debito_compra.id'), nullable=False)
    concepto = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    
    def __repr__(self):
        return f'<NotaDebitoCompraDetalle {self.concepto}>'
