import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql+pg8000://postgres:123456@localhost:5432/jugueteria_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de paginación
    ITEMS_PER_PAGE = 20
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Zona horaria
    TIMEZONE = 'America/Asuncion'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
