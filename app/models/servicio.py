from datetime import datetime
from app import db

class TipoServicio(db.Model):
    __tablename__ = 'tipos_servicio'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_base = db.Column(db.Numeric(12, 2), default=0)
    tiempo_estimado = db.Column(db.Integer, default=1)
    activo = db.Column(db.Boolean, default=True)
    
    solicitudes = db.relationship('SolicitudServicio', backref='tipo_servicio', lazy='dynamic')
    
    def __repr__(self):
        return f'<TipoServicio {self.nombre}>'

class SolicitudServicio(db.Model):
    __tablename__ = 'solicitudes_servicio'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_solicitud = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo_servicio_id = db.Column(db.Integer, db.ForeignKey('tipos_servicio.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_proceso, terminado, entregado, rechazado
    prioridad = db.Column(db.String(20), default='normal')  # baja, normal, alta, urgente
    fecha_estimada = db.Column(db.Date)
    usuario_registro_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    costo_estimado = db.Column(db.Numeric(12, 2), default=0)
    descuento_estimado = db.Column(db.Numeric(12, 2), default=0)
    total_estimado = db.Column(db.Numeric(12, 2), default=0)
    
    # Relaciones
    usuario_registro = db.relationship('Usuario', backref='solicitudes_registradas')
    producto = db.relationship('Producto', backref='solicitudes_servicio')
    presupuestos = db.relationship('Presupuesto', backref='solicitud', lazy='dynamic')
    orden_servicio = db.relationship('OrdenServicio', backref='solicitud', uselist=False)
    
    def __repr__(self):
        return f'<SolicitudServicio {self.numero_solicitud}>'

class Presupuesto(db.Model):
    __tablename__ = 'presupuestos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_presupuesto = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_servicio.id'), nullable=False)
    descripcion_trabajo = db.Column(db.Text, nullable=False)
    mano_obra = db.Column(db.Numeric(12, 2), default=0)
    costo_materiales = db.Column(db.Numeric(12, 2), default=0)
    otros_costos = db.Column(db.Numeric(12, 2), default=0)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    dias_estimados = db.Column(db.Integer)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobado, rechazado, vencido
    fecha_validez = db.Column(db.Date)
    fecha_aprobacion = db.Column(db.DateTime)
    usuario_elabora_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    # Relaciones
    usuario_elabora = db.relationship('Usuario', backref='presupuestos_elaborados')
    detalles = db.relationship('PresupuestoDetalle', backref='presupuesto', lazy='dynamic', cascade='all, delete-orphan')
    
    def calcular_totales(self):
        self.subtotal = self.mano_obra + self.costo_materiales + self.otros_costos
        self.total = self.subtotal - self.descuento + self.iva
    
    def __repr__(self):
        return f'<Presupuesto {self.numero_presupuesto}>'

class PresupuestoDetalle(db.Model):
    __tablename__ = 'presupuesto_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey('presupuestos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<PresupuestoDetalle {self.descripcion}>'

class OrdenServicio(db.Model):
    __tablename__ = 'ordenes_servicio'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_orden = db.Column(db.DateTime, default=datetime.utcnow)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_servicio.id'), nullable=False)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey('presupuestos.id'))
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Cambiado de empleados a usuarios
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_proceso, finalizado, entregado, cancelado
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin_estimada = db.Column(db.DateTime)
    fecha_fin_real = db.Column(db.DateTime)
    observaciones = db.Column(db.Text)
    trabajo_realizado = db.Column(db.Text)
    
    # Relaciones
    presupuesto = db.relationship('Presupuesto', backref='ordenes')
    tecnico = db.relationship('Usuario', foreign_keys=[tecnico_id], backref='ordenes_servicio_tecnico')  # Cambiado a Usuario
    detalles_insumos = db.relationship('OrdenServicioDetalle', backref='orden', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OrdenServicio {self.numero_orden}>'

class OrdenServicioDetalle(db.Model):
    __tablename__ = 'orden_servicio_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes_servicio.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_estimada = db.Column(db.Numeric(10, 2))
    cantidad_utilizada = db.Column(db.Numeric(10, 2), default=0)
    costo_unitario = db.Column(db.Numeric(12, 2))
    fecha_uso = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto')
    
    def __repr__(self):
        return f'<OrdenServicioDetalle Orden {self.orden_id}>'

class Reclamo(db.Model):
    __tablename__ = 'reclamos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_reclamo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fecha_reclamo = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo_reclamo = db.Column(db.String(50), nullable=False)  # servicio, producto, atencion, garantia
    orden_servicio_id = db.Column(db.Integer, db.ForeignKey('ordenes_servicio.id'))
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'))
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='abierto')  # abierto, en_proceso, resuelto, cerrado
    prioridad = db.Column(db.String(20), default='normal')
    asignado_a_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    solucion = db.Column(db.Text)
    fecha_resolucion = db.Column(db.DateTime)
    satisfaccion_cliente = db.Column(db.Integer)  # 1-5
    
    # Relaciones
    orden_servicio = db.relationship('OrdenServicio', backref='reclamos')
    venta = db.relationship('Venta', backref='reclamos')
    asignado_a = db.relationship('Usuario', backref='reclamos_asignados')
    seguimientos = db.relationship('ReclamoSeguimiento', backref='reclamo', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Reclamo {self.numero_reclamo}>'

class ReclamoSeguimiento(db.Model):
    __tablename__ = 'reclamo_seguimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    reclamo_id = db.Column(db.Integer, db.ForeignKey('reclamos.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    descripcion = db.Column(db.Text, nullable=False)
    estado_anterior = db.Column(db.String(20))
    estado_nuevo = db.Column(db.String(20))
    
    usuario = db.relationship('Usuario', backref='seguimientos_reclamos')
    
    def __repr__(self):
        return f'<ReclamoSeguimiento {self.reclamo_id}>'
