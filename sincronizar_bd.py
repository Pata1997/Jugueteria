#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sincronizacion de Base de Datos - Jugueteria
=======================================================
Ejecuta todas las migraciones necesarias de forma segura e idempotente.
Puede correrse multiples veces sin romper nada.

Uso:
    python sincronizar_bd.py

Lo que hace:
    1. Crea tablas nuevas que no existan (create_all)
    2. Aplica todos los ALTER TABLE acumulados del proyecto
    3. Corrige restricciones NOT NULL incorrectas
    4. Crea indices faltantes
    5. Reporta el estado final de cada tabla
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def col_exists(inspector, tabla, columna):
    cols = [c['name'] for c in inspector.get_columns(tabla)]
    return columna in cols

def tabla_existe(inspector, tabla):
    return tabla in inspector.get_table_names()

def index_exists(inspector, tabla, index_name):
    indices = [i['name'] for i in inspector.get_indexes(tabla)]
    return index_name in indices

def es_nullable(inspector, tabla, columna):
    for c in inspector.get_columns(tabla):
        if c['name'] == columna:
            return c['nullable']
    return None

def ok(msg):
    print(f"  [OK] {msg}")

def skip(msg):
    print(f"  [--] {msg} (ya existe, se omite)")

def warn(msg):
    print(f"  [!!] {msg}")

def run(conn, sql, descripcion):
    try:
        conn.execute(text(sql))
        conn.commit()
        ok(descripcion)
    except Exception as e:
        conn.rollback()
        warn(f"{descripcion} => {e}")

# -----------------------------------------------------------------------
# Migraciones
# -----------------------------------------------------------------------

def migrar_formas_pago(conn, inspector):
    print("\n--- formas_pago ---")
    if not tabla_existe(inspector, 'formas_pago'):
        skip("tabla formas_pago no existe aun, se creara con create_all")
        return
    for col, tipo in [('descripcion', 'TEXT'), ('requiere_referencia', 'BOOLEAN DEFAULT FALSE')]:
        if not col_exists(inspector, 'formas_pago', col):
            run(conn, f"ALTER TABLE formas_pago ADD COLUMN {col} {tipo}", f"ADD COLUMN {col}")
        else:
            skip(f"formas_pago.{col}")


def migrar_tipos_servicio(conn, inspector):
    print("\n--- tipos_servicio ---")
    if not tabla_existe(inspector, 'tipos_servicio'):
        skip("tabla tipos_servicio no existe aun")
        return
    if not col_exists(inspector, 'tipos_servicio', 'tiempo_estimado'):
        run(conn, "ALTER TABLE tipos_servicio ADD COLUMN tiempo_estimado INTEGER DEFAULT 1",
            "ADD COLUMN tiempo_estimado")
    else:
        skip("tipos_servicio.tiempo_estimado")


def migrar_solicitudes_servicio(conn, inspector):
    print("\n--- solicitudes_servicio ---")
    if not tabla_existe(inspector, 'solicitudes_servicio'):
        skip("tabla solicitudes_servicio no existe aun")
        return
    for col, tipo in [
        ('costo_estimado',    'NUMERIC(12,2) DEFAULT 0'),
        ('descuento_estimado','NUMERIC(12,2) DEFAULT 0'),
        ('total_estimado',    'NUMERIC(12,2) DEFAULT 0'),
    ]:
        if not col_exists(inspector, 'solicitudes_servicio', col):
            run(conn, f"ALTER TABLE solicitudes_servicio ADD COLUMN {col} {tipo}", f"ADD COLUMN {col}")
        else:
            skip(f"solicitudes_servicio.{col}")


def migrar_notas_debito(conn, inspector):
    print("\n--- notas_debito ---")
    if not tabla_existe(inspector, 'notas_debito'):
        skip("tabla notas_debito no existe aun")
        return
    for col, tipo in [
        ('estado_emision',     'VARCHAR(50)'),
        ('estado_pago',        'VARCHAR(50)'),
        ('fecha_modificacion', 'TIMESTAMP'),
        ('tipo',               'VARCHAR(50)'),
    ]:
        if not col_exists(inspector, 'notas_debito', col):
            run(conn, f"ALTER TABLE notas_debito ADD COLUMN {col} {tipo}", f"ADD COLUMN {col}")
        else:
            skip(f"notas_debito.{col}")


