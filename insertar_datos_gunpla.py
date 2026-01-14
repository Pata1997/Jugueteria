"""
Script para insertar datos de prueba: Productos Gunpla, Servicios y Órdenes de Compra
"""

from app import create_app, db
    # Los imports de modelos van dentro de with app.app_context()
from datetime import datetime, date
from decimal import Decimal

def insertar_datos_gunpla():
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print("INSERTANDO DATOS DE GUNPLA EN LA BASE DE DATOS")
        print("="*60 + "\n")

        # ====== LIMPIAR USUARIOS Y RECREAR LOS PRINCIPALES ======
        # ====== LIMPIAR BASE DE DATOS (excepto configuración) ======
        print("\nLIMPIANDO BASE DE DATOS DE PRUEBA...")
        from app.models import (
            Producto, Categoria, TipoServicio, SolicitudServicio, Proveedor, Compra, CompraDetalle,
            Cliente, Usuario, Venta, VentaDetalle, Pago, CuentaPorPagar, PagoCompra, AperturaCaja, MovimientoCaja
        )
        # Borrar primero los movimientos de caja para evitar error de clave foránea con aperturas de caja
        db.session.query(MovimientoCaja).delete()
        db.session.query(AperturaCaja).delete()
        db.session.query(PagoCompra).delete()
        db.session.query(VentaDetalle).delete()
        db.session.query(Pago).delete()
        db.session.query(Venta).delete()
        db.session.query(CuentaPorPagar).delete()
        db.session.query(CompraDetalle).delete()
        db.session.query(Compra).delete()
        db.session.query(Proveedor).delete()
        db.session.query(SolicitudServicio).delete()
        db.session.query(Cliente).delete()
        db.session.commit()
        print("✓ Base de datos de prueba limpiada (excepto configuración)")
        # Ahora sí, eliminar usuarios y recrear los principales
        print("\nLIMPIANDO USUARIOS Y RECREANDO PRINCIPALES...")
        from app.models import MovimientoProducto, HistorialPrecio, Bitacora
        db.session.query(MovimientoProducto).delete()
        db.session.query(HistorialPrecio).delete()
        db.session.query(Bitacora).delete()
        db.session.query(Usuario).delete()
        db.session.commit()
        usuarios = [
            dict(username='admin', email='admin@demo.com', nombre='Admin', apellido='Demo', rol='admin', password='123456'),
            dict(username='recepcion', email='recepcion@demo.com', nombre='Recepcion', apellido='Demo', rol='recepcion', password='123456'),
            dict(username='tecnico', email='tecnico@demo.com', nombre='Tecnico', apellido='Demo', rol='tecnico', password='123456'),
            dict(username='caja', email='caja@demo.com', nombre='Caja', apellido='Demo', rol='caja', password='123456'),
        ]
        for u in usuarios:
            user = Usuario(
                username=u['username'],
                email=u['email'],
                nombre=u['nombre'],
                apellido=u['apellido'],
                rol=u['rol'],
                activo=True
            )
            user.set_password(u['password'])
            db.session.add(user)
        db.session.commit()
        print("✓ Usuarios principales recreados: admin, recepcion, tecnico, caja")
        # ====== LIMPIAR BASE DE DATOS (excepto configuración) ======
        print("\nLIMPIANDO BASE DE DATOS DE PRUEBA...")
        # Eliminar ventas, compras, reclamos, servicios, clientes, proveedores
        from app.models.venta import Venta, VentaDetalle, Pago
        from app.models.compra import Compra, CompraDetalle, Proveedor
        from app.models.servicio import SolicitudServicio
        from app.models.cliente import Cliente
        # Eliminar detalles y relaciones primero
        db.session.query(VentaDetalle).delete()
        db.session.query(Pago).delete()
        db.session.query(Venta).delete()
        db.session.query(CompraDetalle).delete()
        db.session.query(Compra).delete()
        db.session.query(Proveedor).delete()
        db.session.query(SolicitudServicio).delete()
        db.session.query(Cliente).delete()
        db.session.commit()
        print("✓ Base de datos de prueba limpiada (excepto configuración)")
        # ====== 1. CREAR CATEGORÍA GUNPLA ======
        print("1. Creando categoría Gunpla...")
        categoria_gunpla = Categoria.query.filter_by(codigo='GUNPLA').first()
        if not categoria_gunpla:
            categoria_gunpla = Categoria(
                codigo='GUNPLA',
                nombre='Gunpla / Model Kits',
                descripcion='Model Kits de Gundam y otros mechas japoneses',
                activo=True
            )
            db.session.add(categoria_gunpla)
            db.session.commit()
            print("   ✓ Categoría 'Gunpla / Model Kits' creada")
        else:
            print("   ℹ Categoría ya existe")
        
        # ====== 2. CREAR PRODUCTOS GUNPLA ======
        print("\n2. Creando productos Gunpla...")
        
        productos_gunpla = [
            # 1/144 HG - High Grade
            {
                'codigo': 'HG-001',
                'nombre': 'HG RX-78-2 Gundam',
                'descripcion': 'High Grade 1/144 - Nivel: Principiante/Intermedio. Armado sencillo, buen nivel de detalle, poco o ningún pegamento necesario.',
                'escala': '1/144 HG',
                'precio_compra': 150000,
                'precio_venta': 220000,
                'stock_actual': 15,
                'stock_minimo': 5
            },
            {
                'codigo': 'HG-002',
                'nombre': 'HG Zaku II Char Custom',
                'descripcion': 'High Grade 1/144 - Mobile Suit de Char Aznable. Ideal para principiantes y coleccionistas casuales.',
                'escala': '1/144 HG',
                'precio_compra': 145000,
                'precio_venta': 215000,
                'stock_actual': 12,
                'stock_minimo': 5
            },
            {
                'codigo': 'HG-003',
                'nombre': 'HG Wing Gundam Zero',
                'descripcion': 'High Grade 1/144 - Del anime Gundam Wing. Excelente para iniciarse en el hobby.',
                'escala': '1/144 HG',
                'precio_compra': 160000,
                'precio_venta': 235000,
                'stock_actual': 10,
                'stock_minimo': 5
            },
            
            # 1/144 RG - Real Grade
            {
                'codigo': 'RG-001',
                'nombre': 'RG Strike Freedom Gundam',
                'descripcion': 'Real Grade 1/144 - Nivel: Intermedio/Avanzado. Muchísimo detalle para su tamaño, frame interno, calcomanías realistas.',
                'escala': '1/144 RG',
                'precio_compra': 280000,
                'precio_venta': 420000,
                'stock_actual': 8,
                'stock_minimo': 3
            },
            {
                'codigo': 'RG-002',
                'nombre': 'RG Unicorn Gundam',
                'descripcion': 'Real Grade 1/144 - Modo Destroy con partes transformables. Realismo sin ir a tamaños grandes.',
                'escala': '1/144 RG',
                'precio_compra': 300000,
                'precio_venta': 450000,
                'stock_actual': 6,
                'stock_minimo': 3
            },
            {
                'codigo': 'RG-003',
                'nombre': 'RG Nu Gundam',
                'descripcion': 'Real Grade 1/144 - Del anime Chars Counterattack. Incluye Fin Funnels desplegables.',
                'escala': '1/144 RG',
                'precio_compra': 320000,
                'precio_venta': 480000,
                'stock_actual': 5,
                'stock_minimo': 3
            },
            
            # SD - Super Deformed
            {
                'codigo': 'SD-001',
                'nombre': 'SD Gundam RX-78-2',
                'descripcion': 'Super Deformed - Estilo caricaturesco. Cabeza grande, cuerpo pequeño. Muy fácil de armar, ideal para niños.',
                'escala': '1/200 SD',
                'precio_compra': 80000,
                'precio_venta': 120000,
                'stock_actual': 20,
                'stock_minimo': 8
            },
            {
                'codigo': 'SD-002',
                'nombre': 'SD Barbatos Lupus Rex',
                'descripcion': 'Super Deformed - Del anime Iron-Blooded Orphans. Perfecto para decoración o colección divertida.',
                'escala': '1/200 SD',
                'precio_compra': 85000,
                'precio_venta': 125000,
                'stock_actual': 18,
                'stock_minimo': 8
            },
            
            # 1/100 MG - Master Grade
            {
                'codigo': 'MG-001',
                'nombre': 'MG Freedom Gundam Ver 2.0',
                'descripcion': 'Master Grade 1/100 - Nivel: Intermedio/Avanzado. Frame interno completo, alto nivel de detalle, excelente posabilidad.',
                'escala': '1/100 MG',
                'precio_compra': 450000,
                'precio_venta': 680000,
                'stock_actual': 7,
                'stock_minimo': 3
            },
            {
                'codigo': 'MG-002',
                'nombre': 'MG Sazabi Ver Ka',
                'descripcion': 'Master Grade 1/100 - Versión Katoki. Para fanáticos serios del Gunpla, uno de los mejores MG.',
                'escala': '1/100 MG',
                'precio_compra': 550000,
                'precio_venta': 825000,
                'stock_actual': 4,
                'stock_minimo': 2
            },
            {
                'codigo': 'MG-003',
                'nombre': 'MG Gundam Mk-II Titans',
                'descripcion': 'Master Grade 1/100 - Clásico de Zeta Gundam. Excelente articulación y detalles mecánicos.',
                'escala': '1/100 MG',
                'precio_compra': 400000,
                'precio_venta': 600000,
                'stock_actual': 6,
                'stock_minimo': 3
            },
            
            # 1/60 PG - Perfect Grade
            {
                'codigo': 'PG-001',
                'nombre': 'PG Unicorn Gundam',
                'descripcion': 'Perfect Grade 1/60 - Nivel: Avanzado/Experto. Máximo detalle, partes mecánicas complejas, incluye LEDs. Para vitrinas premium.',
                'escala': '1/60 PG',
                'precio_compra': 1200000,
                'precio_venta': 1800000,
                'stock_actual': 2,
                'stock_minimo': 1
            },
            {
                'codigo': 'PG-002',
                'nombre': 'PG Strike Gundam',
                'descripcion': 'Perfect Grade 1/60 - Versión premium con múltiples capas de detalle. Incluye Aile Striker Pack.',
                'escala': '1/60 PG',
                'precio_compra': 1000000,
                'precio_venta': 1500000,
                'stock_actual': 3,
                'stock_minimo': 1
            },
            
            # 1/48 MS - Mega Size
            {
                'codigo': 'MS-001',
                'nombre': 'Mega Size RX-78-2 Gundam',
                'descripcion': 'Mega Size 1/48 - Muy grande pero sorprendentemente simple de armar. Ideal para impacto visual, poco detalle comparado con PG.',
                'escala': '1/48 MS',
                'precio_compra': 800000,
                'precio_venta': 1200000,
                'stock_actual': 3,
                'stock_minimo': 1
            },
        ]
        
        productos_creados = 0
        for prod_data in productos_gunpla:
            producto_existe = Producto.query.filter_by(codigo=prod_data['codigo']).first()
            if not producto_existe:
                producto = Producto(
                    codigo=prod_data['codigo'],
                    nombre=prod_data['nombre'],
                    descripcion=prod_data['descripcion'],
                    categoria_id=categoria_gunpla.id,
                    tipo_producto='producto',
                    unidad_medida='unidad',
                    precio_compra=prod_data['precio_compra'],
                    precio_venta=prod_data['precio_venta'],
                    tipo_iva='10',
                    stock_actual=prod_data['stock_actual'],
                    stock_minimo=prod_data['stock_minimo'],
                    stock_maximo=prod_data['stock_actual'] * 3,
                    es_importado=True,
                    activo=True
                )
                db.session.add(producto)
                productos_creados += 1
                print(f"   ✓ {prod_data['codigo']} - {prod_data['nombre']}")
        
        db.session.commit()
        print(f"\n   Total productos creados: {productos_creados}")
        
        # ====== 3. CREAR SERVICIOS RELACIONADOS ======
        print("\n3. Creando servicios relacionados con Gunpla...")
        
        servicios = [
            {
                'codigo': 'SRV-ARMADO-BASICO',
                'nombre': 'Armado Básico de Gunpla',
                'descripcion': 'Servicio de armado para kits HG, SD y NG. Incluye corte de piezas, limado básico y ensamble.',
                'precio_base': 100000
            },
            {
                'codigo': 'SRV-ARMADO-AVANZADO',
                'nombre': 'Armado Avanzado (RG/MG)',
                'descripcion': 'Servicio de armado para kits RG y MG. Incluye armado completo con atención al detalle y aplicación de calcomanías.',
                'precio_base': 200000
            },
            {
                'codigo': 'SRV-ARMADO-PREMIUM',
                'nombre': 'Armado Premium (PG/MS)',
                'descripcion': 'Servicio de armado para kits Perfect Grade y Mega Size. Incluye armado experto, instalación de LEDs si aplica.',
                'precio_base': 400000
            },
            {
                'codigo': 'SRV-PINTURA-BASICA',
                'nombre': 'Pintura Básica',
                'descripcion': 'Pintura de detalles básicos con marcadores Gundam. Resalta panel lines y detalles pequeños.',
                'precio_base': 80000
            },
            {
                'codigo': 'SRV-PINTURA-COMPLETA',
                'nombre': 'Pintura Completa Profesional',
                'descripcion': 'Pintura completa con aerógrafo. Incluye imprimación, pintura base, detalles y capa protectora.',
                'precio_base': 350000
            },
            {
                'codigo': 'SRV-CUSTOM',
                'nombre': 'Personalización Custom',
                'descripcion': 'Modificación y personalización del kit. Incluye kitbashing, scribing, adding details. Precio según complejidad.',
                'precio_base': 500000
            },
            {
                'codigo': 'SRV-REPARACION',
                'nombre': 'Reparación de Piezas',
                'descripcion': 'Reparación de piezas rotas o dañadas. Incluye pegado, masillado y repintura si es necesario.',
                'precio_base': 60000
            },
            {
                'codigo': 'SRV-TOPCOAT',
                'nombre': 'Aplicación de Top Coat',
                'descripcion': 'Aplicación de capa protectora final (mate, semi-mate o brillante). Protege la pintura y calcomanías.',
                'precio_base': 50000
            },
        ]
        
        servicios_creados = 0
        for serv_data in servicios:
            servicio_existe = TipoServicio.query.filter_by(codigo=serv_data['codigo']).first()
            if not servicio_existe:
                servicio = TipoServicio(
                    codigo=serv_data['codigo'],
                    nombre=serv_data['nombre'],
                    descripcion=serv_data['descripcion'],
                    precio_base=serv_data['precio_base'],
                    activo=True
                )
                db.session.add(servicio)
                servicios_creados += 1
                print(f"   ✓ {serv_data['codigo']} - {serv_data['nombre']} (Gs. {serv_data['precio_base']:,.0f})")
        
        db.session.commit()
        print(f"\n   Total servicios creados: {servicios_creados}")
        
        # ====== 4. CREAR PROVEEDOR ======
        print("\n4. Creando proveedor...")
        
        proveedor = Proveedor.query.filter_by(codigo='PROV-GUNPLA-01').first()
        if not proveedor:
            proveedor = Proveedor(
                codigo='PROV-GUNPLA-01',
                razon_social='Bandai Hobby Import S.A.',
                ruc='80055555-6',
                direccion='Av. Japón 456, Asunción',
                telefono='021-555-1234',
                email='ventas@bandaiimport.com.py',
                contacto_nombre='Juan Yamamoto',
                contacto_telefono='0981-123456',
                tipo_proveedor='internacional',
                activo=True,
                observaciones='Importador oficial de productos Bandai. Entrega en 15-30 días.'
            )
            db.session.add(proveedor)
            db.session.commit()
            print(f"   ✓ Proveedor '{proveedor.razon_social}' creado")
        else:
            print(f"   ℹ Proveedor ya existe")
        
        # ====== 5. CREAR ÓRDENES DE COMPRA SIN PAGAR ======
        print("\n5. Creando órdenes de compra de prueba (sin pagar)...")
        
        # Obtener usuario admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            print("   ⚠ No se encontró usuario admin. Se necesita para crear compras.")
            return
        
        # Compra 1: Mezcla de productos
        compra1_existe = Compra.query.filter_by(numero_compra='COMP-TEST-001').first()
        if not compra1_existe:
            compra1 = Compra(
                numero_compra='COMP-TEST-001',
                tipo='producto',
                descripcion='Pedido de reposición mixto - Kits HG y RG',
                fecha_compra=datetime.now(),
                fecha_documento=date.today(),
                proveedor_id=proveedor.id,
                usuario_registra_id=admin.id,
                subtotal=0,
                iva=0,
                total=0,
                estado='registrada',
                stock_actualizado=False,
                observaciones='Orden de prueba - Pendiente de pago'
            )
            db.session.add(compra1)
            db.session.flush()
            
            # Agregar detalles
            productos_compra1 = [
                ('HG-001', 10),
                ('HG-002', 8),
                ('RG-001', 5),
                ('SD-001', 15)
            ]
            
            subtotal1 = 0
            for codigo, cantidad in productos_compra1:
                prod = Producto.query.filter_by(codigo=codigo).first()
                if prod:
                    detalle = CompraDetalle(
                        compra_id=compra1.id,
                        producto_id=prod.id,
                        cantidad=cantidad,
                        precio_unitario=prod.precio_compra,
                        subtotal=prod.precio_compra * cantidad
                    )
                    db.session.add(detalle)
                    subtotal1 += prod.precio_compra * cantidad
            
            compra1.subtotal = subtotal1
            compra1.iva = subtotal1 * Decimal('0.10')
            compra1.total = subtotal1 + compra1.iva
            
            print(f"   ✓ {compra1.numero_compra} - Total: Gs. {compra1.total:,.0f}")
        
        # Compra 2: Productos premium
        compra2_existe = Compra.query.filter_by(numero_compra='COMP-TEST-002').first()
        if not compra2_existe:
            compra2 = Compra(
                numero_compra='COMP-TEST-002',
                tipo='producto',
                descripcion='Pedido especial - Master Grade y Perfect Grade',
                fecha_compra=datetime.now(),
                fecha_documento=date.today(),
                proveedor_id=proveedor.id,
                usuario_registra_id=admin.id,
                subtotal=0,
                iva=0,
                total=0,
                estado='registrada',
                stock_actualizado=False,
                observaciones='Orden de prueba - Para clientes premium'
            )
            db.session.add(compra2)
            db.session.flush()
            
            # Agregar detalles
            productos_compra2 = [
                ('MG-001', 4),
                ('MG-002', 2),
                ('PG-001', 1),
                ('MS-001', 2)
            ]
            
            subtotal2 = 0
            for codigo, cantidad in productos_compra2:
                prod = Producto.query.filter_by(codigo=codigo).first()
                if prod:
                    detalle = CompraDetalle(
                        compra_id=compra2.id,
                        producto_id=prod.id,
                        cantidad=cantidad,
                        precio_unitario=prod.precio_compra,
                        subtotal=prod.precio_compra * cantidad
                    )
                    db.session.add(detalle)
                    subtotal2 += prod.precio_compra * cantidad
            
            compra2.subtotal = subtotal2
            compra2.iva = subtotal2 * Decimal('0.10')
            compra2.total = subtotal2 + compra2.iva
            
            print(f"   ✓ {compra2.numero_compra} - Total: Gs. {compra2.total:,.0f}")
        
        # Compra 3: Solo SD para stock
        compra3_existe = Compra.query.filter_by(numero_compra='COMP-TEST-003').first()
        if not compra3_existe:
            compra3 = Compra(
                numero_compra='COMP-TEST-003',
                tipo='producto',
                descripcion='Reposición Super Deformed',
                fecha_compra=datetime.now(),
                fecha_documento=date.today(),
                proveedor_id=proveedor.id,
                usuario_registra_id=admin.id,
                subtotal=0,
                iva=0,
                total=0,
                estado='registrada',
                stock_actualizado=False,
                observaciones='Orden de prueba - Alta rotación'
            )
            db.session.add(compra3)
            db.session.flush()
            
            # Agregar detalles
            productos_compra3 = [
                ('SD-001', 30),
                ('SD-002', 25)
            ]
            
            subtotal3 = 0
            for codigo, cantidad in productos_compra3:
                prod = Producto.query.filter_by(codigo=codigo).first()
                if prod:
                    detalle = CompraDetalle(
                        compra_id=compra3.id,
                        producto_id=prod.id,
                        cantidad=cantidad,
                        precio_unitario=prod.precio_compra,
                        subtotal=prod.precio_compra * cantidad
                    )
                    db.session.add(detalle)
                    subtotal3 += prod.precio_compra * cantidad
            
            compra3.subtotal = subtotal3
            compra3.iva = subtotal3 * Decimal('0.10')
            compra3.total = subtotal3 + compra3.iva
            
            print(f"   ✓ {compra3.numero_compra} - Total: Gs. {compra3.total:,.0f}")
        
        db.session.commit()
        
        # ====== RESUMEN FINAL ======
        print("\n" + "="*60)
        print("✅ DATOS INSERTADOS EXITOSAMENTE")
        print("="*60)
        
        total_productos = Producto.query.filter_by(categoria_id=categoria_gunpla.id).count()
        total_servicios = TipoServicio.query.filter(TipoServicio.codigo.like('SRV-%')).count()
        total_compras = Compra.query.filter(Compra.numero_compra.like('COMP-TEST-%')).count()
        
        print(f"\n📦 Productos Gunpla: {total_productos}")
        print(f"🔧 Servicios: {total_servicios}")
        print(f"📋 Órdenes de compra (sin pagar): {total_compras}")
        
        print("\n💰 TOTALES DE ÓRDENES DE COMPRA:")
        compras = Compra.query.filter(Compra.numero_compra.like('COMP-TEST-%')).all()
        total_general = 0
        for compra in compras:
            print(f"   • {compra.numero_compra}: Gs. {compra.total:,.0f}")
            total_general += compra.total
        print(f"\n   TOTAL GENERAL: Gs. {total_general:,.0f}")
        
        print("\n" + "="*60)
        print("Ahora puedes:")
        print("  1. Ver las compras en: Compras > Listar")
        print("  2. Pagar las compras desde: Compras > Ver compra > Registrar Pago")
        print("  3. Ver productos en: Productos > Listar")
        print("  4. Crear ventas con estos productos")
        print("  5. Crear servicios de armado/personalización")
        print("="*60 + "\n")

if __name__ == '__main__':
    insertar_datos_gunpla()
