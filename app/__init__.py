"""
Paquete principal de la aplicación
Inicialización de Flask y extensiones
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app(config_class=Config):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    # Importar modelos (necesario para migrations)
    from app.models import usuario, cliente, producto, servicio, venta, compra, empleado, configuracion
    
    # Context processor para hacer config disponible en todos los templates
    @app.context_processor
    def inject_config():
        import sys
        try:
            from app.models.configuracion import ConfiguracionEmpresa
            config = ConfiguracionEmpresa.get_config()
            print(f"✅ CONFIG OBTENIDA: {config.nombre_empresa}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"❌ Error obteniendo config: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            config = None
        return dict(config=config)
    
    # Registrar blueprints
    from app.routes import auth, dashboard, clientes, productos, servicios, ventas, compras, rrhh, reportes, configuracion as config_bp, caja
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clientes.bp)
    app.register_blueprint(productos.bp)
    app.register_blueprint(servicios.bp)
    app.register_blueprint(ventas.bp)
    app.register_blueprint(compras.bp)
    app.register_blueprint(rrhh.bp)
    app.register_blueprint(reportes.bp)
    app.register_blueprint(config_bp.bp)
    app.register_blueprint(caja.bp)
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario
        return Usuario.query.get(int(user_id))
    
    # Ruta principal
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    return app
