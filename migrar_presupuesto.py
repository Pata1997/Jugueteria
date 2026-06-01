from app import create_app, db

app = create_app()

with app.app_context():
    # Make pedido_id nullable in presupuestos_proveedor
    db.session.execute(db.text("ALTER TABLE presupuestos_proveedor ALTER COLUMN pedido_id DROP NOT NULL"))
    db.session.commit()
    print("Columna pedido_id ahora es nulable en presupuestos_proveedor.")
