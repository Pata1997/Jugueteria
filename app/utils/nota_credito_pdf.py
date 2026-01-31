# Función de utilidad para el endpoint
def generar_nota_credito_pdf(nota):
    from app.models import ConfiguracionEmpresa
    config = ConfiguracionEmpresa.get_config()
    detalles = nota.detalles.all() if hasattr(nota.detalles, 'all') else nota.detalles
    cliente = nota.venta.cliente
    generador = GeneradorNotaCreditoPDF(config, nota, detalles, cliente)
    pdf_buffer = generador.generar_pdf()
    return pdf_buffer.getvalue()
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
from datetime import datetime

class GeneradorNotaCreditoPDF:
    def __init__(self, config_empresa, nota_credito, detalles, cliente):
        self.config = config_empresa
        self.nota = nota_credito
        self.detalles = detalles
        self.cliente = cliente

    def generar_pdf(self):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 40
        x_margin = 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x_margin, y, self.config.nombre_empresa)
        y -= 25
        c.setFont("Helvetica", 10)
        c.drawString(x_margin, y, f"RUC: {self.config.ruc}")
        y -= 15
        c.drawString(x_margin, y, f"Dirección: {self.config.direccion}")
        y -= 15
        c.drawString(x_margin, y, f"Tel: {self.config.telefono}")
        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_margin, y, "NOTA DE CRÉDITO")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(x_margin, y, f"N°: {self.nota.numero_nota}")
        y -= 15
        c.drawString(x_margin, y, f"Fecha: {self.nota.fecha_emision.strftime('%d/%m/%Y')}")
        y -= 15
        c.drawString(x_margin, y, f"Cliente: {self.cliente.nombre}")
        y -= 15
        c.drawString(x_margin, y, f"Motivo: {self.nota.motivo}")
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_margin, y, "Detalle:")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(x_margin, y, "Descripción")
        c.drawString(x_margin+200, y, "Cant.")
        c.drawString(x_margin+250, y, "Precio")
        c.drawString(x_margin+320, y, "Subtotal")
        y -= 12
        c.line(x_margin, y, width-x_margin, y)
        y -= 10
        total = 0
        for det in self.detalles:
            desc = getattr(det, 'descripcion', getattr(det, 'producto', None)) or '-'
            c.drawString(x_margin, y, str(desc))
            c.drawString(x_margin+200, y, str(det.cantidad))
            c.drawString(x_margin+250, y, f"Gs. {int(det.precio_unitario):,}")
            c.drawString(x_margin+320, y, f"Gs. {int(det.subtotal):,}")
            total += float(det.subtotal)
            y -= 12
        y -= 10
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_margin+250, y, "Total:")
        c.drawString(x_margin+320, y, f"Gs. {int(total):,}")
        y -= 20
        c.setFont("Helvetica", 9)
        c.drawString(x_margin, y, f"Observaciones: {self.nota.observaciones or ''}")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
