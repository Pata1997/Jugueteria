from app import create_app, db
from app.models.configuracion import ConfiguracionEmpresa

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        empresa = ConfiguracionEmpresa.query.first()
        if empresa:
            print(f"[DIAG] Empresa encontrada: {empresa.nombre_empresa} (ID: {empresa.id})")
            print(f"RUC: {empresa.ruc}")
            print(f"Dirección: {empresa.direccion}")
            print(f"Email: {empresa.email}")
        else:
            print("[DIAG] No se encontró ninguna empresa en la base de datos.")
