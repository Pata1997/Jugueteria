import psycopg2

# Datos de conexión
conn = psycopg2.connect(
    dbname="jugueteria_db",
    user="postgres",
    password="123456",
    host="localhost",
    port=5432
)

with conn:
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pagos_nota_debito (
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
            );
        ''')

print("Tabla 'pagos_nota_debito' creada correctamente (si no existía).")
