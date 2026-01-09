"""
Script para inicializar las formas de pago en el sistema.
Ejecutar una sola vez después de la migración de la base de datos.
"""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from app.models.venta import FormaPago

def inicializar_formas_pago():
    """Crea las formas de pago predefinidas en el sistema"""
    
    formas_predefinidas = [
        {
            'codigo': 'efectivo',
            'nombre': 'Efectivo',
            'descripcion': 'Pago en efectivo',
            'requiere_referencia': False
        },
        {
            'codigo': 'tarjeta_debito',
            'nombre': 'Tarjeta de Débito',
            'descripcion': 'Pago con tarjeta de débito',
            'requiere_referencia': True
        },
        {
            'codigo': 'tarjeta_credito',
            'nombre': 'Tarjeta de Crédito',
            'descripcion': 'Pago con tarjeta de crédito',
            'requiere_referencia': True
        },
        {
            'codigo': 'cheque',
            'nombre': 'Cheque',
            'descripcion': 'Pago con cheque',
            'requiere_referencia': True
        },
        {
            'codigo': 'transferencia',
            'nombre': 'Transferencia Bancaria',
            'descripcion': 'Pago por transferencia bancaria',
            'requiere_referencia': True
        },
    ]
    
    app = create_app()
    with app.app_context():
        print("Inicializando formas de pago...")
        
        for forma_data in formas_predefinidas:
            # Verificar si ya existe
            forma_existente = FormaPago.query.filter_by(codigo=forma_data['codigo']).first()
            
            if not forma_existente:
                forma = FormaPago(
                    codigo=forma_data['codigo'],
                    nombre=forma_data['nombre'],
                    descripcion=forma_data['descripcion'],
                    activo=True,
                    requiere_referencia=forma_data['requiere_referencia']
                )
                db.session.add(forma)
                print(f"✓ Creada forma de pago: {forma_data['nombre']}")
            else:
                # Actualizar si ya existe
                forma_existente.nombre = forma_data['nombre']
                forma_existente.descripcion = forma_data['descripcion']
                forma_existente.requiere_referencia = forma_data['requiere_referencia']
                print(f"✓ Actualizada forma de pago: {forma_data['nombre']}")
        
        try:
            db.session.commit()
            print("\n✓ Formas de pago inicializadas correctamente")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error al guardar formas de pago: {str(e)}")
            raise

if __name__ == '__main__':
    inicializar_formas_pago()
