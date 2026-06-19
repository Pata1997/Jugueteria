from datetime import datetime, timedelta
from decimal import Decimal
import random
import sys

from app import create_app, db
from app.models import Cliente, Producto, Usuario, Venta, VentaDetalle


PRODUCTOS_PRUEBA = [
    ("TEST-FAC-001", "Robot articulado de prueba", Decimal("85000")),
    ("TEST-FAC-002", "Bloques didacticos de prueba", Decimal("65000")),
    ("TEST-FAC-003", "Auto a control de prueba", Decimal("120000")),
    ("TEST-FAC-004", "Muneca clasica de prueba", Decimal("95000")),
    ("TEST-FAC-005", "Puzzle familiar de prueba", Decimal("45000")),
]


def obtener_o_crear_usuario():
    usuario = Usuario.query.filter(Usuario.activo.is_(True)).order_by(Usuario.id).first()
    if usuario:
        return usuario

    usuario = Usuario(
        username="admin_prueba",
        email="admin_prueba@example.com",
        nombre="Admin",
        apellido="Prueba",
        rol="admin",
        activo=True,
    )
    usuario.set_password("admin123")
    db.session.add(usuario)
    db.session.flush()
    return usuario


def obtener_o_crear_cliente():
    cliente = Cliente.query.filter_by(numero_documento="80000000-1").first()
    if cliente:
        return cliente

    cliente = Cliente(
        tipo_documento="RUC",
        numero_documento="80000000-1",
        nombre="Cliente Prueba Facturacion",
        tipo_cliente="particular",
        direccion="Direccion de prueba",
        telefono="0981000000",
        email="cliente.prueba@example.com",
        limite_credito=Decimal("0"),
        descuento_especial=Decimal("0"),
        activo=True,
        observaciones="Creado por generar_ventas_para_facturar.py",
    )
    db.session.add(cliente)
    db.session.flush()
    return cliente


def obtener_o_crear_productos():
    productos = []
    for codigo, nombre, precio_venta in PRODUCTOS_PRUEBA:
        producto = Producto.query.filter_by(codigo=codigo).first()
        if not producto:
            producto = Producto(
                codigo=codigo,
                nombre=nombre,
                descripcion="Producto de prueba para generar ventas pendientes",
                tipo_producto="producto",
                unidad_medida="unidad",
                precio_compra=precio_venta * Decimal("0.65"),
                precio_venta=precio_venta,
                tipo_iva="10",
                stock_actual=500,
                stock_minimo=5,
                stock_maximo=1000,
                activo=True,
            )
            db.session.add(producto)
            db.session.flush()
        elif (producto.stock_actual or 0) < 200:
            producto.stock_actual = 500
            producto.activo = True
        productos.append(producto)
    return productos


def siguiente_numero_temporal(indice):
    base = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TMP-{base}-{indice:03d}"


def crear_venta_pendiente(indice, cliente, usuario, productos):
    cantidad_items = random.randint(1, 3)
    seleccionados = random.sample(productos, cantidad_items)

    venta = Venta(
        numero_factura=siguiente_numero_temporal(indice),
        fecha_venta=datetime.utcnow() - timedelta(minutes=indice),
        tipo_venta="producto",
        cliente_id=cliente.id,
        vendedor_id=usuario.id,
        subtotal=Decimal("0"),
        descuento=Decimal("0"),
        iva=Decimal("0"),
        total=Decimal("0"),
        estado="pendiente",
        estado_pago="pendiente",
        dias_credito=0,
        observaciones="Venta de prueba pendiente para facturar",
    )
    db.session.add(venta)
    db.session.flush()

    subtotal_general = Decimal("0")
    iva_general = Decimal("0")

    for producto in seleccionados:
        cantidad = Decimal(random.randint(1, 3))
        precio_unitario = Decimal(producto.precio_venta or 0)
        total_linea = cantidad * precio_unitario
        iva_linea = (total_linea / Decimal("11")).quantize(Decimal("1"))

        detalle = VentaDetalle(
            venta_id=venta.id,
            tipo_item="producto",
            producto_id=producto.id,
            descripcion=producto.nombre,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=total_linea,
            descuento=Decimal("0"),
            total=total_linea,
        )
        db.session.add(detalle)

        subtotal_general += total_linea
        iva_general += iva_linea

    venta.subtotal = subtotal_general
    venta.iva = iva_general
    venta.total = subtotal_general
    return venta


def main():
    cantidad = 30
    if len(sys.argv) > 1:
        cantidad = int(sys.argv[1])
    if cantidad < 30:
        cantidad = 30

    app = create_app()
    with app.app_context():
        cliente = obtener_o_crear_cliente()
        usuario = obtener_o_crear_usuario()
        productos = obtener_o_crear_productos()

        ventas = [
            crear_venta_pendiente(indice, cliente, usuario, productos)
            for indice in range(1, cantidad + 1)
        ]

        db.session.commit()

        print(f"Listo: se crearon {len(ventas)} ventas pendientes para facturar.")
        print("Entrar a: http://127.0.0.1:5000/ventas/")
        print("Numeros temporales:")
        for venta in ventas:
            print(f"- {venta.numero_factura} | total Gs. {int(venta.total):,}")


if __name__ == "__main__":
    main()
