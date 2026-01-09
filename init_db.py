"""
Script de inicialización de la base de datos
Crea las tablas y datos iniciales del sistema
"""

from app import create_app, db
from app.models import (
    Usuario, ConfiguracionEmpresa, Caja, FormaPago,
    TipoServicio, Categoria
)
from datetime import datetime

def init_db():
    app = create_app()
    
    with app.app_context():
        print("Eliminando tablas existentes...")
        db.drop_all()
        
        print("Creando tablas...")
        db.create_all()
        
        print("Creando datos iniciales...")
        
        # Usuario administrador
        admin = Usuario(
            username='admin',
            email='admin@jugueteria.com',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin',
            activo=True
        )
        admin.set_password('123456')
        db.session.add(admin)
        
        # Usuario recepción
        recepcion = Usuario(
            username='recepcion',
            email='recepcion@jugueteria.com',
            nombre='Recepción',
            apellido='Usuario',
            rol='vendedor',
            activo=True
        )
        recepcion.set_password('123456')
        db.session.add(recepcion)
        
        # Usuario cajero
        cajero = Usuario(
            username='cajero',
            email='cajero@jugueteria.com',
            nombre='Cajero',
            apellido='Usuario',
            rol='cajero',
            activo=True
        )
        cajero.set_password('123456')
        db.session.add(cajero)
        
        # Usuario ensamble (técnico)
        ensamble = Usuario(
            username='ensamble',
            email='ensamble@jugueteria.com',
            nombre='Técnico',
            apellido='Ensamble',
            rol='tecnico',
            activo=True
        )
        ensamble.set_password('123456')
        db.session.add(ensamble)
        
        # Configuración de la empresa
        config = ConfiguracionEmpresa(
            nombre_empresa='Juguetería El Mundo Feliz',
            ruc='80012345-6',
            direccion='Av. Principal 123, Asunción',
            telefono='021-123456',
            email='contacto@jugueteria.com',
            timbrado='12345678',
            numero_establecimiento='001',
            numero_expedicion='001',
            numero_factura_actual=1,
            fecha_vencimiento_timbrado=datetime(2026, 12, 31).date(),
            porcentaje_iva=10
        )
        db.session.add(config)
        
        # Cajas
        caja1 = Caja(numero_caja='CAJA-01', nombre='Caja Principal', activo=True)
        caja2 = Caja(numero_caja='CAJA-02', nombre='Caja Secundaria', activo=True)
        db.session.add(caja1)
        db.session.add(caja2)
        
        # Formas de Pago
        formas_pago = [
            FormaPago(codigo='EFECTIVO', nombre='Efectivo'),
            FormaPago(codigo='TARJETA_CREDITO', nombre='Tarjeta de Crédito'),
            FormaPago(codigo='TARJETA_DEBITO', nombre='Tarjeta de Débito'),
            FormaPago(codigo='CHEQUE', nombre='Cheque'),
            FormaPago(codigo='TRANSFERENCIA', nombre='Transferencia Bancaria'),
        ]
        for forma in formas_pago:
            db.session.add(forma)
        
        # Tipos de Servicio
        tipos_servicio = [
            TipoServicio(codigo='MONTAJE', nombre='Montaje de Juguetes', precio_base=50000),
            TipoServicio(codigo='REPARACION', nombre='Reparación', precio_base=75000),
            TipoServicio(codigo='PERSONALIZA', nombre='Personalización', precio_base=100000),
            TipoServicio(codigo='ALQUILER', nombre='Alquiler', precio_base=30000),
        ]
        for tipo in tipos_servicio:
            db.session.add(tipo)
        
        # Categorías de Productos
        categorias = [
            Categoria(codigo='JUGUETES', nombre='Juguetes', descripcion='Juguetes terminados'),
            Categoria(codigo='INSUMOS', nombre='Insumos', descripcion='Insumos para servicios'),
            Categoria(codigo='ACCESORIOS', nombre='Accesorios', descripcion='Accesorios y repuestos'),
            Categoria(codigo='EDUCATIVOS', nombre='Educativos', descripcion='Juguetes educativos'),
            Categoria(codigo='ELECTRONICOS', nombre='Electrónicos', descripcion='Juguetes electrónicos'),
        ]
        for cat in categorias:
            db.session.add(cat)
        
        db.session.commit()
        
        print("\n=== Base de datos inicializada correctamente ===")
        print("\nUsuarios creados:")
        print("  - Usuario: admin      | Contraseña: 123456 | Rol: Administrador")
        print("  - Usuario: recepcion  | Contraseña: 123456 | Rol: Vendedor")
        print("  - Usuario: cajero     | Contraseña: 123456 | Rol: Cajero")
        print("  - Usuario: ensamble   | Contraseña: 123456 | Rol: Técnico")
        print("\n==============================================\n")

if __name__ == '__main__':
    init_db()
