#!/usr/bin/env python
"""Script para agregar la columna tiempo_estimado a la tabla tipos_servicio"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Agregar la columna si no existe
        db.session.execute(text("""
            ALTER TABLE tipos_servicio
            ADD COLUMN IF NOT EXISTS tiempo_estimado INTEGER DEFAULT 1
        """))
        db.session.commit()
        print("✓ Columna 'tiempo_estimado' agregada correctamente a la tabla 'tipos_servicio'")
    except Exception as e:
        print(f"✗ Error al agregar la columna: {str(e)}")
        db.session.rollback()
