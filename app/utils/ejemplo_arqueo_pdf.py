from app.utils.base_pdf import PDFReportBase
from app.utils.tabla_pdf import build_pdf_table

def arqueo_caja_pdf(arqueos, empresa):
    # Configuración del reporte
    title = "Reporte de Arqueo de Caja"
    filename = "arqueo_caja.pdf"
    headers = ["N° Arqueo", "Caja", "Cajero", "Fecha Apertura", "Fecha Cierre", "Total", "Estado"]
    col_widths = [80, 80, 100, 110, 110, 80, 80]
    table_data = [headers]
    for a in arqueos:
        table_data.append([
            a.numero_arqueo,
            a.caja.nombre if a.caja else '',
            a.cajero.username if a.cajero else '',
            a.fecha_apertura.strftime('%d/%m/%Y %H:%M') if a.fecha_apertura else '',
            a.fecha_cierre.strftime('%d/%m/%Y %H:%M') if a.fecha_cierre else '',
            f"Gs. {a.total:,.0f}" if a.total else '',
            a.estado.capitalize() if a.estado else ''
        ])
    # Crear reporte base
    pdf = PDFReportBase(empresa, title, filename)
    pdf.add_membrete()
    pdf.add_title()
    pdf.elements.append(build_pdf_table(table_data, col_widths))
    return pdf.build()
