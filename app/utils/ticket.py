"""
Clase para generar tickets de facturación con IVA desglosado
Basado en el formato paraguayo con múltiples tipos de IVA
"""
from datetime import datetime
from decimal import Decimal
import io
import os
import sys
import traceback

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

class GeneradorTicket:
    """
    Genera tickets de factura con formato paraguayo
    Soporta IVA 10%, 5% y Exenta
    """
    
    def __init__(self, config_empresa, venta, items):
        """
        config_empresa: ConfiguracionEmpresa
        venta: Venta (con cliente, número factura, etc.)
        items: List de DetalleVenta (con producto, cantidad, precio)
        """
        self.config = config_empresa
        self.venta = venta
        self.items = items
    
    def calcular_subtotales_iva(self):
        """
        Calcula subtotales por tipo de IVA
        Retorna: {
            'exenta': {'subtotal': 0, 'iva': 0},
            '5': {'subtotal': 0, 'iva': 0},
            '10': {'subtotal': 0, 'iva': 0}
        }
        """
        subtotales = {
            'exenta': {'subtotal': Decimal('0'), 'iva': Decimal('0')},
            '5': {'subtotal': Decimal('0'), 'iva': Decimal('0')},
            '10': {'subtotal': Decimal('0'), 'iva': Decimal('0')}
        }
        
        for item in self.items:
            # Determinar tipo de IVA: si hay producto usar su tipo, sino usar 10%
            if hasattr(item, 'producto') and item.producto:
                tipo_iva = item.producto.tipo_iva or '10'
            else:
                # Para servicios sin producto asociado, asumir IVA 10%
                tipo_iva = '10'
            
            cantidad = Decimal(str(item.cantidad))
            precio_unitario = Decimal(str(item.precio_unitario))
            subtotal_item = cantidad * precio_unitario
            
            # El precio ya incluye IVA, debemos calcular el IVA incluido
            if tipo_iva == '10':
                # Precio con IVA = Precio sin IVA * 1.10
                # Precio sin IVA = Precio con IVA / 1.10
                precio_sin_iva = subtotal_item / Decimal('1.10')
                iva_item = subtotal_item - precio_sin_iva
                subtotales['10']['subtotal'] += subtotal_item
                subtotales['10']['iva'] += iva_item
                
            elif tipo_iva == '5':
                precio_sin_iva = subtotal_item / Decimal('1.05')
                iva_item = subtotal_item - precio_sin_iva
                subtotales['5']['subtotal'] += subtotal_item
                subtotales['5']['iva'] += iva_item
                
            else:  # exenta
                subtotales['exenta']['subtotal'] += subtotal_item
        
        return subtotales
    
    def numero_a_letras(self, numero):
        """
        Convierte número a letras (implementación simplificada)
        En producción usar librería como num2words
        """
        # Implementación simplificada
        return f"{numero:,.0f}".replace(',', '.')
    
    def generar_ticket(self):
        """
        Genera el contenido del ticket en formato texto
        """
        lines = []
        ancho = 40
        
        # Encabezado
        lines.append(self.config.nombre_empresa.upper().center(ancho))
        lines.append(f"RUC: {self.config.ruc} - Tel: {self.config.telefono}".center(ancho))
        lines.append(f"{self.config.direccion}".center(ancho))
        lines.append("-" * ancho)
        
        # Datos de timbrado y factura
        lines.append(f"TIMBRADO: {self.config.timbrado}")
        lines.append(f"Vence: {self.config.fecha_vencimiento_timbrado.strftime('%d/%b/%Y').upper()}")
        lines.append(f"FACTURA Nro: {self.venta.numero_factura}")
        lines.append(f"Fecha: {self.venta.fecha_venta.strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"Condición: {self.venta.tipo_venta.upper()}")
        lines.append("-" * ancho)
        
        # Datos del cliente
        if self.venta.cliente:
            lines.append(f"CLIENTE: {self.venta.cliente.nombre.upper()}")
            lines.append(f"RUC/CI: {self.venta.cliente.numero_documento}")
        lines.append("-" * ancho)
        
        # Encabezado de items
        lines.append("ITEM         CANT   IVA    PRECIO   SUBT")
        lines.append("-" * ancho)
        
        # Items
        for item in self.items:
            # Obtener el nombre del item: si tiene descripción usarla, sino usar la del producto
            if hasattr(item, 'descripcion') and item.descripcion:
                nombre = item.descripcion[:13]
            elif hasattr(item, 'producto') and item.producto:
                nombre = item.producto.nombre[:13]
            else:
                nombre = "Item"
            cant = item.cantidad
            
            # Determinar tipo de IVA
            if hasattr(item, 'producto') and item.producto:
                tipo_iva_producto = item.producto.tipo_iva if hasattr(item.producto, 'tipo_iva') else '10'
            else:
                tipo_iva_producto = '10'
            
            iva_str = "EX" if tipo_iva_producto == 'exenta' else f"{tipo_iva_producto}%"
            precio = int(item.precio_unitario)
            subtotal = int(item.cantidad * item.precio_unitario)
            
            lines.append(f"{nombre:<13} {cant:>2}  {iva_str:>4}  {precio:>7,}  {subtotal:>7,}".replace(',', '.'))
        
        lines.append("-" * ancho)
        
        # Subtotales por IVA
        subtotales_iva = self.calcular_subtotales_iva()
        
        if subtotales_iva['exenta']['subtotal'] > 0:
            lines.append(f"SUBTOTAL EXENTA:        {int(subtotales_iva['exenta']['subtotal']):>14,}".replace(',', '.'))
        
        if subtotales_iva['5']['subtotal'] > 0:
            lines.append(f"SUBTOTAL 5%:            {int(subtotales_iva['5']['subtotal']):>14,}".replace(',', '.'))
        
        if subtotales_iva['10']['subtotal'] > 0:
            lines.append(f"SUBTOTAL 10%:           {int(subtotales_iva['10']['subtotal']):>14,}".replace(',', '.'))
        
        lines.append("-" * ancho)
        
        # Total
        total = int(self.venta.total)
        lines.append(f"TOTAL A PAGAR:          {total:>14,} Gs.".replace(',', '.'))
        lines.append("-" * ancho)
        
        # FORMAS DE PAGO
        if hasattr(self.venta, 'pagos') and self.venta.pagos:
            lines.append("FORMAS DE PAGO")
            lines.append("-" * ancho)
            
            total_pagado = 0
            for pago in self.venta.pagos:
                if pago.estado == 'confirmado':
                    forma_nombre = pago.forma_pago.nombre if pago.forma_pago else 'N/A'
                    monto = int(pago.monto)
                    total_pagado += monto
                    
                    # Mostrar forma de pago con referencia si existe
                    if pago.referencia:
                        lines.append(f"{forma_nombre}: {monto:>7,} Gs.".replace(',', '.'))
                        lines.append(f"  Ref: {pago.referencia[:25]}")
                    else:
                        lines.append(f"{forma_nombre}: {monto:>23,} Gs.".replace(',', '.'))
            
            lines.append("-" * ancho)
            lines.append(f"TOTAL RECIBIDO:         {total_pagado:>14,} Gs.".replace(',', '.'))
            
            # VUELTO
            vuelto = total_pagado - total
            if vuelto > 0:
                lines.append(f"VUELTO:                 {vuelto:>14,} Gs.".replace(',', '.'))
                lines.append("-" * ancho)
        
        # Total en letras
        lines.append(f"TOTAL EN LETRAS: {self.numero_a_letras(total)}")
        lines.append(f"guaraníes.")
        lines.append("")
        
        # Liquidación del IVA
        lines.append("LIQUIDACIÓN DEL IVA")
        if subtotales_iva['5']['iva'] > 0:
            lines.append(f"IVA 5%:   {int(subtotales_iva['5']['iva']):>7,}".replace(',', '.'))
        if subtotales_iva['10']['iva'] > 0:
            lines.append(f"IVA 10%:  {int(subtotales_iva['10']['iva']):>7,}".replace(',', '.'))
        
        total_iva = sum(s['iva'] for s in subtotales_iva.values())
        lines.append(f"TOTAL IVA: {int(total_iva):>6,}".replace(',', '.'))
        lines.append("-" * ancho)
        
        # Pie de página
        lines.append("¡Gracias por su compra!".center(ancho))
        lines.append("Original: Cliente (Blanco)".center(ancho))
        
        return "\n".join(lines)

    def generar_ticket_pdf(self):
        """
        Genera el ticket en PDF usando reportlab - Diseño profesional con logo.
        """
        print("[ticket] Iniciando generar_ticket_pdf", file=sys.stderr, flush=True)
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from io import BytesIO
            import os
            
            buffer = BytesIO()
            print("[ticket] Buffer creado", file=sys.stderr, flush=True)
            
            # Ticket en formato 80mm de ancho (papel térmico estándar)
            ancho_ticket = 80 * mm
            alto_ticket = 297 * mm  # A4 alto
            
            c = canvas.Canvas(buffer, pagesize=(ancho_ticket, alto_ticket))
            print("[ticket] Canvas creado", file=sys.stderr, flush=True)
            
            # Posición inicial
            x_margin = 5 * mm
            y = alto_ticket - 10 * mm
            ancho_util = ancho_ticket - (2 * x_margin)
            
            # ============== ENCABEZADO CON LOGO ==============
            
            # Intentar cargar el logo
            logo_path = None
            if self.config.logo_url:
                # Si es ruta relativa, buscar en static
                if not self.config.logo_url.startswith('http'):
                    logo_path = os.path.join('app', 'static', self.config.logo_url.lstrip('/'))
                    if not os.path.exists(logo_path):
                        logo_path = None
                        print(f"[ticket] Logo no encontrado: {logo_path}", file=sys.stderr, flush=True)
            
            # Dibujar logo si existe
            if logo_path and os.path.exists(logo_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    logo_height = 15 * mm
                    logo_width = 40 * mm
                    x_logo = (ancho_ticket - logo_width) / 2
                    c.drawImage(logo_path, x_logo, y - logo_height, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
                    y -= (logo_height + 3 * mm)
                    print("[ticket] Logo dibujado", file=sys.stderr, flush=True)
                except Exception as e:
                    print(f"[ticket] Error al cargar logo: {e}", file=sys.stderr, flush=True)
            
            # Nombre de la empresa
            c.setFont("Helvetica-Bold", 12)
            nombre_empresa = self.config.nombre_empresa.upper()
            text_width = c.stringWidth(nombre_empresa, "Helvetica-Bold", 12)
            c.drawString((ancho_ticket - text_width) / 2, y, nombre_empresa)
            y -= 5 * mm
            
            # RUC y Teléfono
            c.setFont("Helvetica", 8)
            info_line = f"RUC: {self.config.ruc}"
            text_width = c.stringWidth(info_line, "Helvetica", 8)
            c.drawString((ancho_ticket - text_width) / 2, y, info_line)
            y -= 3.5 * mm
            
            if self.config.telefono:
                tel_line = f"Tel: {self.config.telefono}"
                text_width = c.stringWidth(tel_line, "Helvetica", 8)
                c.drawString((ancho_ticket - text_width) / 2, y, tel_line)
                y -= 3.5 * mm
            
            if self.config.direccion:
                c.setFont("Helvetica", 7)
                direccion = self.config.direccion[:50]
                text_width = c.stringWidth(direccion, "Helvetica", 7)
                c.drawString((ancho_ticket - text_width) / 2, y, direccion)
                y -= 4 * mm
            
            # Línea separadora gruesa
            c.setLineWidth(1.5)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 4 * mm
            
            # ============== DATOS DE TIMBRADO Y FACTURA ==============
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_margin, y, "FACTURA")
            y -= 4 * mm
            
            c.setFont("Helvetica", 8)
            c.drawString(x_margin, y, f"Timbrado: {self.config.timbrado or 'N/A'}")
            y -= 3.5 * mm
            
            if self.config.fecha_vencimiento_timbrado:
                vence = self.config.fecha_vencimiento_timbrado.strftime('%d/%m/%Y')
                c.drawString(x_margin, y, f"Vence: {vence}")
                y -= 3.5 * mm
            
            # Número de factura destacado
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_margin, y, f"Nro: {self.venta.numero_factura}")
            y -= 4 * mm
            
            c.setFont("Helvetica", 8)
            fecha_str = self.venta.fecha_venta.strftime('%d/%m/%Y %H:%M')
            c.drawString(x_margin, y, f"Fecha: {fecha_str}")
            y -= 3.5 * mm
            
            tipo_venta = self.venta.tipo_venta.upper()
            c.drawString(x_margin, y, f"Condición: {tipo_venta}")
            y -= 4 * mm
            
            # Línea separadora
            c.setLineWidth(0.5)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 4 * mm
            
            # ============== DATOS DEL CLIENTE ==============
            
            if self.venta.cliente:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(x_margin, y, "CLIENTE:")
                y -= 3.5 * mm
                
                c.setFont("Helvetica", 7)
                cliente_nombre = self.venta.cliente.nombre.upper()[:35]
                c.drawString(x_margin, y, cliente_nombre)
                y -= 3 * mm
                
                c.drawString(x_margin, y, f"RUC/CI: {self.venta.cliente.numero_documento}")
                y -= 4 * mm
            
            # Línea separadora
            c.setLineWidth(0.5)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 4 * mm
            
            # ============== ITEMS ==============
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x_margin, y, "DESCRIPCIÓN")
            c.drawString(x_margin + 35 * mm, y, "CANT")
            c.drawString(x_margin + 45 * mm, y, "PRECIO")
            c.drawString(x_margin + 60 * mm, y, "TOTAL")
            y -= 3 * mm
            
            c.setLineWidth(0.3)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 3 * mm
            
            c.setFont("Helvetica", 7)
            for item in self.items:
                # Verificar si necesitamos nueva página
                if y < 30 * mm:
                    c.showPage()
                    y = alto_ticket - 10 * mm
                    c.setFont("Helvetica", 7)
                
                # Obtener nombre del item
                if hasattr(item, 'descripcion') and item.descripcion:
                    nombre = item.descripcion[:30]
                elif hasattr(item, 'producto') and item.producto:
                    nombre = item.producto.nombre[:30]
                else:
                    nombre = "Item"
                
                cant = f"{item.cantidad:.0f}"
                precio = f"{int(item.precio_unitario):,}".replace(',', '.')
                total = f"{int(item.cantidad * item.precio_unitario):,}".replace(',', '.')
                
                # Nombre del item
                c.drawString(x_margin, y, nombre)
                y -= 3 * mm
                
                # Cantidad, precio y total en la misma línea
                c.drawString(x_margin + 35 * mm, y, cant)
                c.drawString(x_margin + 45 * mm, y, precio)
                c.drawRightString(ancho_ticket - x_margin, y, total)
                y -= 4 * mm
            
            # Línea separadora
            c.setLineWidth(0.5)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 4 * mm
            
            # ============== TOTALES ==============
            
            subtotales_iva = self.calcular_subtotales_iva()
            c.setFont("Helvetica", 8)
            
            if subtotales_iva['exenta']['subtotal'] > 0:
                c.drawString(x_margin, y, "Exenta:")
                valor = f"{int(subtotales_iva['exenta']['subtotal']):,}".replace(',', '.')
                c.drawRightString(ancho_ticket - x_margin, y, valor)
                y -= 3.5 * mm
            
            if subtotales_iva['5']['subtotal'] > 0:
                c.drawString(x_margin, y, "Gravada 5%:")
                valor = f"{int(subtotales_iva['5']['subtotal']):,}".replace(',', '.')
                c.drawRightString(ancho_ticket - x_margin, y, valor)
                y -= 3 * mm
                c.drawString(x_margin + 5 * mm, y, "IVA 5%:")
                iva5 = f"{int(subtotales_iva['5']['iva']):,}".replace(',', '.')
                c.drawRightString(ancho_ticket - x_margin, y, iva5)
                y -= 3.5 * mm
            
            if subtotales_iva['10']['subtotal'] > 0:
                c.drawString(x_margin, y, "Gravada 10%:")
                valor = f"{int(subtotales_iva['10']['subtotal']):,}".replace(',', '.')
                c.drawRightString(ancho_ticket - x_margin, y, valor)
                y -= 3 * mm
                c.drawString(x_margin + 5 * mm, y, "IVA 10%:")
                iva10 = f"{int(subtotales_iva['10']['iva']):,}".replace(',', '.')
                c.drawRightString(ancho_ticket - x_margin, y, iva10)
                y -= 4 * mm
            
            # Total IVA
            total_iva = sum(s['iva'] for s in subtotales_iva.values())
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_margin, y, "TOTAL IVA:")
            iva_str = f"{int(total_iva):,}".replace(',', '.')
            c.drawRightString(ancho_ticket - x_margin, y, iva_str)
            y -= 5 * mm
            
            # Línea antes del total
            c.setLineWidth(1)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 5 * mm
            
            # TOTAL A PAGAR - Destacado
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "TOTAL A PAGAR:")
            total_str = f"{int(self.venta.total):,} Gs.".replace(',', '.')
            c.drawRightString(ancho_ticket - x_margin, y, total_str)
            y -= 6 * mm
            
            # Línea después del total
            c.setLineWidth(1)
            c.line(x_margin, y, ancho_ticket - x_margin, y)
            y -= 5 * mm
            
            # ============== FORMAS DE PAGO ==============
            
            if hasattr(self.venta, 'pagos') and self.venta.pagos:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(x_margin, y, "FORMAS DE PAGO:")
                y -= 4 * mm
                
                c.setFont("Helvetica", 7)
                for pago in self.venta.pagos:
                    if pago.estado == 'confirmado':
                        forma_nombre = pago.forma_pago.nombre if pago.forma_pago else 'N/A'
                        monto_str = f"{int(pago.monto):,}".replace(',', '.')
                        
                        c.drawString(x_margin + 2 * mm, y, forma_nombre)
                        c.drawRightString(ancho_ticket - x_margin, y, monto_str)
                        y -= 3.5 * mm
                
                y -= 3 * mm
            
            # ============== PIE DE PÁGINA ==============
            
            c.setFont("Helvetica-BoldOblique", 9)
            mensaje = "¡Gracias por su compra!"
            text_width = c.stringWidth(mensaje, "Helvetica-BoldOblique", 9)
            c.drawString((ancho_ticket - text_width) / 2, y, mensaje)
            y -= 5 * mm
            
            c.setFont("Helvetica", 6)
            footer = "Original: Cliente"
            text_width = c.stringWidth(footer, "Helvetica", 6)
            c.drawString((ancho_ticket - text_width) / 2, y, footer)
            
            print("[ticket] Dibujado completado, llamando c.save()", file=sys.stderr, flush=True)
            c.save()
            print("[ticket] c.save() completado", file=sys.stderr, flush=True)
            
            # Leer el contenido del buffer
            buffer.seek(0)
            pdf_bytes = buffer.read()
            buffer.close()
            
            print(f"[ticket] PDF generado: {len(pdf_bytes)} bytes", file=sys.stderr, flush=True)
            
            # Validar PDF
            if len(pdf_bytes) < 100:
                print(f"[ticket] ERROR: PDF muy pequeño ({len(pdf_bytes)} bytes)", file=sys.stderr, flush=True)
                raise Exception(f"PDF generado muy pequeño: {len(pdf_bytes)} bytes")
            
            if not pdf_bytes.startswith(b'%PDF'):
                print(f"[ticket] ERROR: No es PDF válido", file=sys.stderr, flush=True)
                raise Exception("Contenido no es PDF válido")
            
            print("[ticket] PDF válido, retornando", file=sys.stderr, flush=True)
            return pdf_bytes
            
        except Exception as e:
            print(f"[ticket] EXCEPCIÓN: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            raise


# EJEMPLO DE USO:
"""
# En la ruta de crear venta:
from app.utils.ticket import GeneradorTicket

def crear_venta():
    # ... crear venta y detalles ...
    
    config = ConfiguracionEmpresa.get_config()
    ticket = GeneradorTicket(config, venta, venta.detalles)
    contenido_ticket = ticket.generar_ticket()
    
    # Imprimir o guardar el ticket
    print(contenido_ticket)
    
    # O enviar a impresora térmica
    # imprimir_ticket(contenido_ticket)
"""
