#!/usr/bin/env python
"""Agrega columnas de costos estimados a solicitudes_servicio"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("""
            ALTER TABLE solicitudes_servicio
            ADD COLUMN IF NOT EXISTS costo_estimado NUMERIC(12,2) DEFAULT 0;
        """))
        db.session.execute(text("""
            ALTER TABLE solicitudes_servicio
            ADD COLUMN IF NOT EXISTS descuento_estimado NUMERIC(12,2) DEFAULT 0;
        """))
        db.session.execute(text("""
            ALTER TABLE solicitudes_servicio
            ADD COLUMN IF NOT EXISTS total_estimado NUMERIC(12,2) DEFAULT 0;
        """))
        db.session.commit()
        print("✓ Columnas de costos agregadas")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {e}")
