from app.utils.ticket import GeneradorTicket
from app.models import ConfiguracionEmpresa

def generar_nota_credito_ticket_pdf(nota):
    config = ConfiguracionEmpresa.get_config()
    import sys
    print(f"[DEBUG] NotaCredito recibido: {nota}", file=sys.stderr)
    print(f"[DEBUG] Dir(nota): {dir(nota)}", file=sys.stderr)
    try:
        detalles = list(nota.detalles)
        print(f"[DEBUG] detalles extraídos: {detalles}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Al acceder a detalles: {e}", file=sys.stderr)
        raise
    cliente = nota.venta.cliente
    # Creamos un objeto "falso" de venta para el ticket
    class VentaFake:
        def __init__(self, nota, cliente):
            self.numero_factura = nota.numero_nota
            self.fecha_venta = nota.fecha_emision
            self.tipo_venta = 'NOTA DE CRÉDITO'
            self.cliente = cliente
            self.total = nota.monto
            # Envolver cada detalle para exponer descripcion
            self.detalles = [
                DetalleFake(det) for det in detalles
            ]

    class DetalleFake:
        def __init__(self, det):
            self.cantidad = det.cantidad
            self.precio_unitario = det.precio_unitario
            self.subtotal = det.subtotal
            # Buscar descripcion desde VentaDetalle
            self.descripcion = None
            try:
                if hasattr(det, 'venta_detalle_id') and det.venta_detalle_id:
                    from app.models.venta import VentaDetalle
                    vdet = VentaDetalle.query.get(det.venta_detalle_id)
                    if vdet:
                        self.descripcion = vdet.descripcion
            except Exception:
                pass
            if not self.descripcion:
                self.descripcion = getattr(det, 'descripcion', 'Item')
    venta_fake = VentaFake(nota, cliente)
    ticket = GeneradorTicket(config, venta_fake, detalles)
    return ticket.generar_ticket_pdf()
