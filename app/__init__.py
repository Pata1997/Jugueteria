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
    from app.models import usuario, cliente, producto, servicio, venta, compra, configuracion
    
    # Context processor para hacer empresa disponible en todos los templates
    @app.context_processor
    def inject_empresa():
        import sys
        import time
        from sqlalchemy.exc import OperationalError
        max_retries = 5
        delay = 3  # segundos
        empresa = None
        for attempt in range(1, max_retries + 1):
            try:
                from app.models.configuracion import ConfiguracionEmpresa
                empresa = ConfiguracionEmpresa.query.first()
                print(f"✅ EMPRESA OBTENIDA: {empresa.nombre_empresa if empresa else None}", file=sys.stderr, flush=True)
                break
            except OperationalError as e:
                print(f"⏳ Intento {attempt}/{max_retries}: Base de datos no disponible aún: {e}", file=sys.stderr, flush=True)
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    print(f"❌ Error obteniendo empresa tras {max_retries} intentos: {e}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"❌ Error obteniendo empresa: {e}", file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
                break
        return dict(empresa=empresa)
    
    # Registrar blueprints
    from app.routes import auth, dashboard, clientes, productos, servicios, ventas, compras, reportes, configuracion as config_bp, caja
    from app.routes import bitacora


    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clientes.bp)
    app.register_blueprint(productos.bp)
    app.register_blueprint(servicios.bp)
    app.register_blueprint(ventas.bp)
    app.register_blueprint(compras.bp)
    app.register_blueprint(reportes.bp)
    app.register_blueprint(config_bp.bp)
    app.register_blueprint(caja.bp)
    app.register_blueprint(bitacora.bp)

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
