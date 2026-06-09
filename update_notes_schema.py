import os
os.environ['FLASK_ENV'] = 'development'
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Verificar si las columnas ya existen
        with db.engine.connect() as conn:
            # Para notas_credito_compra
            try:
                conn.execute(text("ALTER TABLE notas_credito_compra RENAME COLUMN numero_nota TO numero_nota_proveedor"))
                conn.commit()
                print("✓ Renombrado numero_nota a numero_nota_proveedor en notas_credito_compra")
            except Exception as e:
                print(f"Nota: {e}")
                
            try:
                conn.execute(text("ALTER TABLE notas_credito_compra RENAME COLUMN fecha_emision TO fecha_nota_proveedor"))
                conn.commit()
                print("✓ Renombrado fecha_emision a fecha_nota_proveedor en notas_credito_compra")
            except Exception as e:
                print(f"Nota: {e}")
            
            try:
                conn.execute(text("ALTER TABLE notas_credito_compra ADD COLUMN fecha_registro TIMESTAMP DEFAULT NOW()"))
                conn.commit()
                print("✓ Agregado fecha_registro en notas_credito_compra")
            except Exception as e:
                print(f"Nota: {e}")
            
            # Para notas_debito_compra
            try:
                conn.execute(text("ALTER TABLE notas_debito_compra RENAME COLUMN numero_nota TO numero_nota_proveedor"))
                conn.commit()
                print("✓ Renombrado numero_nota a numero_nota_proveedor en notas_debito_compra")
            except Exception as e:
                print(f"Nota: {e}")
                
            try:
                conn.execute(text("ALTER TABLE notas_debito_compra RENAME COLUMN fecha_emision TO fecha_nota_proveedor"))
                conn.commit()
                print("✓ Renombrado fecha_emision a fecha_nota_proveedor en notas_debito_compra")
            except Exception as e:
                print(f"Nota: {e}")
            
            try:
                conn.execute(text("ALTER TABLE notas_debito_compra ADD COLUMN fecha_registro TIMESTAMP DEFAULT NOW()"))
                conn.commit()
                print("✓ Agregado fecha_registro en notas_debito_compra")
            except Exception as e:
                print(f"Nota: {e}")
                
        print("\n✓ Cambios aplicados correctamente a la base de datos")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