def migrar_notas_debito_detalle(conn, inspector):
    print("\n--- notas_debito_detalle ---")
    if not tabla_existe(inspector, 'notas_debito_detalle'):
        skip("tabla notas_debito_detalle no existe aun")
        return
    if not col_exists(inspector, 'notas_debito_detalle', 'venta_detalle_id'):
        run(conn, "ALTER TABLE notas_debito_detalle ADD COLUMN venta_detalle_id INTEGER",
            "ADD COLUMN venta_detalle_id")
    else:
        skip("notas_debito_detalle.venta_detalle_id")


def migrar_notas_credito_compra(conn, inspector):
    print("\n--- notas_credito_compra ---")
    if not tabla_existe(inspector, 'notas_credito_compra'):
        skip("tabla notas_credito_compra no existe aun")
        return

    # Renombrar numero_nota -> numero_nota_proveedor
    if col_exists(inspector, 'notas_credito_compra', 'numero_nota') and \
       not col_exists(inspector, 'notas_credito_compra', 'numero_nota_proveedor'):
        run(conn,
            "ALTER TABLE notas_credito_compra RENAME COLUMN numero_nota TO numero_nota_proveedor",
            "RENAME numero_nota -> numero_nota_proveedor")
    else:
        skip("notas_credito_compra.numero_nota ya renombrado")

    # Renombrar fecha_emision -> fecha_nota_proveedor
    if col_exists(inspector, 'notas_credito_compra', 'fecha_emision') and \
       not col_exists(inspector, 'notas_credito_compra', 'fecha_nota_proveedor'):
        run(conn,
            "ALTER TABLE notas_credito_compra RENAME COLUMN fecha_emision TO fecha_nota_proveedor",
            "RENAME fecha_emision -> fecha_nota_proveedor")
    else:
        skip("notas_credito_compra.fecha_emision ya renombrado")

    # Agregar fecha_registro
    if not col_exists(inspector, 'notas_credito_compra', 'fecha_registro'):
        run(conn,
            "ALTER TABLE notas_credito_compra ADD COLUMN fecha_registro TIMESTAMP DEFAULT NOW()",
            "ADD COLUMN fecha_registro")
    else:
        skip("notas_credito_compra.fecha_registro")

    # Indices: eliminar el unico viejo y recrear sin unique
    if index_exists(inspector, 'notas_credito_compra', 'ix_notas_credito_compra_numero_nota'):
        run(conn, "DROP INDEX ix_notas_credito_compra_numero_nota",
            "DROP INDEX ix_notas_credito_compra_numero_nota")

    if not index_exists(inspector, 'notas_credito_compra', 'ix_notas_credito_compra_numero_nota_proveedor'):
        run(conn,
            "CREATE INDEX ix_notas_credito_compra_numero_nota_proveedor ON notas_credito_compra(numero_nota_proveedor)",
            "CREATE INDEX numero_nota_proveedor")
    else:
        skip("index ix_notas_credito_compra_numero_nota_proveedor")


def migrar_notas_debito_compra(conn, inspector):
    print("\n--- notas_debito_compra ---")
    if not tabla_existe(inspector, 'notas_debito_compra'):
        skip("tabla notas_debito_compra no existe aun")
        return

    if col_exists(inspector, 'notas_debito_compra', 'numero_nota') and \
       not col_exists(inspector, 'notas_debito_compra', 'numero_nota_proveedor'):
        run(conn,
            "ALTER TABLE notas_debito_compra RENAME COLUMN numero_nota TO numero_nota_proveedor",
            "RENAME numero_nota -> numero_nota_proveedor")
    else:
        skip("notas_debito_compra.numero_nota ya renombrado")

    if col_exists(inspector, 'notas_debito_compra', 'fecha_emision') and \
       not col_exists(inspector, 'notas_debito_compra', 'fecha_nota_proveedor'):
        run(conn,
            "ALTER TABLE notas_debito_compra RENAME COLUMN fecha_emision TO fecha_nota_proveedor",
            "RENAME fecha_emision -> fecha_nota_proveedor")
    else:
        skip("notas_debito_compra.fecha_emision ya renombrado")

    if not col_exists(inspector, 'notas_debito_compra', 'fecha_registro'):
        run(conn,
            "ALTER TABLE notas_debito_compra ADD COLUMN fecha_registro TIMESTAMP DEFAULT NOW()",
            "ADD COLUMN fecha_registro")
    else:
        skip("notas_debito_compra.fecha_registro")

    if index_exists(inspector, 'notas_debito_compra', 'ix_notas_debito_compra_numero_nota'):
        run(conn, "DROP INDEX ix_notas_debito_compra_numero_nota",
            "DROP INDEX ix_notas_debito_compra_numero_nota")

    if not index_exists(inspector, 'notas_debito_compra', 'ix_notas_debito_compra_numero_nota_proveedor'):
        run(conn,
            "CREATE INDEX ix_notas_debito_compra_numero_nota_proveedor ON notas_debito_compra(numero_nota_proveedor)",
            "CREATE INDEX numero_nota_proveedor")
    else:
        skip("index ix_notas_debito_compra_numero_nota_proveedor")


