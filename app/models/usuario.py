from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, vendedor, tecnico, cajero
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Relaciones
    empleado = db.relationship('Empleado', backref='usuario', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String(50), nullable=False)
    modulo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.accion} - {self.modulo}>'
