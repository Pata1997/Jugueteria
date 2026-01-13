

from flask import Blueprint, render_template, request, make_response, redirect, url_for, flash, jsonify
from flask_login import login_required
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from app import db
from app.models import Compra, Proveedor, Venta, Producto, Cliente, ConfiguracionEmpresa, OrdenServicio, AperturaCaja, Caja, Usuario

# =====================================================
# BLUEPRINT
# =====================================================
bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# =====================================================
# REPORTE FINANCIERO MENSUAL (PDF)
# =====================================================
@bp.route('/financiero/pdf')
@login_required
def financiero_pdf():
    from app.utils.base_pdf import PDFReportBase
    from app.utils.tabla_pdf import build_pdf_table
    from datetime import date, datetime, timedelta
    empresa = ConfiguracionEmpresa.query.first()
    # Parámetros de mes
    hoy = date.today()
    mes = int(request.args.get('mes', hoy.month))
    anio = int(request.args.get('anio', hoy.year))
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    # Ventas completadas en el mes
    ventas = Venta.query.filter(
        Venta.fecha_venta >= fecha_inicio,
        Venta.fecha_venta <= fecha_fin,
        Venta.estado == 'completada'
    ).all()
    total_ventas = sum(float(v.total) for v in ventas)
    # Compras pagadas en el mes
    compras = Compra.query.filter(
        Compra.fecha_compra >= fecha_inicio,
        Compra.fecha_compra <= fecha_fin,
        Compra.estado.in_(['pagada'])
    ).all()
    total_compras = sum(float(c.total) for c in compras)
    # Compras pendientes/parcial en el mes (informativo)
    compras_pendientes = Compra.query.filter(
        Compra.fecha_compra >= fecha_inicio,
        Compra.fecha_compra <= fecha_fin,
        Compra.estado.in_(['registrada', 'parcial_pagada'])
    ).all()
    total_pendientes = sum(float(c.total) for c in compras_pendientes)
    ganancia = total_ventas - total_compras
    resultado = 'GANANCIA' if ganancia >= 0 else 'PÉRDIDA'
    resultado_es = 'GANANCIA' if ganancia >= 0 else 'PÉRDIDA'
    # Mes en español
    meses_es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    mes_nombre = meses_es[mes-1].capitalize()
    # PDF armado
    pdf = PDFReportBase(empresa, f"Balance Financiero {mes_nombre} {anio}", f"balance_financiero_{anio}_{mes:02d}.pdf")
    pdf.add_membrete()
    pdf.add_title()
    resumen = f"<b>Período:</b> {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}<br/>"
    resumen += f"<b>Total vendido:</b> Gs. {total_ventas:,.0f}<br/>"
    resumen += f"<b>Total gastado:</b> Gs. {total_compras:,.0f}<br/>"
    resumen += f"<b>Compras pendientes de pago (informativo):</b> Gs. {total_pendientes:,.0f}<br/>"
    resumen += f"<b>Resultado:</b> <font color='{'green' if ganancia >= 0 else 'red'}'><b>{resultado_es}</b></font> Gs. {ganancia:,.0f}"
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    pdf.elements.append(Paragraph(resumen, styles['Normal']))
    pdf.elements.append(Spacer(1, 16))
    # Tabla detalle
    headers = ["Concepto", "Monto (Gs.)"]
    col_widths = [200, 150]
    table_data = [headers]
    table_data.append(["Total vendido", f"Gs. {total_ventas:,.0f}"])
    table_data.append(["Total gastado", f"Gs. {total_compras:,.0f}"])
    table_data.append(["Compras pendientes de pago", f"Gs. {total_pendientes:,.0f}"])
    table_data.append([resultado_es, f"Gs. {ganancia:,.0f}"])
    pdf.elements.append(build_pdf_table(table_data, col_widths, header_color='#8e44ad'))
    return pdf.build()



