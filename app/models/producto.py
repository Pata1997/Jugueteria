from datetime import datetime
from app import db

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    
    productos = db.relationship('Producto', backref='categoria', lazy='dynamic')
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    tipo_producto = db.Column(db.String(20), nullable=False)  # producto, insumo
    unidad_medida = db.Column(db.String(20))  # unidad, metro, kg, etc
    precio_compra = db.Column(db.Numeric(12, 2), default=0)
    precio_venta = db.Column(db.Numeric(12, 2), default=0)
    tipo_iva = db.Column(db.String(10), default='10')  # '10', '5', 'exenta'
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    stock_maximo = db.Column(db.Integer, default=0)
    es_importado = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    imagen_url = db.Column(db.String(255))
    
    # Relaciones
    movimientos = db.relationship('MovimientoProducto', backref='producto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Producto {self.codigo} - {self.nombre}>'
    
    @property
    def necesita_reposicion(self):
        return self.stock_actual <= self.stock_minimo
    
    @staticmethod
    def generar_proximo_codigo():
        """Genera el siguiente código de producto con formato 001, 002, 003, etc"""
        ultimo_producto = Producto.query.order_by(Producto.id.desc()).first()
        
        if not ultimo_producto or not ultimo_producto.codigo:
            return '001'
        
        try:
            # Extraer número del último código
            ultimo_numero = int(ultimo_producto.codigo)
            nuevo_numero = ultimo_numero + 1
            # Formatear con ceros a la izquierda
            return str(nuevo_numero).zfill(3)
        except (ValueError, AttributeError):
            # Si no se puede parsear, empezar desde 001
            return '001'

class MovimientoProducto(db.Model):
    __tablename__ = 'movimientos_producto'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo_movimiento = db.Column(db.String(20), nullable=False)  # entrada, salida, ajuste
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_actual = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(50))  # compra, venta, servicio, ajuste, devolucion
    referencia_tipo = db.Column(db.String(50))  # orden_servicio, venta, compra
    referencia_id = db.Column(db.Integer)
    costo_unitario = db.Column(db.Numeric(12, 2))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref='movimientos_producto')
    
    def __repr__(self):
        return f'<MovimientoProducto {self.tipo_movimiento} - {self.cantidad}>'

class HistorialPrecio(db.Model):
    __tablename__ = 'historial_precios'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    precio_compra_anterior = db.Column(db.Numeric(12, 2))
    precio_compra_nuevo = db.Column(db.Numeric(12, 2))
    precio_venta_anterior = db.Column(db.Numeric(12, 2))
    precio_venta_nuevo = db.Column(db.Numeric(12, 2))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))
    
    producto = db.relationship('Producto', backref='historial_precios')
    usuario = db.relationship('Usuario', backref='cambios_precio')
    
    def __repr__(self):
        return f'<HistorialPrecio Producto {self.producto_id}>'
