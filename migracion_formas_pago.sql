-- =========================================
-- Script de migración para Sistema de Formas de Pago y Vuelto
-- Base de datos: PostgreSQL
-- Fecha: 2026-01-06
-- =========================================

-- 1. AGREGAR COLUMNAS A TABLA formas_pago
-- =========================================

-- Agregar columna descripcion (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'formas_pago' AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE formas_pago ADD COLUMN descripcion TEXT;
        RAISE NOTICE 'Columna descripcion agregada a formas_pago';
    ELSE
        RAISE NOTICE 'Columna descripcion ya existe en formas_pago';
    END IF;
END $$;

-- Agregar columna requiere_referencia (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'formas_pago' AND column_name = 'requiere_referencia'
    ) THEN
        ALTER TABLE formas_pago ADD COLUMN requiere_referencia BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Columna requiere_referencia agregada a formas_pago';
    ELSE
        RAISE NOTICE 'Columna requiere_referencia ya existe en formas_pago';
    END IF;
END $$;

-- 2. INSERTAR/ACTUALIZAR FORMAS DE PAGO PREDEFINIDAS
-- =========================================

-- Efectivo
INSERT INTO formas_pago (codigo, nombre, descripcion, activo, requiere_referencia)
VALUES ('efectivo', 'Efectivo', 'Pago en efectivo', TRUE, FALSE)
ON CONFLICT (codigo) 
DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    requiere_referencia = EXCLUDED.requiere_referencia;

-- Tarjeta de Débito
INSERT INTO formas_pago (codigo, nombre, descripcion, activo, requiere_referencia)
VALUES ('tarjeta_debito', 'Tarjeta de Débito', 'Pago con tarjeta de débito', TRUE, TRUE)
ON CONFLICT (codigo) 
DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    requiere_referencia = EXCLUDED.requiere_referencia;

-- Tarjeta de Crédito
INSERT INTO formas_pago (codigo, nombre, descripcion, activo, requiere_referencia)
VALUES ('tarjeta_credito', 'Tarjeta de Crédito', 'Pago con tarjeta de crédito', TRUE, TRUE)
ON CONFLICT (codigo) 
DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    requiere_referencia = EXCLUDED.requiere_referencia;

-- Cheque
INSERT INTO formas_pago (codigo, nombre, descripcion, activo, requiere_referencia)
VALUES ('cheque', 'Cheque', 'Pago con cheque', TRUE, TRUE)
ON CONFLICT (codigo) 
DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    requiere_referencia = EXCLUDED.requiere_referencia;

-- Transferencia Bancaria
INSERT INTO formas_pago (codigo, nombre, descripcion, activo, requiere_referencia)
VALUES ('transferencia', 'Transferencia Bancaria', 'Pago por transferencia bancaria', TRUE, TRUE)
ON CONFLICT (codigo) 
DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    requiere_referencia = EXCLUDED.requiere_referencia;

-- 3. VERIFICACIÓN
-- =========================================

-- Mostrar formas de pago registradas
SELECT 
    id, 
    codigo, 
    nombre, 
    descripcion, 
    activo, 
    requiere_referencia 
FROM formas_pago 
ORDER BY id;

-- =========================================
-- FIN DEL SCRIPT
-- =========================================

-- NOTA: Si la tabla formas_pago no tiene la columna 'codigo' como UNIQUE,
-- deberás ejecutar esto antes de los INSERT ON CONFLICT:
-- ALTER TABLE formas_pago ADD CONSTRAINT formas_pago_codigo_key UNIQUE (codigo);