# =====================================================
# REPORTE DE COMPRAS (PDF)
# =====================================================
@bp.route('/compras/pdf')
@login_required
def compras_pdf():
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    query = Compra.query
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Compra.fecha_compra >= fecha_desde_dt)
        except Exception:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Compra.fecha_compra <= fecha_hasta_dt)
        except Exception:
            pass
    compras = query.all()
    from app.utils.base_pdf import PDFReportBase
    from app.utils.tabla_pdf import build_pdf_table
    empresa = ConfiguracionEmpresa.query.first()
    headers = ["N° Compra", "Proveedor", "Fecha", "Total", "Estado"]
    # Ajuste para A4: suma total ~500 puntos
    col_widths = [80, 140, 80, 100, 100]
    table_data = [headers]
    for c in compras:
        proveedor = c.proveedor.razon_social if c.proveedor else ''
        fecha = c.fecha_compra.strftime('%d/%m/%Y') if c.fecha_compra else ''
        total = f"Gs. {c.total:,.0f}" if c.total else ''
        estado = c.estado.capitalize() if c.estado else ''
        table_data.append([
            c.numero_compra,
            proveedor,
            fecha,
            total,
            estado
        ])
    pdf = PDFReportBase(empresa, "Reporte de Compras", "reporte_compras.pdf")
    pdf.add_membrete()
    pdf.add_title()
    # Usar fuente más pequeña en la tabla para mayor contenido
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    pdf.elements.append(table)
    return pdf.build()

# =====================================================
# REPORTE DE COMPRAS PENDIENTES DE PAGO (PDF)
# =====================================================
@bp.route('/compras-pendientes-pago/pdf')
@login_required
def compras_pendientes_pago_pdf():
    # Match web view: show compras with estado 'registrada' or 'parcial_pagada'
    query = Compra.query.filter(Compra.estado.in_(['registrada', 'parcial_pagada']))
    compras = query.all()
    from app.utils.base_pdf import PDFReportBase
    from app.utils.tabla_pdf import build_pdf_table
    empresa = ConfiguracionEmpresa.query.first()
    headers = ["N° Compra", "Proveedor", "Fecha", "Total", "Saldo Pendiente", "Estado"]
    # Ajuste para A4: suma total ~500 puntos
    col_widths = [70, 120, 70, 80, 80, 80]
    table_data = [headers]
    for c in compras:
        proveedor = c.proveedor.razon_social if c.proveedor else ''
        fecha = c.fecha_compra.strftime('%d/%m/%Y') if c.fecha_compra else ''
        total = f"Gs. {c.total:,.0f}" if c.total else ''
        saldo_pendiente = c.monto_pendiente() if hasattr(c, 'monto_pendiente') else ''
        saldo = f"Gs. {saldo_pendiente:,.0f}" if saldo_pendiente else ''
        estado = c.estado.capitalize() if c.estado else ''
        table_data.append([
            c.numero_compra,
            proveedor,
            fecha,
            total,
            saldo,
            estado
        ])
    pdf = PDFReportBase(empresa, "Compras Pendientes de Pago", "compras_pendientes_pago.pdf")
    pdf.add_membrete()
    pdf.add_title()
    # Usar fuente más pequeña en la tabla para mayor contenido
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    pdf.elements.append(table)
    return pdf.build()

