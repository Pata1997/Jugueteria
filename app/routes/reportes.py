from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required
from app import db
from app.models import Venta, Compra, Producto, Cliente, AperturaCaja
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from io import BytesIO

bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# ===== REPORTES DE CAJA =====
@bp.route('/caja-dia/pdf')
@login_required
def caja_dia_pdf():
    fecha = request.args.get('fecha')
    if not fecha:
        flash('Debe seleccionar una fecha', 'danger')
        return redirect(url_for('reportes.index'))

    # Buscar aperturas de caja para la fecha
    apertura = AperturaCaja.query.filter(
        db.func.date(AperturaCaja.fecha_apertura) == fecha
    ).first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("Reporte de Caja por Día", title_style))
    elements.append(Paragraph(f"Fecha: {fecha}", styles['Normal']))
    elements.append(Spacer(1, 20))

    if apertura:
        data = [
            ['Fecha Apertura', apertura.fecha_apertura.strftime('%d/%m/%Y %H:%M')],
            ['Monto Inicial', f"Gs. {apertura.monto_inicial:,.0f}"],
            ['Monto Final', f"Gs. {apertura.monto_final:,.0f}" if apertura.monto_final else ''],
            ['Estado', apertura.estado],
        ]
        table = Table(data, colWidths=[150, 220])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No se encontró apertura de caja para la fecha seleccionada.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_caja_{fecha}.pdf'
    return response

from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required
from app import db
from app.models import Venta, Compra, Producto, Cliente, AperturaCaja
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from io import BytesIO

bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# ===== REPORTES PERSONALIZADOS SOLICITADOS =====
@bp.route('/valoracion-inventario')
@login_required
def valoracion_inventario():
    return render_template('reportes/reporte_base.html', titulo='Valoración de Inventario')

@bp.route('/movimientos-inventario')
@login_required
def movimientos_inventario():
    return render_template('reportes/reporte_base.html', titulo='Movimientos de Inventario')

@bp.route('/kardex-producto')
@login_required
def kardex_producto():
    return render_template('reportes/reporte_base.html', titulo='Kardex por Producto')

@bp.route('/servicios-por-tecnico')
@login_required
def servicios_por_tecnico():
    return render_template('reportes/reporte_base.html', titulo='Servicios por Técnico')

@bp.route('/cuentas-por-cobrar', endpoint='reportes_cuentas_por_cobrar')
@login_required
def reportes_cuentas_por_cobrar():
    return render_template('reportes/reporte_base.html', titulo='Cuentas por Cobrar')

@bp.route('/stock-actual', endpoint='reportes_stock_actual')
@login_required
def reportes_stock_actual():
    return render_template('reportes/reporte_base.html', titulo='Stock Actual')

@bp.route('/servicios-realizados', endpoint='reportes_servicios_realizados')
@login_required
def reportes_servicios_realizados():
    return render_template('reportes/reporte_base.html', titulo='Servicios Realizados')

@bp.route('/servicios-pendientes', endpoint='reportes_servicios_pendientes')
@login_required
def reportes_servicios_pendientes():
    return render_template('reportes/reporte_base.html', titulo='Servicios Pendientes')

@bp.route('/reclamos', endpoint='reportes_reclamos')
@login_required
def reportes_reclamos():
    return render_template('reportes/reporte_base.html', titulo='Reclamos')

@bp.route('/compras-por-periodo', endpoint='reportes_compras_por_periodo')
@login_required
def reportes_compras_por_periodo():
    return render_template('reportes/reporte_base.html', titulo='Compras por Período')

@bp.route('/compras-por-proveedor', endpoint='reportes_compras_por_proveedor')
@login_required
def reportes_compras_por_proveedor():
    return render_template('reportes/reporte_base.html', titulo='Compras por Proveedor')

@bp.route('/cuentas-por-pagar', endpoint='reportes_cuentas_por_pagar')
@login_required
def reportes_cuentas_por_pagar():
    return render_template('reportes/reporte_base.html', titulo='Cuentas por Pagar')

@bp.route('/pedidos-pendientes', endpoint='reportes_pedidos_pendientes')
@login_required
def reportes_pedidos_pendientes():
    return render_template('reportes/reporte_base.html', titulo='Pedidos Pendientes')

@bp.route('/')
@login_required
def index():
    return render_template('reportes/index.html')

