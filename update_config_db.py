"""
Script para actualizar la base de datos con los nuevos campos de configuración
"""
from app import create_app, db
from app.models.configuracion import ConfiguracionEmpresa
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Agregar columnas si no existen
        with db.engine.connect() as conn:
            # Verificar y agregar numero_factura_desde
            try:
                conn.execute(text("""
                    ALTER TABLE configuracion_empresa 
                    ADD COLUMN IF NOT EXISTS numero_factura_desde INTEGER DEFAULT 1
                """))
                conn.commit()
                print("✓ Campo numero_factura_desde agregado/verificado")
            except Exception as e:
                print(f"Campo numero_factura_desde: {e}")
            
            # Verificar y agregar numero_factura_hasta
            try:
                conn.execute(text("""
                    ALTER TABLE configuracion_empresa 
                    ADD COLUMN IF NOT EXISTS numero_factura_hasta INTEGER DEFAULT 99999
                """))
                conn.commit()
                print("✓ Campo numero_factura_hasta agregado/verificado")
            except Exception as e:
                print(f"Campo numero_factura_hasta: {e}")
            
            # Actualizar valores por defecto
            try:
                conn.execute(text("""
                    UPDATE configuracion_empresa 
                    SET numero_factura_desde = 1 
                    WHERE numero_factura_desde IS NULL
                """))
                conn.execute(text("""
                    UPDATE configuracion_empresa 
                    SET numero_factura_hasta = 99999 
                    WHERE numero_factura_hasta IS NULL
                """))
                conn.execute(text("""
                    UPDATE configuracion_empresa 
                    SET numero_establecimiento = '001' 
                    WHERE numero_establecimiento IS NULL
                """))
                conn.execute(text("""
                    UPDATE configuracion_empresa 
                    SET numero_expedicion = '001' 
                    WHERE numero_expedicion IS NULL
                """))
                conn.commit()
                print("✓ Valores por defecto actualizados")
            except Exception as e:
                print(f"Actualización de valores: {e}")
        
        print("\n¡Base de datos actualizada correctamente!")
        print("\nConfiguracion actual:")
        config = ConfiguracionEmpresa.get_config()
        print(f"  - Nombre: {config.nombre_empresa}")
        print(f"  - Timbrado: {config.timbrado or 'No configurado'}")
        print(f"  - Rango facturas: {config.numero_factura_desde} - {config.numero_factura_hasta}")
        print(f"  - Factura actual: {config.numero_factura_actual}")
        print(f"  - Establecimiento: {config.numero_establecimiento}")
        print(f"  - Punto expedición: {config.numero_expedicion}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