# =====================================================
# SERVICIOS POR FECHA Y PRIORIDAD (PDF)
# =====================================================
@bp.route('/servicios/pdf')
@login_required
def servicios_pdf():
    from app.models import Venta, OrdenServicio
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    # Filtro de fechas

    # Mostrar todas las fechas de ordenes existentes sin filtro
    from app.models import OrdenServicio
    todas_ordenes = OrdenServicio.query.all()
    print(f"[DEBUG] Fechas de TODAS las ordenes de servicio en la base de datos:")
    for o in todas_ordenes:
        print(f"  - {o.numero_orden}: {o.fecha_orden} (type: {type(o.fecha_orden)})")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    empresa = ConfiguracionEmpresa.query.first()
    nombre = empresa.nombre_empresa if empresa else 'Juguetería'
    ruc = empresa.ruc if empresa else 'N/A'
    from app.utils.base_pdf import PDFReportBase
    from app.utils.tabla_pdf import build_pdf_table
    direccion = empresa.direccion if empresa else ''
    from app.models import Venta, SolicitudServicio
    query = SolicitudServicio.query
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(SolicitudServicio.fecha_solicitud >= fecha_desde_dt)
        except Exception:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(SolicitudServicio.fecha_solicitud <= fecha_hasta_dt)
        except Exception:
            pass
    solicitudes = query.all()
    headers = ["N° Solicitud", "Prioridad", "Precio", "Fecha Estimada", "Estado"]
    col_widths = [110, 90, 110, 110, 110]
    table_data = [headers]
    for s in solicitudes:
        prioridad = s.prioridad.capitalize() if s.prioridad else ''
        precio = s.total_estimado if s.total_estimado else ''
        fecha_estimada = s.fecha_estimada.strftime('%d/%m/%Y') if s.fecha_estimada else ''
        estado = s.estado.capitalize() if s.estado else ''
        table_data.append([
            s.numero_solicitud,
            prioridad,
            f"Gs. {precio:,.0f}" if precio else '',
            fecha_estimada,
            estado
        ])
    pdf = PDFReportBase(empresa, "Servicios por Fecha y Prioridad", "servicios_por_fecha.pdf")
    pdf.add_membrete()
    pdf.add_title()
    pdf.elements.append(build_pdf_table(table_data, col_widths, header_color='#3498db'))
    return pdf.build()
# Endpoint para buscar aperturas de caja cerradas por fecha (AJAX)
@bp.route('/cajas-cerradas')
@login_required
def cajas_cerradas():
    from datetime import datetime, timedelta
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify([])
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
    except Exception:
        return jsonify([])
    dia_siguiente = fecha_dt + timedelta(days=1)
    aperturas = AperturaCaja.query.filter(
        AperturaCaja.fecha_apertura >= fecha_dt,
        AperturaCaja.fecha_apertura < dia_siguiente,
        AperturaCaja.estado == 'cerrada'
    ).all()
    resultado = []
    for a in aperturas:
        resultado.append({
            'id': a.id,
            'caja': a.caja.nombre if a.caja else '',
            'cajero': a.cajero.username if a.cajero else '',
            'fecha_apertura': a.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
            'fecha_cierre': a.fecha_cierre.strftime('%d/%m/%Y %H:%M') if a.fecha_cierre else '',
        })
    return jsonify(resultado)

# =====================================================
# HELPERS PDF
# =====================================================
def membrete(elements, styles, empresa: ConfiguracionEmpresa | None):
    nombre = empresa.nombre_empresa if empresa else 'JUGUETERÍA'
    ruc = empresa.ruc if empresa else 'N/A'
    direccion = empresa.direccion if empresa else ''

    elements.append(Paragraph(f"<b>{nombre}</b>", styles['Title']))
    elements.append(Paragraph("El Mundo Feliz", styles['Normal']))
    elements.append(Paragraph(f"RUC: {ruc}", styles['Normal']))
    elements.append(Paragraph(direccion, styles['Normal']))
    elements.append(Spacer(1, 12))


# =====================================================
# INDEX REPORTES
# =====================================================
@bp.route('/')
@login_required
def index():
    print("[DEBUG] Ejecutando reportes.index")
    return render_template('reportes/index.html')


