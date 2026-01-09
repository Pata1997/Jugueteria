"""
Migración: Agregar producto_id a solicitudes_servicio
"""
import sys
sys.path.insert(0, 'C:\\Users\\Informatica 1\\Desktop\\Proyectos\\Jugueteria')

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Agregar columna producto_id
        db.session.execute(text("""
            ALTER TABLE solicitudes_servicio
            ADD COLUMN IF NOT EXISTS producto_id INTEGER REFERENCES productos(id)
        """))
        db.session.commit()
        print("✓ Columna producto_id agregada a solicitudes_servicio")
    except Exception as e:
        print(f"Error al agregar columna: {e}")
        db.session.rollback()
