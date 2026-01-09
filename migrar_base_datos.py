"""
Script para ejecutar la migración de formas de pago directamente usando SQLAlchemy
Sin necesidad de tener psql instalado
"""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from sqlalchemy import text

def migrar_formas_pago():
    """Ejecuta la migración para agregar campos a FormaPago"""
    
    app = create_app()
    with app.app_context():
        print("Iniciando migración de base de datos...")
        
        try:
            # Verificar si las columnas ya existen
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'formas_pago' 
                AND column_name IN ('descripcion', 'requiere_referencia')
            """))
            columnas_existentes = [row[0] for row in result]
            
            # Agregar columna descripcion si no existe
            if 'descripcion' not in columnas_existentes:
                print("→ Agregando columna 'descripcion' a tabla formas_pago...")
                db.session.execute(text("""
                    ALTER TABLE formas_pago ADD COLUMN descripcion TEXT
                """))
                print("✓ Columna 'descripcion' agregada")
            else:
                print("✓ Columna 'descripcion' ya existe")
            
            # Agregar columna requiere_referencia si no existe
            if 'requiere_referencia' not in columnas_existentes:
                print("→ Agregando columna 'requiere_referencia' a tabla formas_pago...")
                db.session.execute(text("""
                    ALTER TABLE formas_pago ADD COLUMN requiere_referencia BOOLEAN DEFAULT FALSE
                """))
                print("✓ Columna 'requiere_referencia' agregada")
            else:
                print("✓ Columna 'requiere_referencia' ya existe")
            
            # Commit de cambios
            db.session.commit()
            print("\n✓ Migración completada exitosamente")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error durante la migración: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    exito = migrar_formas_pago()
    
    if exito:
        print("\n" + "="*60)
        print("Ahora ejecute: python inicializar_formas_pago.py")
        print("="*60)
        sys.exit(0)
    else:
        sys.exit(1)