# =====================================================
# REPORTES DE VENTAS (HTML)
# =====================================================
@bp.route('/ventas')
@login_required
def ventas():
    fecha_desde = request.args.get(
        'fecha_desde',
        (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )
    fecha_hasta = request.args.get(
        'fecha_hasta',
        datetime.now().strftime('%Y-%m-%d')
    )

    ventas = Venta.query.filter(
        Venta.fecha_venta >= fecha_desde,
        Venta.fecha_venta <= fecha_hasta,
        Venta.estado == 'completada'
    ).all()

    total = sum(v.total for v in ventas)

    return render_template(
        'reportes/ventas.html',
        ventas=ventas,
        total=total,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


# =====================================================
# REPORTES DE VENTAS (PDF)
# =====================================================
@bp.route('/ventas/pdf')
@login_required
def ventas_pdf():

    from datetime import datetime, date, timedelta
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    hoy = date.today()
    # Si no se especifica, usar el mes actual
    if not fecha_desde:
        fecha_desde_dt = hoy.replace(day=1)
        fecha_desde = fecha_desde_dt.strftime('%Y-%m-%d')
    else:
        fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
    if not fecha_hasta:
        # último día del mes actual
        next_month = hoy.replace(day=28) + timedelta(days=4)
        fecha_hasta_dt = next_month - timedelta(days=next_month.day)
        fecha_hasta = fecha_hasta_dt.strftime('%Y-%m-%d')
    else:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')

    query = Venta.query
    query = query.filter(Venta.fecha_venta >= fecha_desde_dt)
    query = query.filter(Venta.fecha_venta <= fecha_hasta_dt)
    query = query.filter(Venta.estado == 'completada')
    ventas = query.all()

    empresa = ConfiguracionEmpresa.query.first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor('#2c3e50'),
        backColor=colors.HexColor('#f4f6f7'),
    )

    membrete(elements, styles, empresa)

    # Traducir mes al español
    meses_es = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]
    periodo_str = f"{fecha_desde_dt.strftime('%d/%m/%Y')} al {fecha_hasta_dt.strftime('%d/%m/%Y')}"
    if fecha_desde_dt.day == 1 and fecha_hasta_dt.day in [28,29,30,31] and fecha_desde_dt.month == fecha_hasta_dt.month:
        mes = meses_es[fecha_desde_dt.month - 1]
        periodo_str = f"{mes.capitalize()} {fecha_desde_dt.year}"

    # Encabezado de período mejorado
    elements.append(
        Paragraph(
            f"<b>Reporte de Ventas</b>", title_style
        )
    )
    elements.append(Spacer(1, 8))
    periodo_style = ParagraphStyle(
        'Periodo', parent=styles['Normal'], fontSize=14, alignment=1,
        textColor=colors.HexColor('#2980b9'), spaceAfter=12
    )
    elements.append(Paragraph(f"Período: {periodo_str}", periodo_style))
    elements.append(Spacer(1, 10))

    # Ajustar ancho de columnas para que no se salga el texto
    data = [['Factura', 'Fecha', 'Cliente', 'Total']]
    for v in ventas:
        data.append([
            v.numero_factura,
            v.fecha_venta.strftime('%d/%m/%Y'),
            v.cliente.nombre[:30],
            f"Gs. {v.total:,.0f}"
        ])

    total = sum(v.total for v in ventas)
    data.append(['', '', 'TOTAL', f"Gs. {total:,.0f}"])

    table = Table(data, colWidths=[120, 70, 180, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#34495e')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f9e79f')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2c3e50')),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=reporte_ventas_{fecha_desde}_{fecha_hasta}.pdf'
    )
    return response


# =====================================================
# REPORTES DE PRODUCTOS
# =====================================================
@bp.route('/productos')
@login_required
def productos():
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('reportes/productos.html', productos=productos)


@bp.route('/productos-stock-bajo')
@login_required
def productos_stock_bajo():
    productos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo.is_(True)
    ).all()
    return render_template(
        'reportes/productos_stock_bajo.html',
        productos=productos
    )


