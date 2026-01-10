import os
import sys
from datetime import datetime, timedelta
from flask import url_for

# Ensure workspace root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import db
from app import create_app
from app.models.usuario import Usuario
from app.models.venta import Caja, AperturaCaja
from app.models.producto import Producto
from app.models.compra import Proveedor, Compra, CompraDetalle, CuentaPorPagar, PagoCompra, MovimientoCaja


def setup_app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    return app


def ensure_user():
    user = Usuario.query.filter_by(username="tester").first()
    if not user:
        user = Usuario(
            username="tester",
            email="tester@example.com",
            nombre="Test",
            apellido="User",
            rol="admin",
            activo=True,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    return user


def ensure_open_caja():
    caja = Caja.query.first()
    if not caja:
        caja = Caja(numero_caja="001", nombre="Principal", activo=True)
        db.session.add(caja)
        db.session.commit()

    apertura = AperturaCaja.query.filter_by(estado='abierto').first()
    if not apertura:
        apertura = AperturaCaja(
            caja_id=caja.id,
            cajero_id=Usuario.query.first().id,
            fecha_apertura=datetime.utcnow(),
            monto_inicial=5000000,  # 5 millones para tener fondos suficientes
            monto_final=5000000,
            estado='abierto'
        )
        db.session.add(apertura)
    # Always reset funds for test consistency
    apertura.monto_inicial = 5000000
    apertura.monto_final = 5000000
    db.session.commit()
    return apertura


def create_test_data_producto_compra():
    prov = Proveedor.query.filter_by(ruc="99999901-0").first()
    if not prov:
        prov = Proveedor(codigo="PROV-TEST", razon_social="Proveedor Test", ruc="99999901-0")
        db.session.add(prov)
        db.session.commit()

    prod = Producto.query.filter_by(codigo="PRD-TEST").first()
    if not prod:
        prod = Producto(
            codigo="PRD-TEST",
            nombre="Producto de Prueba",
            tipo_producto="producto",
            precio_compra=10000,
            stock_actual=10,
            activo=True
        )
        db.session.add(prod)
        db.session.commit()

    num_cr = f"C-TEST-CR-{int(datetime.utcnow().timestamp())}"
    compra_credito = Compra(
        numero_compra=num_cr,
        proveedor_id=prov.id,
        tipo="producto",
        descripcion="Compra a crédito de prueba",
        estado='registrada',
        usuario_registra_id=Usuario.query.first().id,
        fecha_compra=datetime.utcnow(),
        subtotal=0,
        iva=0,
        total=0,
        stock_actualizado=False,
    )
    db.session.add(compra_credito)
    db.session.flush()

    det1 = CompraDetalle(
        compra_id=compra_credito.id,
        producto_id=prod.id,
        cantidad=5,
        precio_unitario=10000,
        subtotal=5*10000,
    )
    db.session.add(det1)

    # Totales con IVA incluido
    total = float(det1.subtotal)
    iva = total / 11.0
    compra_credito.total = total
    compra_credito.iva = iva
    compra_credito.subtotal = total - iva

    # Segunda compra para caja chica
    num_cj = f"C-TEST-CJ-{int(datetime.utcnow().timestamp())}"
    compra_caja = Compra(
        numero_compra=num_cj,
        proveedor_id=prov.id,
        tipo="producto",
        descripcion="Compra caja chica prueba",
        estado='registrada',
        usuario_registra_id=Usuario.query.first().id,
        fecha_compra=datetime.utcnow(),
        subtotal=0,
        iva=0,
        total=0,
        stock_actualizado=False,
    )
    db.session.add(compra_caja)
    db.session.flush()

    det2 = CompraDetalle(
        compra_id=compra_caja.id,
        producto_id=prod.id,
        cantidad=2,
        precio_unitario=20000,
        subtotal=2*20000,
    )
    db.session.add(det2)

    total2 = float(det2.subtotal)
    iva2 = total2 / 11.0
    compra_caja.total = total2
    compra_caja.iva = iva2
    compra_caja.subtotal = total2 - iva2

    db.session.commit()
    return prod, compra_credito, compra_caja


def test_credit_flow(client, compra_id):
    resp = client.post(f"/compras/{compra_id}/pagar", data={
        "origen_pago": "dejar_credito",
        "plazo_credito_dias": "30",
        "observaciones_credito": "Prueba crédito",
    }, follow_redirects=True)
    assert resp.status_code == 200

    compra = Compra.query.get(compra_id)
    assert compra is not None
    assert compra.stock_actualizado is True
    assert compra.estado == 'registrada'

    cxp = CuentaPorPagar.query.filter_by(compra_id=compra_id).first()
    assert cxp is not None
    assert float(cxp.monto_adeudado) == float(compra.total)
    assert cxp.fecha_vencimiento is not None
    print("[OK] Crédito: Stock actualizado y CxP creada con vencimiento.")


def test_caja_chica_flow(client, compra_id):
    from app import db
    apertura = AperturaCaja.query.filter_by(estado='abierto').first()
    disponible_before = float(apertura.monto_final or apertura.monto_inicial or 0)
    compra = Compra.query.get(compra_id)
    monto_a_pagar = min(float(compra.total), 20000)
    resp = client.post(f"/compras/{compra_id}/pagar", data={
        "origen_pago": "caja_chica",
        "monto": str(int(monto_a_pagar)),
        "referencia": "",
    }, follow_redirects=True)
    print(f"Response status: {resp.status_code}")
    # Refresh objects from DB after route commit
    db.session.expire_all()
    pagos = PagoCompra.query.filter_by(compra_id=compra_id).all()
    if len(pagos) == 0:
        print(f"ERROR: No se registró PagoCompra para compra {compra_id}. Abortando.")
        print(f"Compra estado actual: {Compra.query.get(compra_id).estado}")
        import sys
        sys.exit(1)
    apertura = AperturaCaja.query.filter_by(estado='abierto').first()
    disponible_after = float(apertura.monto_final or apertura.monto_inicial or 0)
    expected = int(disponible_before - monto_a_pagar)
    actual = int(disponible_after)
    if actual != expected:
        print(f"ERROR: Caja esperada={expected}, actual={actual}")
        import sys
        sys.exit(1)
    print("[OK] Caja chica: Movimiento y descuento de caja registrados.")


def main():
    app = setup_app()
    with app.app_context():
        user = ensure_user()
        ensure_open_caja()
        prod, compra_credito, compra_caja = create_test_data_producto_compra()

        client = app.test_client()
        # Login
        login_resp = client.post('/auth/login', data={
            'username': 'tester',
            'password': 'password123'
        }, follow_redirects=True)
        assert login_resp.status_code == 200

        # Test credit flow
        stock_before = Producto.query.filter_by(id=prod.id).first().stock_actual
        test_credit_flow(client, compra_credito.id)
        stock_after = Producto.query.filter_by(id=prod.id).first().stock_actual
        assert int(stock_after) == int(stock_before) + 5

        # Re-ensure caja has funds before caja_chica test
        apertura_check = AperturaCaja.query.filter_by(estado='abierto').first()
        print(f"DEBUG main: Antes de caja_chica test, caja disponible={apertura_check.monto_final if apertura_check else 'N/A'}")
        
        # Test caja chica flow
        test_caja_chica_flow(client, compra_caja.id)

        print("Pruebas manuales completadas.")


if __name__ == "__main__":
    main()