def migrar_presupuestos_proveedor(conn, inspector):
    print("\n--- presupuestos_proveedor ---")
    if not tabla_existe(inspector, 'presupuestos_proveedor'):
        skip("tabla presupuestos_proveedor no existe aun")
        return
    # pedido_id debe ser nullable
    if not es_nullable(inspector, 'presupuestos_proveedor', 'pedido_id'):
        run(conn,
            "ALTER TABLE presupuestos_proveedor ALTER COLUMN pedido_id DROP NOT NULL",
            "pedido_id DROP NOT NULL")
    else:
        skip("presupuestos_proveedor.pedido_id ya es nullable")


def migrar_pagos_nota_debito(conn, inspector):
    print("\n--- pagos_nota_debito ---")
    if tabla_existe(inspector, 'pagos_nota_debito'):
        skip("tabla pagos_nota_debito ya existe")
        return
    run(conn, """
        CREATE TABLE pagos_nota_debito (
            id SERIAL PRIMARY KEY,
            nota_debito_id INTEGER NOT NULL REFERENCES notas_debito(id) ON DELETE CASCADE,
            apertura_caja_id INTEGER,
            fecha_pago TIMESTAMP,
            forma_pago_id INTEGER NOT NULL REFERENCES formas_pago(id),
            monto NUMERIC(12,2) NOT NULL,
            referencia VARCHAR(100),
            banco VARCHAR(100),
            estado VARCHAR(20),
            observaciones TEXT
        )
    """, "CREATE TABLE pagos_nota_debito")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  SINCRONIZACION DE BASE DE DATOS - JUGUETERIA")
    print("=" * 70)

    app = create_app()

    with app.app_context():
        inspector = db.inspect(db.engine)

        # --- PASO 1: crear tablas nuevas ---
        print("\n[PASO 1] Creando tablas nuevas con create_all()...")
        try:
            db.create_all()
            ok("create_all() ejecutado")
        except Exception as e:
            warn(f"create_all() fallo: {e}")
            return 1

        # Re-inspeccionar despues del create_all
        inspector = db.inspect(db.engine)

        # --- PASO 2: aplicar migraciones ---
        print("\n[PASO 2] Aplicando migraciones acumuladas...")

        with db.engine.connect() as conn:
            migrar_formas_pago(conn, inspector)
            migrar_tipos_servicio(conn, inspector)
            migrar_solicitudes_servicio(conn, inspector)
            migrar_notas_debito(conn, inspector)
            migrar_notas_debito_detalle(conn, inspector)
            migrar_notas_credito_compra(conn, inspector)
            migrar_notas_debito_compra(conn, inspector)
            migrar_presupuestos_proveedor(conn, inspector)
            migrar_pagos_nota_debito(conn, inspector)

        # --- PASO 3: reporte final ---
        inspector = db.inspect(db.engine)
        tablas = sorted(inspector.get_table_names())

        print("\n[PASO 3] Estado final de la base de datos")
        print(f"  Total de tablas: {len(tablas)}")
        for t in tablas:
            ncols = len(inspector.get_columns(t))
            print(f"    - {t} ({ncols} columnas)")

        print("\n" + "=" * 70)
        print("  SINCRONIZACION COMPLETADA")
        print("=" * 70)
        print("""
Workflow recomendado para mantener maquinas sincronizadas:

  Esta maquina (cambios):
    git add .
    git commit -m "descripcion del cambio"
    git push origin main

  Otra maquina (actualizar):
    git pull origin main
    python sincronizar_bd.py

IMPORTANTE: Cada vez que agregues una columna o cambies un modelo,
agrega la migracion correspondiente en este script (una funcion
migrar_<tabla>) para que la otra maquina la aplique automaticamente.
""")
        return 0


if __name__ == '__main__':
    sys.exit(main())