# =====================================================
# PRODUCTOS CON STOCK BAJO (PDF)
# =====================================================
@bp.route('/productos-stock-bajo/pdf')
@login_required
def productos_stock_bajo_pdf():
    from app.utils.base_pdf import PDFReportBase
    from app.utils.tabla_pdf import build_pdf_table
    productos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo.is_(True)
    ).all()
    empresa = ConfiguracionEmpresa.query.first()
    headers = ["Código", "Nombre", "Stock Actual", "Stock Mínimo"]
    col_widths = [90, 260, 90, 90]
    table_data = [headers]
    for p in productos:
        table_data.append([
            p.codigo,
            p.nombre,
            str(p.stock_actual),
            str(p.stock_minimo)
        ])
    pdf = PDFReportBase(empresa, "Productos con Stock Bajo", "productos_stock_bajo.pdf")
    pdf.add_membrete()
    pdf.add_title()
    pdf.elements.append(build_pdf_table(table_data, col_widths, header_color='#e74c3c'))
    return pdf.build()

# =====================================================
# REPORTES DE SERVICIOS
# =====================================================
@bp.route('/servicios')
@login_required
def servicios():
    fecha_desde = request.args.get(
        'fecha_desde',
        (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )
    fecha_hasta = request.args.get(
        'fecha_hasta',
        datetime.now().strftime('%Y-%m-%d')
    )

    ordenes = OrdenServicio.query.filter(
        OrdenServicio.fecha_orden >= fecha_desde,
        OrdenServicio.fecha_orden <= fecha_hasta
    ).all()

    return render_template(
        'reportes/servicios.html',
        ordenes=ordenes,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


# =====================================================
# REPORTES DE CLIENTES
# =====================================================
@bp.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.filter_by(activo=True).all()

    datos = []
    for c in clientes:
        ventas = [v for v in c.ventas if v.estado == 'completada']
        datos.append({
            'cliente': c,
            'cantidad': len(ventas),
            'total': sum(v.total for v in ventas)
        })

    datos.sort(key=lambda x: x['total'], reverse=True)

    return render_template('reportes/clientes.html', datos_clientes=datos)


# =====================================================
# FACTURA PDF
# =====================================================
@bp.route('/factura/<int:venta_id>/pdf')
@login_required
def factura_pdf(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    empresa = ConfiguracionEmpresa.get_config()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, height - 40, "FACTURA")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, empresa.nombre_empresa)
    c.drawString(50, height - 95, f"RUC: {empresa.ruc}")
    c.drawString(50, height - 110, empresa.direccion or "")

    # Datos factura
    c.drawString(400, height - 80, f"N°: {venta.numero_factura}")
    c.drawString(400, height - 95, venta.fecha_venta.strftime('%d/%m/%Y'))

    # Cliente
    c.drawString(50, height - 150, f"Cliente: {venta.cliente.nombre}")
    c.drawString(50, height - 165, f"Doc: {venta.cliente.numero_documento}")

    # Detalles
    y = height - 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Cant.")
    c.drawString(100, y, "Descripción")
    c.drawString(400, y, "Precio")
    c.drawString(500, y, "Total")

    y -= 20
    c.setFont("Helvetica", 10)

    for d in venta.detalles:
        c.drawString(50, y, str(int(d.cantidad)))
        c.drawString(100, y, d.descripcion[:40])
        c.drawRightString(470, y, f"{d.precio_unitario:,.0f}")
        c.drawRightString(570, y, f"{d.total:,.0f}")
        y -= 18

    # Totales
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(470, y, "TOTAL:")
    c.drawRightString(570, y, f"Gs. {venta.total:,.0f}")

    c.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        f'inline; filename=factura_{venta.numero_factura}.pdf'
    )
    return response


