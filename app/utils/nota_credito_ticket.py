"""
Generador de tickets para Notas de Crédito
Cumple con requisitos de SET Paraguay
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
import os
import sys
import traceback
from decimal import Decimal

from app.models import ConfiguracionEmpresa

def generar_nota_credito_ticket_pdf(nota):
    """
    Genera PDF para Nota de Crédito cumpliendo con requisitos SET Paraguay
    Muestra: Factura Original, Productos Devueltos, Timbrado Vence, Nuevo Saldo
    """
    print(f"[nota_credito_pdf] Generando PDF para NC {nota.id}", file=sys.stderr, flush=True)
    
    try:
        config = ConfiguracionEmpresa.get_config()
        buffer = BytesIO()
        
        # Ticket en formato 80mm de ancho (papel térmico estándar)
        ancho_ticket = 80 * mm
        alto_ticket = 297 * mm
        
        c = canvas.Canvas(buffer, pagesize=(ancho_ticket, alto_ticket))
        
        # Posición inicial
        x_margin = 5 * mm
        y = alto_ticket - 10 * mm
        ancho_util = ancho_ticket - (2 * x_margin)
        
        # ============== ENCABEZADO CON LOGO ==============
        
        # Intentar cargar el logo
        logo_path = None
        if config.logo_url:
            if not config.logo_url.startswith('http'):
                logo_path = os.path.join('app', 'static', config.logo_url.lstrip('/'))
                if not os.path.exists(logo_path):
                    logo_path = None
        
        # Dibujar logo si existe
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_height = 15 * mm
                logo_width = 40 * mm
                x_logo = (ancho_ticket - logo_width) / 2
                c.drawImage(logo_path, x_logo, y - logo_height, width=logo_width, height=logo_height, 
                           preserveAspectRatio=True, mask='auto')
                y -= (logo_height + 3 * mm)
            except Exception as e:
                print(f"[nota_credito_pdf] Error al cargar logo: {e}", file=sys.stderr, flush=True)
        
        # Nombre de la empresa
        c.setFont("Helvetica-Bold", 12)
        nombre_empresa = config.nombre_empresa.upper()
        text_width = c.stringWidth(nombre_empresa, "Helvetica-Bold", 12)
        c.drawString((ancho_ticket - text_width) / 2, y, nombre_empresa)
        y -= 5 * mm
        
        # RUC
        c.setFont("Helvetica", 8)
        info_line = f"RUC: {config.ruc}"
        text_width = c.stringWidth(info_line, "Helvetica", 8)
        c.drawString((ancho_ticket - text_width) / 2, y, info_line)
        y -= 3.5 * mm
        
        # Teléfono
        if config.telefono:
            tel_line = f"Tel: {config.telefono}"
            text_width = c.stringWidth(tel_line, "Helvetica", 8)
            c.drawString((ancho_ticket - text_width) / 2, y, tel_line)
            y -= 3.5 * mm
        
        # Dirección
        if config.direccion:
            c.setFont("Helvetica", 7)
            direccion = config.direccion[:50]
            text_width = c.stringWidth(direccion, "Helvetica", 7)
            c.drawString((ancho_ticket - text_width) / 2, y, direccion)
            y -= 4 * mm
        
        # Línea separadora gruesa
        c.setLineWidth(1.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 5 * mm
        
        # ============== TÍTULO NOTA DE CRÉDITO ==============
        
        c.setFont("Helvetica-Bold", 14)
        titulo = "NOTA DE CRÉDITO"
        text_width = c.stringWidth(titulo, "Helvetica-Bold", 14)
        c.drawString((ancho_ticket - text_width) / 2, y, titulo)
        y -= 6 * mm
        
        # ============== DATOS DE TIMBRADO ==============
        
        c.setFont("Helvetica", 8)
        c.drawString(x_margin, y, f"Timbrado: {config.timbrado or 'N/A'}")
        y -= 3.5 * mm
        
        if config.fecha_vencimiento_timbrado:
            vence = config.fecha_vencimiento_timbrado.strftime('%d/%m/%Y')
            c.drawString(x_margin, y, f"Vence: {vence}")
            y -= 4 * mm
        
        # Establecimiento y punto de expedición de factura original (para construir número completo)
        # Formato: 001-001
        establecimiento_punto = "N/A"
        if nota.venta and nota.venta.numero_factura:
            partes_factura = nota.venta.numero_factura.split('-')
            if len(partes_factura) >= 2:
                establecimiento = partes_factura[0]
                punto_expedicion = partes_factura[1]
                establecimiento_punto = f"{establecimiento}-{punto_expedicion}"
        
        # Número de NC destacado con formato completo
        c.setFont("Helvetica-Bold", 10)
        # Extraer solo el número de la NC (ej: 0000013 de NC-0000013)
        numero_nc_base = nota.numero_nota.replace('NC-', '').lstrip('0').zfill(7)
        numero_nc_completo = f"NC {establecimiento_punto}-{numero_nc_base}"
        c.drawString(x_margin, y, f"N°: {numero_nc_completo}")
        y -= 4 * mm
        
        c.setFont("Helvetica", 8)
        fecha_str = nota.fecha_emision.strftime('%d/%m/%Y %H:%M')
        c.drawString(x_margin, y, f"Fecha: {fecha_str}")
        y -= 5 * mm
        
        # Línea separadora
        c.setLineWidth(0.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 4 * mm
        
        # ============== FACTURA ORIGINAL REFERENCIADA ==============
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_margin, y, "MODIFICA FACTURA:")
        y -= 3.5 * mm
        
        if nota.venta:
            c.setFont("Helvetica", 8)
            c.drawString(x_margin + 2 * mm, y, f"N°: {nota.venta.numero_factura}")
            y -= 3 * mm
            
            fecha_factura = nota.venta.fecha_venta.strftime('%d/%m/%Y')
            c.drawString(x_margin + 2 * mm, y, f"Fecha: {fecha_factura}")
            y -= 4 * mm
        else:
            c.setFont("Helvetica", 8)
            c.drawString(x_margin + 2 * mm, y, "No especificada")
            y -= 4 * mm
        
        # Línea separadora
        c.setLineWidth(0.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 4 * mm
        
        # ============== DATOS DEL CLIENTE ==============
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_margin, y, "CLIENTE:")
        y -= 3.5 * mm
        
        if nota.venta and nota.venta.cliente:
            c.setFont("Helvetica", 7)
            cliente_nombre = nota.venta.cliente.nombre.upper()[:35]
            c.drawString(x_margin, y, cliente_nombre)
            y -= 3 * mm
            
            c.drawString(x_margin, y, f"RUC/CI: {nota.venta.cliente.numero_documento}")
            y -= 4 * mm
        else:
            c.setFont("Helvetica", 7)
            c.drawString(x_margin, y, "No especificado")
            y -= 4 * mm
        
        # Línea separadora
        c.setLineWidth(0.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 4 * mm
        
        # ============== MOTIVO DE LA NOTA DE CRÉDITO ==============
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_margin, y, "MOTIVO:")
        y -= 3.5 * mm
        
        c.setFont("Helvetica", 7)
        # Wrap del motivo si es muy largo
        motivo_texto = nota.motivo or "Devolución de productos"
        max_chars_per_line = 45
        
        if len(motivo_texto) > max_chars_per_line:
            # Dividir en líneas
            palabras = motivo_texto.split()
            linea_actual = ""
            for palabra in palabras:
                if len(linea_actual) + len(palabra) + 1 <= max_chars_per_line:
                    linea_actual += (" " if linea_actual else "") + palabra
                else:
                    c.drawString(x_margin + 2 * mm, y, linea_actual)
                    y -= 3 * mm
                    linea_actual = palabra
            if linea_actual:
                c.drawString(x_margin + 2 * mm, y, linea_actual)
                y -= 3 * mm
        else:
            c.drawString(x_margin + 2 * mm, y, motivo_texto)
            y -= 3 * mm
        
        y -= 1 * mm
        
        # Línea separadora
        c.setLineWidth(0.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 4 * mm
        
        # ============== PRODUCTOS DEVUELTOS ==============
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_margin, y, "PRODUCTOS DEVUELTOS:")
        y -= 4 * mm
        
        # Obtener detalles y descripción desde VentaDetalle
        try:
            # Obtener detalles - intentar desde relación primero
            if hasattr(nota, 'detalles') and nota.detalles:
                detalles = list(nota.detalles)
            else:
                from app.models.nota_credito_detalle import NotaCreditoDetalle
                detalles = NotaCreditoDetalle.query.filter_by(nota_credito_id=nota.id).all()
            
            if detalles:
                c.setFont("Helvetica-Bold", 7)
                c.drawString(x_margin, y, "DESCRIPCIÓN")
                c.drawString(x_margin + 35 * mm, y, "CANT")
                c.drawRightString(ancho_ticket - x_margin, y, "MONTO")
                y -= 3 * mm
                
                c.setLineWidth(0.3)
                c.line(x_margin, y, ancho_ticket - x_margin, y)
                y -= 3 * mm
                
                c.setFont("Helvetica", 7)
                for detalle in detalles:
                    # Buscar descripción desde VentaDetalle
                    descripcion = None
                    try:
                        if hasattr(detalle, 'venta_detalle_id') and detalle.venta_detalle_id:
                            from app.models.venta import VentaDetalle
                            vdet = VentaDetalle.query.get(detalle.venta_detalle_id)
                            if vdet:
                                descripcion = vdet.descripcion
                    except Exception:
                        pass
                    
                    if not descripcion:
                        descripcion = getattr(detalle, 'descripcion', 'Producto')
                    
                    descripcion = descripcion[:30]
                    cant = f"{detalle.cantidad:.0f}"
                    monto_str = f"{int(detalle.subtotal):,}".replace(',', '.')
                    
                    c.drawString(x_margin, y, descripcion)
                    c.drawString(x_margin + 35 * mm, y, cant)
                    c.drawRightString(ancho_ticket - x_margin, y, monto_str)
                    y -= 3.5 * mm
                
                y -= 1 * mm
        except Exception as e:
            print(f"[nota_credito_pdf] Error al procesar detalles: {e}", file=sys.stderr, flush=True)
            c.setFont("Helvetica", 7)
            c.drawString(x_margin, y, "Error al cargar productos")
            y -= 4 * mm
        
        # Línea separadora
        c.setLineWidth(0.5)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 4 * mm
        
        # ============== CÁLCULO DEL NUEVO SALDO ==============
        
        c.setFont("Helvetica", 8)
        
        # Factura Original
        if nota.venta:
            monto_original = f"{int(nota.venta.total):,}".replace(',', '.')
            c.drawString(x_margin, y, "Factura Original:")
            c.drawRightString(ancho_ticket - x_margin, y, f"{monto_original} Gs.")
            y -= 4 * mm
        
        # Crédito a Favor
        credito_str = f"{int(nota.monto):,}".replace(',', '.')
        c.drawString(x_margin, y, "Crédito a Favor:")
        c.drawRightString(ancho_ticket - x_margin, y, f"{credito_str} Gs.")
        y -= 5 * mm
        
        # Línea antes del nuevo saldo
        c.setLineWidth(1)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 5 * mm
        
        # NUEVO SALDO - Destacado
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margin, y, "NUEVO SALDO:")
        
        if nota.venta:
            nuevo_saldo = nota.venta.total - nota.monto
        else:
            nuevo_saldo = -nota.monto
        
        nuevo_saldo_str = f"{int(nuevo_saldo):,} Gs.".replace(',', '.')
        c.drawRightString(ancho_ticket - x_margin, y, nuevo_saldo_str)
        y -= 6 * mm
        
        # Línea después del saldo
        c.setLineWidth(1)
        c.line(x_margin, y, ancho_ticket - x_margin, y)
        y -= 6 * mm
        
        # ============== PIE DE PÁGINA ==============
        
        c.setFont("Helvetica", 6)
        c.drawString(x_margin, y, f"Emisión: {nota.estado or 'N/A'}")
        y -= 3 * mm
        
        c.drawString(x_margin, y, f"Estado: {nota.estado or 'N/A'}")
        y -= 5 * mm
        
        c.setFont("Helvetica-BoldOblique", 8)
        mensaje = "Documento tributario válido"
        text_width = c.stringWidth(mensaje, "Helvetica-BoldOblique", 8)
        c.drawString((ancho_ticket - text_width) / 2, y, mensaje)
        y -= 4 * mm
        
        c.setFont("Helvetica", 6)
        footer = "Original: Cliente"
        text_width = c.stringWidth(footer, "Helvetica", 6)
        c.drawString((ancho_ticket - text_width) / 2, y, footer)
        
        print("[nota_credito_pdf] Dibujado completado, guardando PDF", file=sys.stderr, flush=True)
        c.save()
        
        # Leer el contenido del buffer
        buffer.seek(0)
        pdf_bytes = buffer.read()
        buffer.close()
        
        print(f"[nota_credito_pdf] PDF generado: {len(pdf_bytes)} bytes", file=sys.stderr, flush=True)
        
        # Validar PDF
        if len(pdf_bytes) < 100:
            raise Exception(f"PDF generado muy pequeño: {len(pdf_bytes)} bytes")
        
        if not pdf_bytes.startswith(b'%PDF'):
            raise Exception("Contenido no es PDF válido")
        
        return pdf_bytes
        
    except Exception as e:
        print(f"[nota_credito_pdf] EXCEPCIÓN: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise

