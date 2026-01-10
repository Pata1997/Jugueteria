from datetime import datetime
from app import db

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    razon_social = db.Column(db.String(200), nullable=False)
    ruc = db.Column(db.String(50), unique=True, nullable=False, index=True)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    contacto_nombre = db.Column(db.String(100))
    contacto_telefono = db.Column(db.String(50))
    tipo_proveedor = db.Column(db.String(50))  # nacional, internacional
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    pedidos = db.relationship('PedidoCompra', backref='proveedor', lazy='dynamic')
    compras = db.relationship('Compra', backref='proveedor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Proveedor {self.razon_social}>'

# ===== MODELOS ANTERIORES (MANTIENEN COMPATIBILIDAD) =====

class PedidoCompra(db.Model):
    __tablename__ = 'pedidos_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, presupuestado, aprobado, completado, cancelado
    fecha_entrega_estimada = db.Column(db.Date)
    usuario_solicita_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    usuario_solicita = db.relationship('Usuario', backref='pedidos_compra')
    detalles = db.relationship('PedidoCompraDetalle', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')
    presupuestos = db.relationship('PresupuestoProveedor', backref='pedido', lazy='dynamic')
    
    def __repr__(self):
        return f'<PedidoCompra {self.numero_pedido}>'

class PedidoCompraDetalle(db.Model):
    __tablename__ = 'pedido_compra_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_solicitada = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_recibida = db.Column(db.Numeric(10, 2), default=0)
    observaciones = db.Column(db.String(255))
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<PedidoCompraDetalle Pedido {self.pedido_id}>'

class PresupuestoProveedor(db.Model):
    __tablename__ = 'presupuestos_proveedor'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_presupuesto = db.Column(db.String(50), unique=True, nullable=False)
    fecha_recepcion = db.Column(db.DateTime, default=datetime.utcnow)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos_compra.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    dias_entrega = db.Column(db.Integer)
    condiciones_pago = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, seleccionado, rechazado
    fecha_validez = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    
    proveedor = db.relationship('Proveedor')
    detalles = db.relationship('PresupuestoProveedorDetalle', backref='presupuesto', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PresupuestoProveedor {self.numero_presupuesto}>'

class PresupuestoProveedorDetalle(db.Model):
    __tablename__ = 'presupuesto_proveedor_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey('presupuestos_proveedor.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<PresupuestoProveedorDetalle {self.producto_id}>'

class OrdenCompra(db.Model):
    __tablename__ = 'ordenes_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_orden = db.Column(db.DateTime, default=datetime.utcnow)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos_compra.id'))
    presupuesto_proveedor_id = db.Column(db.Integer, db.ForeignKey('presupuestos_proveedor.id'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, parcial, completada, cancelada
    fecha_entrega_estimada = db.Column(db.Date)
    usuario_autoriza_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    pedido = db.relationship('PedidoCompra', backref='ordenes')
    presupuesto_proveedor = db.relationship('PresupuestoProveedor', backref='ordenes')
    proveedor = db.relationship('Proveedor')
    usuario_autoriza = db.relationship('Usuario', backref='ordenes_autorizadas')
    detalles = db.relationship('OrdenCompraDetalle', backref='orden', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OrdenCompra {self.numero_orden}>'

class OrdenCompraDetalle(db.Model):
    __tablename__ = 'orden_compra_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_ordenada = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_recibida = db.Column(db.Numeric(10, 2), default=0)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<OrdenCompraDetalle Orden {self.orden_id}>'

class Compra(db.Model):
    __tablename__ = 'compras'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_compra = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # QUÉ registras
    tipo = db.Column(db.String(20), default='producto')  # producto, servicio, factura, gasto
    descripcion = db.Column(db.String(255), nullable=True)
    fecha_documento = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    fecha_compra = db.Column(db.DateTime, default=datetime.utcnow)
    
    # RELACIONES
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    usuario_registra_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # CÁLCULO
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    
    # ESTADO
    estado = db.Column(db.String(20), default='registrada')  # registrada, pagada, parcial_pagada
    stock_actualizado = db.Column(db.Boolean, default=False)
    
    # CRÉDITO (opcional cuando la compra se deja a crédito)
    plazo_credito_dias = db.Column(db.Integer, nullable=True)
    fecha_vencimiento_credito = db.Column(db.Date, nullable=True)
    observaciones_credito = db.Column(db.Text, nullable=True)
    
    # AUDITORÍA
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    # Campos legacy para compatibilidad
    numero_factura = db.Column(db.String(50), nullable=True)
    fecha_factura = db.Column(db.Date, nullable=True)
    orden_compra_id = db.Column(db.Integer, db.ForeignKey('ordenes_compra.id'), nullable=True)
    usuario_recibe_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # RELACIONES
    detalles = db.relationship('CompraDetalle', backref='compra', lazy='dynamic', cascade='all, delete-orphan')
    pagos = db.relationship('PagoCompra', backref='compra', lazy='dynamic', cascade='all, delete-orphan')
    cuenta_por_pagar = db.relationship('CuentaPorPagar', backref='compra', uselist=False, cascade='all, delete-orphan')
    
    usuario_registra = db.relationship('Usuario', foreign_keys=[usuario_registra_id], backref='compras_registradas')
    usuario_recibe = db.relationship('Usuario', foreign_keys=[usuario_recibe_id], backref='compras_recibidas')
    
    def __repr__(self):
        return f'<Compra {self.numero_compra}>'
    
    def monto_pagado(self):
        """Calcula total pagado"""
        return sum(float(p.monto) for p in self.pagos)
    
    def monto_pendiente(self):
        """Calcula pendiente de pago"""
        return float(self.total) - self.monto_pagado()

class CompraDetalle(db.Model):
    __tablename__ = 'compra_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    
    # PRODUCTO
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=True)
    cantidad = db.Column(db.Numeric(10, 2), nullable=True)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Actualización de stock
    stock_actualizado = db.Column(db.Boolean, default=False)
    
    # SERVICIO/FACTURA
    concepto = db.Column(db.String(255), nullable=True)
    
    # LEGACY
    lote = db.Column(db.String(50), nullable=True)
    fecha_vencimiento_lote = db.Column(db.Date, nullable=True)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        if self.producto:
            return f'<CompraDetalle {self.producto.nombre}>'
        return f'<CompraDetalle {self.concepto}>'

# ===== PAGO DE COMPRA (NUEVO - LA CLAVE) =====
class PagoCompra(db.Model):
    __tablename__ = 'pagos_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    
    # DECISIÓN CRUCIAL
    origen_pago = db.Column(db.String(50), nullable=False)  # 'caja_chica', 'otra_fuente'
    
    # Si es caja chica
    apertura_caja_id = db.Column(db.Integer, db.ForeignKey('aperturas_caja.id'), nullable=True)
    movimiento_caja_id = db.Column(db.Integer, db.ForeignKey('movimientos_caja.id'), nullable=True)
    
    # Si es otra fuente
    referencia = db.Column(db.String(255), nullable=True)  # Transf., cheque, etc
    
    observaciones = db.Column(db.Text)
    usuario_paga_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario_paga = db.relationship('Usuario', backref='pagos_compra')
    
    def __repr__(self):
        return f'<PagoCompra {self.compra_id} - {self.origen_pago}>'

# ===== MOVIMIENTO DE CAJA (NUEVO) =====
class MovimientoCaja(db.Model):
    __tablename__ = 'movimientos_caja'
    
    id = db.Column(db.Integer, primary_key=True)
    apertura_caja_id = db.Column(db.Integer, db.ForeignKey('aperturas_caja.id'), nullable=False)
    
    tipo = db.Column(db.String(50), nullable=False)  # 'ingreso', 'egreso'
    concepto = db.Column(db.String(255), nullable=False)  # 'Venta', 'Compra a proveedor', etc
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Referencia
    referencia_id = db.Column(db.Integer, nullable=True)
    referencia_tipo = db.Column(db.String(50), nullable=True)  # 'venta', 'compra', 'otro'
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref='movimientos_caja')
    
    def __repr__(self):
        return f'<MovimientoCaja {self.concepto} {self.monto}>'

# ===== CUENTA POR PAGAR (ACTUALIZADA) =====
class CuentaPorPagar(db.Model):
    __tablename__ = 'cuentas_por_pagar'
    
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    
    monto_adeudado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_pagado = db.Column(db.Numeric(12, 2), default=0)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.Date)
    
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, pagada, parcial
    
    proveedor = db.relationship('Proveedor')
    
    # LEGACY
    monto_total = db.Column(db.Numeric(12, 2), nullable=True)
    saldo_pendiente = db.Column(db.Numeric(12, 2), nullable=True)
    pagos_proveedor = db.relationship('PagoProveedor', backref='cuenta', lazy='dynamic', cascade='all, delete-orphan')
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CuentaPorPagar Compra {self.compra_id}>'
    
    def actualizar_estado(self):
        """Actualiza estado basado en pagos"""
        if self.monto_pagado >= self.monto_adeudado:
            self.estado = 'pagada'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        else:
            self.estado = 'pendiente'

class PagoProveedor(db.Model):
    __tablename__ = 'pagos_proveedor'
    
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas_por_pagar.id'), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    forma_pago = db.Column(db.String(50), nullable=False)  # efectivo, transferencia, cheque
    referencia = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    usuario_registra_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    usuario_registra = db.relationship('Usuario', backref='pagos_proveedores')
    
    def __repr__(self):
        return f'<PagoProveedor {self.monto}>'
