-- SQL para crear la tabla notas_credito_detalle en PostgreSQL
CREATE TABLE IF NOT EXISTS notas_credito_detalle (
    id SERIAL PRIMARY KEY,
    nota_credito_id INTEGER NOT NULL REFERENCES notas_credito(id) ON DELETE CASCADE,
    venta_detalle_id INTEGER NOT NULL REFERENCES venta_detalles(id) ON DELETE CASCADE,
    cantidad NUMERIC(12,2) NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
