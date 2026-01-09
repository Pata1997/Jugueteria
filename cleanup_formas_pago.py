"""
Marca como inactivos los duplicados de formas de pago conservando una instancia por código/nombre.
Ejecutar con el entorno virtual activo: python cleanup_formas_pago.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.venta import FormaPago


def cleanup_formas_pago():
    app = create_app()
    with app.app_context():
        vistos = {}
        inactivados = []
        registros = FormaPago.query.order_by(FormaPago.nombre, FormaPago.id).all()
        for fp in registros:
            clave = (fp.codigo or '').strip().lower() or (fp.nombre or '').strip().lower() or str(fp.id)
            guardado = vistos.get(clave)
            if guardado is None:
                vistos[clave] = fp
                continue
            if (not getattr(guardado, 'activo', False)) and getattr(fp, 'activo', False):
                vistos[clave] = fp
                continue
            if getattr(fp, 'activo', False):
                fp.activo = False
                inactivados.append(fp)
        db.session.commit()
        print(f"Claves únicas detectadas: {len(vistos)}")
        print(f"Formas de pago inactivadas: {len(inactivados)}")
        if inactivados:
            print("IDs inactivados:", ', '.join(str(f.id) for f in inactivados))


if __name__ == '__main__':
    cleanup_formas_pago()
