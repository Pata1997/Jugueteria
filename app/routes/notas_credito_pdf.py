from flask import send_file
from flask_login import login_required
from app.models import NotaCredito, Cliente, ConfiguracionEmpresa, NotaCreditoDetalle
from app.utils.nota_credito_ticket import GeneradorTicket
from app import db
from io import BytesIO
from flask import Blueprint

bp = Blueprint('notas_credito_pdf', __name__)

@bp.route('/ventas/notas-credito/pdf/<int:nota_id>')
@login_required
def descargar_nota_credito_pdf(nota_id):
    nota = NotaCredito.query.get_or_404(nota_id)
    cliente = Cliente.query.get(nota.venta.cliente_id)
    import sys
    detalles = NotaCreditoDetalle.query.filter_by(nota_credito_id=nota.id).all()
    print(f"[DEBUG] Detalles obtenidos: {detalles}", file=sys.stderr)
    detalles = NotaCreditoDetalle.query.filter_by(nota_credito_id=nota.id).all()
    config = ConfiguracionEmpresa.get_config()
    cliente = Cliente.query.get(nota.venta.cliente_id)
    # Crear objeto fake para el ticket
    # Envolver detalles para exponer descripción
    class DetalleFake:
        def __init__(self, det):
            self.cantidad = det.cantidad
            self.precio_unitario = det.precio_unitario
            self.subtotal = det.subtotal
            # Buscar descripción desde VentaDetalle
            self.descripcion = None
            try:
                from app.models.venta import VentaDetalle
                vdet = VentaDetalle.query.get(det.venta_detalle_id)
                if vdet:
                    self.descripcion = vdet.descripcion
            except Exception:
                pass
            if not self.descripcion:
                self.descripcion = getattr(det, 'descripcion', 'Item')
    detalles_ticket = []
    for det in detalles:
        fake = DetalleFake(det)
        print(f"[DEBUG] DetalleFake: desc={fake.descripcion}, cant={fake.cantidad}, precio={fake.precio_unitario}, subtotal={fake.subtotal}", file=sys.stderr)
        detalles_ticket.append(fake)
    class VentaFake:
        def __init__(self, nota, cliente, detalles):
            self.numero_factura = nota.numero_nota
            self.fecha_venta = nota.fecha_emision
            self.tipo_venta = 'NOTA DE CRÉDITO'
            self.cliente = cliente
            self.total = nota.monto
            self.detalles = detalles
    venta_fake = VentaFake(nota, cliente, detalles_ticket)
    ticket = GeneradorTicket(config, venta_fake, detalles_ticket)
    pdf_bytes = ticket.generar_ticket_pdf()
    from io import BytesIO
    pdf_buffer = BytesIO(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'nota_credito_{nota.numero_nota}.pdf'
    )