# =====================================================
# REPORTES PDF PERSONALIZADOS
# =====================================================
@bp.route('/ventas-cliente/pdf')
@login_required
def ventas_cliente_pdf():
    ventas = Venta.query.filter(Venta.estado == 'completada').all()
    clientes = {}
    for v in ventas:
        nombre = v.cliente.nombre
        if nombre not in clientes:
            clientes[nombre] = {'cantidad': 0, 'total': 0}
        clientes[nombre]['cantidad'] += 1
        clientes[nombre]['total'] += v.total
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    membrete(elements, styles, ConfiguracionEmpresa.query.first())
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=16)
    elements.append(Paragraph("Reporte de Ventas por Cliente", title_style))
    elements.append(Spacer(1, 12))
    table_data = [['Cliente', 'Cantidad de Compras', 'Total Comprado']]
    for nombre, info in sorted(clientes.items(), key=lambda x: x[1]['total'], reverse=True):
        table_data.append([nombre, info['cantidad'], f"Gs. {info['total']:,.0f}"])
    table = Table(table_data, colWidths=[320, 150, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=ventas_cliente.pdf'
    return response

@bp.route('/productos-mas-vendidos/pdf')
@login_required
def productos_mas_vendidos_pdf():
    ventas = Venta.query.filter(Venta.estado == 'completada').all()
    productos = {}
    for v in ventas:
        for d in v.detalles:
            nombre = d.descripcion
            if nombre not in productos:
                productos[nombre] = {'cantidad': 0, 'total': 0}
            productos[nombre]['cantidad'] += d.cantidad
            productos[nombre]['total'] += d.total
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    membrete(elements, styles, ConfiguracionEmpresa.query.first())
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=16)
    elements.append(Paragraph("Productos Más Vendidos", title_style))
    elements.append(Spacer(1, 12))
    table_data = [['Producto', 'Cantidad Vendida', 'Total Vendido']]
    for nombre, info in sorted(productos.items(), key=lambda x: x[1]['cantidad'], reverse=True):
        table_data.append([nombre, int(info['cantidad']), f"Gs. {info['total']:,.0f}"])
    table = Table(table_data, colWidths=[200, 120, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=productos_mas_vendidos.pdf'
    return response

@bp.route('/ventas-diarias/pdf')
@login_required
def ventas_diarias_pdf():
    desde = request.args.get('desde')
    from datetime import datetime, timedelta
    desde_dt = None
    if desde:
        try:
            desde_dt = datetime.strptime(desde, '%Y-%m-%d')
        except Exception:
            desde_dt = None

    query = Venta.query
    if desde_dt:
        # Filtrar solo ese día
        dia_siguiente = desde_dt + timedelta(days=1)
        query = query.filter(Venta.fecha_venta >= desde_dt)
        query = query.filter(Venta.fecha_venta < dia_siguiente)
    query = query.filter(Venta.estado == 'completada')
    ventas = query.all()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    membrete(elements, styles, ConfiguracionEmpresa.query.first())
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=16)
    fecha_str = desde_dt.strftime('%d/%m/%Y') if desde_dt else ''
    elements.append(Paragraph(f"Arqueo de Caja ({fecha_str})", title_style))
    elements.append(Spacer(1, 12))
    table_data = [['Fecha', 'Nro. Factura', 'Cliente', 'Total']]
    for v in ventas:
        table_data.append([
            v.fecha_venta.strftime('%d/%m/%Y'),
            v.numero_factura,
            v.cliente.nombre[:30],
            f"Gs. {v.total:,.0f}"
        ])
    table = Table(table_data, colWidths=[90, 90, 200, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_caja_{desde}.pdf'
    return response

@bp.route('/ventas-periodo/pdf')
@login_required
def ventas_periodo_pdf():
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    ventas = Venta.query.filter(
        Venta.fecha_venta >= desde,
        Venta.fecha_venta <= hasta,
        Venta.estado == 'completada'
    ).all()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    membrete(elements, styles, ConfiguracionEmpresa.query.first())
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=16)
    elements.append(Paragraph(f"Ventas por Período ({desde} a {hasta})", title_style))
    elements.append(Spacer(1, 12))
    table_data = [['Semana', 'Total']]
    ventas_por_semana = {}
    for v in ventas:
        semana_key = v.fecha_venta.strftime('%Y-%U')
        ventas_por_semana.setdefault(semana_key, 0)
        ventas_por_semana[semana_key] += v.total
    for k, total in ventas_por_semana.items():
        table_data.append([f"Semana {k}", f"Gs. {total:,.0f}"])
    table = Table(table_data, colWidths=[200, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ventas_periodo_{desde}_{hasta}.pdf'
    return response