# ===== REPORTES DE VENTAS =====
@bp.route('/ventas')
@login_required
def ventas():
    fecha_desde = request.args.get('fecha_desde', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_hasta = request.args.get('fecha_hasta', datetime.now().strftime('%Y-%m-%d'))
    
    ventas = Venta.query.filter(
        Venta.fecha_venta >= fecha_desde,
        Venta.fecha_venta <= fecha_hasta,
        Venta.estado == 'completada'
    ).all()
    
    total = sum(v.total for v in ventas)
    
    return render_template('reportes/ventas.html', 
                         ventas=ventas, 
                         total=total,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

@bp.route('/ventas/pdf')
@login_required
def ventas_pdf():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    ventas = Venta.query.filter(
        Venta.fecha_venta >= fecha_desde,
        Venta.fecha_venta <= fecha_hasta,
        Venta.estado == 'completada'
    ).all()
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1
    )
    
    # Título
    elements.append(Paragraph("Reporte de Ventas", title_style))
    elements.append(Paragraph(f"Período: {fecha_desde} al {fecha_hasta}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Tabla
    data = [['Nro. Factura', 'Fecha', 'Cliente', 'Total']]
    for v in ventas:
        data.append([
            v.numero_factura,
            v.fecha_venta.strftime('%d/%m/%Y'),
            v.cliente.nombre[:30],
            f"Gs. {v.total:,.0f}"
        ])
    
    total = sum(v.total for v in ventas)
    data.append(['', '', 'TOTAL:', f"Gs. {total:,.0f}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_ventas_{fecha_desde}_{fecha_hasta}.pdf'
    
    return response

# ===== REPORTES DE PRODUCTOS =====
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
        Producto.activo == True
    ).all()
    
    return render_template('reportes/productos_stock_bajo.html', productos=productos)

# ===== REPORTES DE SERVICIOS =====
@bp.route('/servicios')
@login_required
def servicios():
    fecha_desde = request.args.get('fecha_desde', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_hasta = request.args.get('fecha_hasta', datetime.now().strftime('%Y-%m-%d'))
    
    from app.models import OrdenServicio
    ordenes = OrdenServicio.query.filter(
        OrdenServicio.fecha_orden >= fecha_desde,
        OrdenServicio.fecha_orden <= fecha_hasta
    ).all()
    
    return render_template('reportes/servicios.html', 
                         ordenes=ordenes,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

# ===== REPORTES DE CLIENTES =====
@bp.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.filter_by(activo=True).all()
    
    # Calcular ventas por cliente
    datos_clientes = []
    for cliente in clientes:
        total_compras = sum(v.total for v in cliente.ventas if v.estado == 'completada')
        datos_clientes.append({
            'cliente': cliente,
            'total_compras': total_compras,
            'cantidad_compras': cliente.ventas.filter_by(estado='completada').count()
        })
    
    # Ordenar por total
    datos_clientes.sort(key=lambda x: x['total_compras'], reverse=True)
    
    return render_template('reportes/clientes.html', datos_clientes=datos_clientes)

# ===== FACTURA PDF =====
@bp.route('/factura/<int:venta_id>/pdf')
@login_required
def factura_pdf(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, height - 50, "FACTURA")
    
    # Información de la empresa
    from app.models import ConfiguracionEmpresa
    config = ConfiguracionEmpresa.get_config()
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, config.nombre_empresa)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 115, f"RUC: {config.ruc}")
    c.drawString(50, height - 130, f"Dirección: {config.direccion or ''}")
    c.drawString(50, height - 145, f"Teléfono: {config.telefono or ''}")
    
    # Información de la factura
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, height - 100, f"Factura Nº: {venta.numero_factura}")
    c.setFont("Helvetica", 10)
    c.drawString(400, height - 115, f"Fecha: {venta.fecha_venta.strftime('%d/%m/%Y')}")
    c.drawString(400, height - 130, f"Timbrado: {config.timbrado or ''}")
    
    # Cliente
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 180, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(110, height - 180, venta.cliente.nombre)
    c.drawString(50, height - 195, f"RUC/CI: {venta.cliente.numero_documento}")
    c.drawString(50, height - 210, f"Dirección: {venta.cliente.direccion or ''}")
    
    # Línea separadora
    c.line(50, height - 230, width - 50, height - 230)
    
    # Detalles de la venta
    y = height - 260
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Cant.")
    c.drawString(100, y, "Descripción")
    c.drawString(400, y, "Precio Unit.")
    c.drawString(500, y, "Subtotal")
    
    c.line(50, y - 5, width - 50, y - 5)
    
    y -= 25
    c.setFont("Helvetica", 10)
    
    for detalle in venta.detalles:
        c.drawString(50, y, str(int(detalle.cantidad)))
        c.drawString(100, y, detalle.descripcion[:40])
        c.drawRightString(470, y, f"Gs. {detalle.precio_unitario:,.0f}")
        c.drawRightString(570, y, f"Gs. {detalle.total:,.0f}")
        y -= 20
        
        if y < 150:
            c.showPage()
            y = height - 100
    
    # Totales
    c.line(400, y - 10, width - 50, y - 10)
    y -= 30
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y, "Subtotal:")
    c.drawRightString(570, y, f"Gs. {venta.subtotal:,.0f}")
    y -= 20
    
    c.drawString(400, y, "IVA 10%:")
    c.drawRightString(570, y, f"Gs. {venta.iva:,.0f}")
    y -= 20
    
    if venta.descuento > 0:
        c.drawString(400, y, "Descuento:")
        c.drawRightString(570, y, f"Gs. {venta.descuento:,.0f}")
        y -= 20
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y, "TOTAL:")
    c.drawRightString(570, y, f"Gs. {venta.total:,.0f}")
    
    c.save()
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=factura_{venta.numero_factura}.pdf'
    
    return response
