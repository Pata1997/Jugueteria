"""
Utilidades para generar reportes con ReportLab
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from datetime import datetime
from decimal import Decimal


def generar_reporte_arqueo(apertura, totales_esperados, empresa_config, return_elements=False):
    """
    Genera un PDF con el reporte de arqueo de caja
    
    Args:
        apertura: Objeto AperturaCaja
        totales_esperados: Dict con totales esperados
        empresa_config: Configuración de la empresa
    
    Returns:
        BytesIO con el PDF generado
    """
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a3a52'),
        spaceAfter=6,
        alignment=1  # Centrado
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#555555'),
        spaceAfter=4,
        alignment=1  # Centrado
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=8,
        spaceBefore=8,
        bold=True
    )
    
    normal_style = styles['Normal']
    
    # Contenido del documento
    elements = []
    
    # ===== MEMBRETE =====
    elements.append(Paragraph(empresa_config.get('nombre', 'JUGUETERÍA'), title_style))
    elements.append(Paragraph(empresa_config.get('subtitulo', 'El Mundo Feliz'), subtitle_style))
    elements.append(Paragraph(f"RUC: {empresa_config.get('ruc', 'N/A')}", normal_style))
    elements.append(Paragraph(f"{empresa_config.get('direccion', '')}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # ===== TÍTULO DEL REPORTE =====
    elements.append(Paragraph("REPORTE DE ARQUEO DE CAJA", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # ===== DATOS GENERALES =====
    fecha_hora = apertura.fecha_cierre.strftime('%d/%m/%Y %H:%M:%S') if apertura.fecha_cierre else 'N/A'
    
    info_data = [
        ['Caja:', apertura.caja.nombre, 'Cajero:', apertura.cajero.nombre],
        ['Apertura:', apertura.fecha_apertura.strftime('%d/%m/%Y %H:%M:%S'), 'Cierre:', fecha_hora],
    ]
    
    info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # ===== MONTO INICIAL =====
    monto_inicial = apertura.monto_inicial
    elements.append(Paragraph(f"<b>Monto Inicial de Caja:</b> Gs. {monto_inicial:,.0f}", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # ===== TABLA DE TOTALES =====
    # Preparar datos
    efectivo_esperado = totales_esperados.get('efectivo', 0)
    tarjeta_esperado = totales_esperados.get('tarjeta', 0)
    transferencia_esperada = totales_esperados.get('transferencia', 0)
    cheque_esperado = totales_esperados.get('cheque', 0)
    
    efectivo_real = apertura.monto_efectivo_real or 0
    tarjeta_real = apertura.monto_tarjeta_real or 0
    transferencia_real = apertura.monto_transferencias_real or 0
    cheque_real = apertura.monto_cheques_real or 0
    
    total_esperado = efectivo_esperado + tarjeta_esperado + transferencia_esperada + cheque_esperado
    total_real = efectivo_real + tarjeta_real + transferencia_real + cheque_real
    diferencia_total = total_real - total_esperado
    
    # Tabla de comparación
    tabla_data = [
        ['CONCEPTO', 'ESPERADO', 'REAL', 'DIFERENCIA'],
        ['Efectivo', f'Gs. {efectivo_esperado:,.0f}', f'Gs. {efectivo_real:,.0f}', 
         f'Gs. {efectivo_real - efectivo_esperado:,.0f}'],
        ['Tarjetas', f'Gs. {tarjeta_esperado:,.0f}', f'Gs. {tarjeta_real:,.0f}', 
         f'Gs. {tarjeta_real - tarjeta_esperado:,.0f}'],
        ['Transferencias', f'Gs. {transferencia_esperada:,.0f}', f'Gs. {transferencia_real:,.0f}', 
         f'Gs. {transferencia_real - transferencia_esperada:,.0f}'],
        ['Cheques', f'Gs. {cheque_esperado:,.0f}', f'Gs. {cheque_real:,.0f}', 
         f'Gs. {cheque_real - cheque_esperado:,.0f}'],
        ['TOTAL', f'Gs. {total_esperado:,.0f}', f'Gs. {total_real:,.0f}', 
         f'Gs. {diferencia_total:,.0f}'],
    ]
    
    tabla = Table(tabla_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(tabla)
    elements.append(Spacer(1, 0.15*inch))
    
    # ===== ESTADO DEL ARQUEO =====
    if abs(diferencia_total) < 1:
        estado = "ARQUEO CUADRADO ✓"
        color_estado = colors.HexColor('#28a745')
    elif diferencia_total > 0:
        estado = f"SOBRANTE: Gs. {diferencia_total:,.0f}"
        color_estado = colors.HexColor('#ffc107')
    else:
        estado = f"FALTANTE: Gs. {abs(diferencia_total):,.0f}"
        color_estado = colors.HexColor('#dc3545')
    
    estado_style = ParagraphStyle(
        'Estado',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=color_estado,
        spaceAfter=8,
        alignment=1,
        bold=True
    )
    elements.append(Paragraph(estado, estado_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # ===== OBSERVACIONES =====
    if apertura.observaciones:
        elements.append(Paragraph("<b>Observaciones:</b>", heading_style))
        elements.append(Paragraph(apertura.observaciones, normal_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # ===== FIRMA =====
    elements.append(Spacer(1, 0.2*inch))
    firma_data = [
        ['_________________________', '', '_________________________'],
        ['Cajero', '', 'Supervisor'],
        [apertura.cajero.nombre, '', ''],
    ]
    
    firma_table = Table(firma_data, colWidths=[2*inch, 1*inch, 2*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    elements.append(firma_table)
    
    if return_elements:
        return elements
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer