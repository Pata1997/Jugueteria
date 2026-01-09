from datetime import datetime
from app import db

class Empleado(db.Model):
    __tablename__ = 'empleados'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    ci = db.Column(db.String(50), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    cargo = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    fecha_ingreso = db.Column(db.Date, nullable=False)
    fecha_egreso = db.Column(db.Date)
    salario = db.Column(db.Numeric(12, 2))
    activo = db.Column(db.Boolean, default=True)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    vacaciones = db.relationship('Vacacion', backref='empleado', lazy='dynamic')
    permisos = db.relationship('Permiso', backref='empleado', lazy='dynamic')
    asistencias = db.relationship('Asistencia', backref='empleado', lazy='dynamic')
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def __repr__(self):
        return f'<Empleado {self.codigo} - {self.nombre_completo}>'

class Vacacion(db.Model):
    __tablename__ = 'vacaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    dias_solicitados = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobada, rechazada, cancelada
    fecha_aprobacion = db.Column(db.DateTime)
    aprobado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    aprobado_por = db.relationship('Usuario', backref='vacaciones_aprobadas')
    
    def __repr__(self):
        return f'<Vacacion Empleado {self.empleado_id} - {self.fecha_inicio}>'

class Permiso(db.Model):
    __tablename__ = 'permisos'
    
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_permiso = db.Column(db.String(50), nullable=False)  # personal, medico, familiar, otro
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    horas_solicitadas = db.Column(db.Numeric(5, 2))
    motivo = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobado, rechazado, cancelado
    fecha_aprobacion = db.Column(db.DateTime)
    aprobado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)
    
    aprobado_por = db.relationship('Usuario', backref='permisos_aprobados')
    
    def __repr__(self):
        return f'<Permiso Empleado {self.empleado_id} - {self.tipo_permiso}>'

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_entrada = db.Column(db.Time)
    hora_salida = db.Column(db.Time)
    estado = db.Column(db.String(20), nullable=False)  # presente, ausente, tarde, permiso, vacacion
    horas_trabajadas = db.Column(db.Numeric(5, 2))
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Asistencia {self.empleado.nombre_completo} - {self.fecha}>'

class HorarioAtencion(db.Model):
    __tablename__ = 'horarios_atencion'
    
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Lunes, 6=Domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    empleado = db.relationship('Empleado', backref='horarios')
    
    def __repr__(self):
        return f'<HorarioAtencion {self.empleado.nombre_completo} - Dia {self.dia_semana}>'
