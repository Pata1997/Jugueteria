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
        with open("fix_tablas_detalles.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())

print("¡Tablas creadas correctamente!")
