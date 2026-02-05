from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Verificar si hay datos en la tabla
    count = db.session.execute(text("SELECT COUNT(*) FROM notas_debito")).scalar()
    print(f"Registros en notas_debito: {count}")
    
    # Ver valores de la columna 'estado' antigua
    if count > 0:
        result = db.session.execute(text("SELECT id, estado FROM notas_debito"))
        print("\nValores columna 'estado' (antigua):")
        for row in result:
            print(f"  ID {row[0]}: estado={row[1]}")
