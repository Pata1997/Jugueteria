from datetime import datetime
from app import db

class Caja(db.Model):
    __tablename__ = 'cajas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_caja = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    aperturas = db.relationship('AperturaCaja', backref='caja', lazy='dynamic')
    
    def __repr__(self):
        return f'<Caja {self.nombre}>'

class AperturaCaja(db.Model):
    __tablename__ = 'aperturas_caja'
    
    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey('cajas.id'), nullable=False)
    cajero_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_apertura = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime)
    monto_inicial = db.Column(db.Numeric(12, 2), nullable=False)
    monto_final = db.Column(db.Numeric(12, 2))
    monto_sistema = db.Column(db.Numeric(12, 2))
    diferencia = db.Column(db.Numeric(12, 2))
    estado = db.Column(db.String(20), default='abierto')  # abierto, en_arqueo, cerrada
    observaciones = db.Column(db.Text)
    
    # Campos para arqueo (valores reales contados)
    monto_efectivo_real = db.Column(db.Numeric(12, 2))
    monto_tarjeta_real = db.Column(db.Numeric(12, 2))
    monto_transferencias_real = db.Column(db.Numeric(12, 2))
    monto_cheques_real = db.Column(db.Numeric(12, 2))
    
    # Campos para arqueo (valores esperados por forma de pago)
    monto_efectivo_esperado = db.Column(db.Numeric(12, 2))
    monto_tarjeta_esperado = db.Column(db.Numeric(12, 2))
    monto_transferencias_esperado = db.Column(db.Numeric(12, 2))
    monto_cheques_esperado = db.Column(db.Numeric(12, 2))
    
    cajero = db.relationship('Usuario', backref='aperturas_caja')
    ventas = db.relationship('Venta', backref='apertura_caja', lazy='dynamic')
    movimientos = db.relationship('MovimientoCaja', backref='apertura_caja', lazy='dynamic', cascade='all, delete-orphan')
    
    def calcular_cierre(self):
        total_efectivo = sum(
            p.monto for v in self.ventas 
            for p in v.pagos 
            if p.forma_pago == 'efectivo'
        )
        self.monto_sistema = self.monto_inicial + total_efectivo
        
        if self.monto_final:
            self.diferencia = self.monto_final - self.monto_sistema
    
    def __repr__(self):
        return f'<AperturaCaja {self.caja.nombre} - {self.fecha_apertura}>'

class Venta(db.Model):
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_factura = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_venta = db.Column(db.String(20), nullable=False)  # producto, servicio, mixta
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    orden_servicio_id = db.Column(db.Integer, db.ForeignKey('ordenes_servicio.id'))
    apertura_caja_id = db.Column(db.Integer, db.ForeignKey('aperturas_caja.id'))
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    
    estado = db.Column(db.String(20), default='completada')  # completada, anulada
    estado_pago = db.Column(db.String(20), default='pagado')  # pagado, pendiente, parcial
    dias_credito = db.Column(db.Integer, default=0)
    fecha_vencimiento = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    orden_servicio = db.relationship('OrdenServicio', backref='ventas')
    vendedor = db.relationship('Usuario', backref='ventas')
    detalles = db.relationship('VentaDetalle', backref='venta', lazy='dynamic', cascade='all, delete-orphan')
    pagos = db.relationship('Pago', backref='venta', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def monto_pagado(self):
        return sum(p.monto for p in self.pagos if p.estado == 'confirmado')
    
    @property
    def saldo_pendiente(self):
        return self.total - self.monto_pagado
    
    def actualizar_estado_pago(self):
        pagado = self.monto_pagado
        estado_anterior = self.estado_pago
        
        if pagado >= self.total:
            self.estado_pago = 'pagado'
        elif pagado > 0:
            self.estado_pago = 'parcial'
        else:
            self.estado_pago = 'pendiente'
        
        # Si cambió a "pagado", descontar stock de los productos
        if self.estado_pago == 'pagado' and estado_anterior != 'pagado':
            self._descontar_stock()
    
    def _descontar_stock(self):
        """Descuenta el stock de los productos cuando la venta se marca como pagada"""
        from app.models.producto import Producto, MovimientoProducto
        from flask_login import current_user
        from datetime import datetime
        
        for detalle in self.detalles:
            if detalle.producto_id:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    # Registrar movimiento anterior
                    stock_anterior = producto.stock_actual
                    
                    # Descontar stock (convertir a int)
                    cantidad = int(detalle.cantidad)
                    producto.stock_actual -= cantidad
                    
                    # Registrar movimiento en la auditoría
                    movimiento = MovimientoProducto(
                        producto_id=producto.id,
                        tipo_movimiento='salida',
                        cantidad=cantidad,
                        stock_anterior=stock_anterior,
                        stock_actual=producto.stock_actual,
                        motivo='venta',
                        referencia_tipo='venta',
                        referencia_id=self.id,
                        costo_unitario=producto.precio_compra,
                        usuario_id=self.vendedor_id if hasattr(self, 'vendedor_id') else None
                    )
                    from app import db
                    db.session.add(movimiento)
    
    def __repr__(self):
        return f'<Venta {self.numero_factura}>'

class VentaDetalle(db.Model):
    __tablename__ = 'venta_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    tipo_item = db.Column(db.String(20), nullable=False)  # producto, servicio, insumo
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<VentaDetalle {self.descripcion}>'

class FormaPago(db.Model):
    __tablename__ = 'formas_pago'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    requiere_referencia = db.Column(db.Boolean, default=False)
    # Si es True, se debe capturar número de cheque, últimos 4 dígitos, etc.

    @classmethod
    def activas_unicas(cls):
        """Devuelve formas de pago activas sin duplicados por código/nombre."""
        vistos = set()
        resultado = []
        registros = cls.query.filter_by(activo=True).order_by(cls.nombre, cls.id).all()
        for fp in registros:
            clave = (fp.codigo or '').strip().lower() or (fp.nombre or '').strip().lower() or str(fp.id)
            if clave in vistos:
                continue
            vistos.add(clave)
            resultado.append(fp)
        return resultado
    
    def __repr__(self):
        return f'<FormaPago {self.nombre}>'

class Pago(db.Model):
    __tablename__ = 'pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    forma_pago_id = db.Column(db.Integer, db.ForeignKey('formas_pago.id'), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    referencia = db.Column(db.String(100))  # número de cheque, transacción, etc
    banco = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='confirmado')  # confirmado, pendiente, rechazado
    observaciones = db.Column(db.Text)
    
    forma_pago = db.relationship('FormaPago', backref='pagos_realizados')
    
    def __repr__(self):
        return f'<Pago {self.forma_pago.nombre if self.forma_pago else "N/A"} - {self.monto}>'

class NotaCredito(db.Model):
    __tablename__ = 'notas_credito'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_nota = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    estado = db.Column(db.String(20), default='activa')  # activa, anulada
    observaciones = db.Column(db.Text)
    
    venta = db.relationship('Venta', backref='notas_credito')
    usuario = db.relationship('Usuario', backref='notas_credito')
    detalles = db.relationship('NotaCreditoDetalle', backref='nota_credito', lazy='select', cascade='all, delete-orphan')
    
    
    def __repr__(self):
        return f'<NotaCredito {self.numero_nota}>'

# NotaDebito se movió a app.models.nota_debito para mejor organización
# Ver nota_debito.py para la definición completa del modelo

