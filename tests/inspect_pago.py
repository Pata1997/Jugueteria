import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

from app import create_app, db
from app.models.compra import Compra, PagoCompra

app = create_app()
with app.app_context():
    # Find latest compra
    compra = Compra.query.order_by(Compra.id.desc()).first()
    if compra:
        print(f"Última compra: {compra.numero_compra}, estado={compra.estado}, stock_actualizado={compra.stock_actualizado}")
        pagos = PagoCompra.query.filter_by(compra_id=compra.id).all()
        print(f"Pagos: {len(pagos)}")
        for p in pagos:
            print(f"  - Pago #{p.id}, monto={p.monto}, origen={p.origen_pago}")
    else:
        print("No hay compras.")
