from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # We drop the unique index or constraint if it exists.
    # The error says "ix_notas_credito_compra_numero_nota"
    try:
        db.session.execute(text("DROP INDEX ix_notas_credito_compra_numero_nota;"))
        db.session.commit()
        print("Dropped ix_notas_credito_compra_numero_nota")
    except Exception as e:
        db.session.rollback()
        print("Could not drop index:", e)
        
    try:
        db.session.execute(text("DROP INDEX ix_notas_credito_compra_numero_nota_proveedor;"))
        db.session.commit()
        print("Dropped ix_notas_credito_compra_numero_nota_proveedor")
    except Exception as e:
        db.session.rollback()
        print("Could not drop index 2:", e)
        
    # Re-create the index WITHOUT unique
    try:
        db.session.execute(text("CREATE INDEX ix_notas_credito_compra_numero_nota_proveedor ON notas_credito_compra(numero_nota_proveedor);"))
        db.session.commit()
        print("Recreated index without unique")
    except Exception as e:
        db.session.rollback()
        print("Could not recreate index:", e)

    # Let's do the same for nota_debito_compra
    try:
        db.session.execute(text("DROP INDEX ix_notas_debito_compra_numero_nota;"))
        db.session.commit()
    except:
        db.session.rollback()
        
    try:
        db.session.execute(text("CREATE INDEX ix_notas_debito_compra_numero_nota_proveedor ON notas_debito_compra(numero_nota_proveedor);"))
        db.session.commit()
    except:
        db.session.rollback()

