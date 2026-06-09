from app import db
from datetime import datetime

class NotaCreditoCompra(db.Model):
    __tablename__ = 'notas_credito_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    # Número emitido por el proveedor
    numero_nota_proveedor = db.Column(db.String(50), nullable=False, index=True)
    # Fecha emitida por el proveedor
    fecha_nota_proveedor = db.Column(db.DateTime, nullable=False)
    # Fecha de registro en nuestro sistema
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    estado = db.Column(db.String(20), default='activa')  # activa, anulada
    observaciones = db.Column(db.Text)
    
    compra = db.relationship('Compra', backref='notas_credito')
    proveedor = db.relationship('Proveedor', backref='notas_credito_compra')
    usuario = db.relationship('Usuario', backref='notas_credito_compra')
    detalles = db.relationship('NotaCreditoCompraDetalle', backref='nota_credito', lazy='select', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<NotaCreditoCompra {self.numero_nota_proveedor}>'

class NotaCreditoCompraDetalle(db.Model):
    __tablename__ = 'nota_credito_compra_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    nota_credito_id = db.Column(db.Integer, db.ForeignKey('notas_credito_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=True)
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<NotaCreditoCompraDetalle {self.descripcion}>'
