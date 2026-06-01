from app import create_app, db
from app.models.nota_credito_compra import NotaCreditoCompra, NotaCreditoCompraDetalle
from app.models.nota_debito_compra import NotaDebitoCompra, NotaDebitoCompraDetalle

app = create_app()

with app.app_context():
    # Creamos las tablas si no existen
    db.create_all()
    print("Tablas para Notas de Crédito y Débito de Compras creadas con éxito.")
