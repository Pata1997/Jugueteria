from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from flask import make_response

class PDFReportBase:
    def __init__(self, empresa, title, filename):
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(self.buffer, pagesize=A4)
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.empresa = empresa
        self.title = title
        self.filename = filename

    def add_membrete(self):
        nombre = getattr(self.empresa, 'nombre_empresa', 'Juguetería') if self.empresa else 'Juguetería'
        ruc = getattr(self.empresa, 'ruc', 'N/A') if self.empresa else 'N/A'
        direccion = getattr(self.empresa, 'direccion', '') if self.empresa else ''
        # Espaciado superior reducido
        self.elements.append(Spacer(1, 10))
        # Membrete con fuente más pequeña y alineado
        membrete_style = ParagraphStyle('Membrete', parent=self.styles['Normal'], fontSize=11, alignment=1, spaceAfter=2)
        self.elements.append(Paragraph(f"<b>{nombre}</b>", membrete_style))
        self.elements.append(Paragraph("El Mundo Feliz", ParagraphStyle('Subtitulo', parent=self.styles['Normal'], fontSize=10, alignment=1, textColor='#888')))
        self.elements.append(Paragraph(f"RUC: {ruc}", membrete_style))
        self.elements.append(Paragraph(direccion, membrete_style))
        self.elements.append(Spacer(1, 8))

    def add_title(self):
        title_style = ParagraphStyle('Title', parent=self.styles['Heading1'], fontSize=17, alignment=1, spaceAfter=10, textColor='#222')
        self.elements.append(Paragraph(self.title, title_style))
        self.elements.append(Spacer(1, 8))

    def add_footer(self):
        from datetime import datetime
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        footer_style = ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=9, alignment=1, textColor='#888', spaceBefore=16)
        self.elements.append(Spacer(1, 16))
        self.elements.append(Paragraph(f"Documento generado el {fecha} | Sistema de Gestión - Juguetería", footer_style))

    def build(self):
        self.add_footer()
        self.doc.build(self.elements)
        self.buffer.seek(0)
        response = make_response(self.buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={self.filename}'
        return response
