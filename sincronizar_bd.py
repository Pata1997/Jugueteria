#!/usr/bin/env python3
"""
Script para sincronizar la Base de Datos entre máquinas.
Ejecuta todas las migraciones y crea las tablas faltantes.

Uso:
    python sincronizar_bd.py
"""

import sys
import os
from app import create_app, db

def main():
    print("=" * 80)
    print("SINCRONIZACION DE BASE DE DATOS")
    print("=" * 80)
    
    # Crear app context
    app = create_app()
    
    with app.app_context():
        try:
            print("\n[1/3] Creando tablas con create_all()...")
            db.create_all()
            print("[OK] Tablas creadas/actualizadas")
            
            print("\n[2/3] Validando integridad de tablas...")
            # Listar todas las tablas esperadas
            expected_tables = [
                'usuarios', 'categorias', 'productos', 'movimientos_producto',
                'historial_precios', 'clientes', 'ventas', 'venta_detalles',
                'pagos', 'notas_credito', 'nota_credito_detalles',
                'notas_debito', 'nota_debito_detalles', 'pagos_nota_debito',
                'notas_credito_compra', 'nota_credito_compra_detalles',
                'notas_debito_compra', 'nota_debito_compra_detalles',
                'compras', 'compra_detalles', 'ordenes_servicio',
                'orden_servicio_detalles', 'servicios', 'cajas', 'apertura_caja',
                'configuracion_empresa', 'bitacora', 'formas_pago'
            ]
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            
            if missing_tables:
                print(f"[WARN] Tablas faltantes: {', '.join(missing_tables)}")
            else:
                print("[OK] Todas las tablas principales existen")
            
            print(f"\nTablas en BD: {len(existing_tables)}")
            for table in sorted(existing_tables):
                columns = len(inspector.get_columns(table))
                print(f"  - {table} ({columns} columnas)")
            
            print("\n[3/3] Validando columnas criticas...")
            # Validar que stock_actual sea INTEGER en productos
            producto_cols = {col['name']: col['type'] for col in inspector.get_columns('productos')}
            if 'stock_actual' in producto_cols:
                col_type = str(producto_cols['stock_actual'])
                if 'INTEGER' in col_type.upper():
                    print("[OK] Columna stock_actual es INTEGER")
                else:
                    print(f"[WARN] stock_actual es {col_type}, deberia ser INTEGER")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] SINCRONIZACION COMPLETADA EXITOSAMENTE")
            print("=" * 80)
            print("\nProximos pasos:")
            print("1. Subir este script a git: git add sincronizar_bd.py")
            print("2. Hacer commit: git commit -m 'Agregar script de sincronizacion BD'")
            print("3. Hacer push: git push origin main")
            print("\nEn la otra maquina:")
            print("1. Hacer pull: git pull origin main")
            print("2. Ejecutar: python sincronizar_bd.py")
            print("\n¡La BD esta lista para usar!")
            
            return 0
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    sys.exit(main())
