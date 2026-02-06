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
            ALTER TABLE notas_debito_detalle ADD COLUMN venta_detalle_id INTEGER;
        ''')

print("Columna 'venta_detalle_id' agregada correctamente a notas_debito_detalle.")
