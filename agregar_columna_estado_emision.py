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
        cur.execute("ALTER TABLE notas_debito ADD COLUMN estado_emision VARCHAR(50);")

print("Columna 'estado_emision' agregada correctamente a notas_debito.")
