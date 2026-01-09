from datetime import datetime
from app import db

class ConfiguracionEmpresa(db.Model):
    __tablename__ = 'configuracion_empresa'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(200), nullable=False)
    ruc = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(255))
    
    # Configuración de facturación
    timbrado = db.Column(db.String(50))
    numero_establecimiento = db.Column(db.String(10), default='001')
    numero_expedicion = db.Column(db.String(10), default='001')
    numero_factura_desde = db.Column(db.Integer, default=1)
    numero_factura_hasta = db.Column(db.Integer, default=99999)
    numero_factura_actual = db.Column(db.Integer, default=1)
    fecha_vencimiento_timbrado = db.Column(db.Date)
    
    # Configuración de impuestos
    porcentaje_iva = db.Column(db.Numeric(5, 2), default=10)
    
    # Configuración de sistema
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConfiguracionEmpresa {self.nombre_empresa}>'
    
    @staticmethod
    def get_config():
        """Obtener o crear la configuración única"""
        config = ConfiguracionEmpresa.query.first()
        if not config:
            config = ConfiguracionEmpresa(
                nombre_empresa='Juguetería',
                ruc='',
                porcentaje_iva=10,
                numero_establecimiento='001',
                numero_expedicion='001',
                numero_factura_desde=1,
                numero_factura_hasta=99999,
                numero_factura_actual=1
            )
            db.session.add(config)
            db.session.commit()
        return config
    
    def generar_numero_factura(self):
        """Generar el siguiente número de factura automáticamente"""
        # Verificar que no se exceda el rango autorizado
        if self.numero_factura_actual > self.numero_factura_hasta:
            raise ValueError(f'Se ha alcanzado el límite de facturas autorizadas ({self.numero_factura_hasta}). Debe actualizar el timbrado.')
        
        # Formato: 001-001-0000001 (Establecimiento-Expedición-Número)
        numero = f"{self.numero_establecimiento or '001'}-{self.numero_expedicion or '001'}-{str(self.numero_factura_actual).zfill(7)}"
        
        # Incrementar contador
        self.numero_factura_actual += 1
        
        return numero
