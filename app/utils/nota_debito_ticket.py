from app.utils.ticket import GeneradorTicket
from app.models import ConfiguracionEmpresa

def generar_nota_debito_ticket_pdf(nota):
    config = ConfiguracionEmpresa.get_config()
    # Obtener detalles por consulta directa para máxima compatibilidad
    from app.models.nota_debito_detalle import NotaDebitoDetalle
    detalles = NotaDebitoDetalle.query.filter_by(nota_debito_id=nota.id).all()
    cliente = nota.venta.cliente
    # Creamos un objeto "falso" de venta para el ticket
    class VentaFake:
        def __init__(self, nota, cliente):
            self.numero_factura = nota.numero_nota
            self.fecha_venta = nota.fecha_emision
            self.tipo_venta = 'NOTA DE DÉBITO'
            self.cliente = cliente
            self.total = nota.monto
            self.detalles = detalles
    venta_fake = VentaFake(nota, cliente)
    ticket = GeneradorTicket(config, venta_fake, detalles)
    return ticket.generar_ticket_pdf()
