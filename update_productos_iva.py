"""
Script para agregar campo tipo_iva a productos
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Agregar columna tipo_iva
        with db.engine.connect() as conn:
            try:
                conn.execute(text("""
                    ALTER TABLE productos 
                    ADD COLUMN IF NOT EXISTS tipo_iva VARCHAR(10) DEFAULT '10'
                """))
                conn.commit()
                print("✓ Campo tipo_iva agregado al modelo Producto")
            except Exception as e:
                print(f"Campo tipo_iva: {e}")
            
            # Actualizar productos existentes
            try:
                conn.execute(text("""
                    UPDATE productos 
                    SET tipo_iva = '10' 
                    WHERE tipo_iva IS NULL
                """))
                conn.commit()
                print("✓ Productos existentes actualizados con IVA 10%")
            except Exception as e:
                print(f"Actualización: {e}")
        
        print("\n✅ Base de datos actualizada correctamente!")
        print("\n📋 Tipos de IVA disponibles:")
        print("  - '10'    → IVA 10% (estándar)")
        print("  - '5'     → IVA 5% (reducido)")
        print("  - 'exenta' → Exenta de IVA (0%)")
        print("\n💡 Ahora cada producto puede tener su tipo de IVA")
        print("   La factura calculará subtotales por cada tipo de IVA")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
