# Sistema de Gestión para Juguetería

Sistema completo de gestión empresarial desarrollado con Flask, PostgreSQL y ReportLab para una juguetería que ofrece venta de productos y servicios de montaje, reparación y personalización.

## Características Principales

### Módulos Implementados

1. **Gestión de Clientes**
   - Registro de clientes particulares, empresas y gobierno
   - Control de límites de crédito
   - Descuentos especiales
   - Historial de compras y servicios

2. **Gestión de Productos e Inventario**
   - Productos terminados e insumos separados
   - Control de stock con alertas de stock mínimo
   - Trazabilidad de movimientos
   - Historial de cambios de precios
   - Categorización de productos

3. **Gestión de Servicios**
   - Solicitudes de servicio (montaje, reparación, personalización, alquiler)
   - Presupuestos con aprobación del cliente
   - Órdenes de servicio con seguimiento por estados
   - Registro de insumos utilizados
   - Sistema de reclamos con seguimiento

4. **Ventas y Facturación**
   - Punto de venta con soporte para productos y servicios
   - Ventas mixtas (productos + servicios)
   - Múltiples formas de pago (efectivo, tarjetas, cheques, transferencias)
   - Ventas a crédito hasta 30 días
   - Notas de crédito y débito
   - Gestión de caja (apertura, cierre, arqueo)
   - Cuentas por cobrar

5. **Compras**
   - Registro de proveedores
   - Pedidos de compra
   - Comparación de presupuestos de proveedores
   - Órdenes de compra
   - Registro de compras con actualización automática de stock
   - Cuentas por pagar
   - Pagos a proveedores

6. **Recursos Humanos**
   - Gestión de empleados
   - Control de asistencia
   - Solicitudes de vacaciones
   - Solicitudes de permisos
   - Horarios de atención

7. **Reportes**
   - Reporte de ventas por período
   - Reporte de productos
   - Reporte de servicios
   - Reporte de clientes
   - Generación de PDFs con ReportLab
   - Impresión de facturas

8. **Configuración**
   - Configuración de datos de la empresa
   - Gestión de usuarios y permisos
   - Configuración de timbrado y facturación
   - Configuración de IVA

## Tecnologías Utilizadas

- **Backend**: Flask 3.0
- **Base de Datos**: PostgreSQL
- **ORM**: SQLAlchemy con Flask-SQLAlchemy
- **Migraciones**: Flask-Migrate (Alembic)
- **Autenticación**: Flask-Login
- **Generación de PDFs**: ReportLab
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Seguridad**: Flask-Bcrypt para hash de contraseñas

## Requisitos Previos

- Python 3.8 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar el repositorio o descargar los archivos

```bash
cd Jugueteria
```

### 2. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

Crear la base de datos en PostgreSQL:

```sql
CREATE DATABASE jugueteria_db;
CREATE USER jugueteria_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE jugueteria_db TO jugueteria_user;
```

### 5. Configurar variables de entorno

Crear archivo `.env` basado en `.env.example`:

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Editar `.env` con tus configuraciones:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-muy-segura-cambiar-en-produccion
DATABASE_URL=postgresql://jugueteria_user:tu_password_seguro@localhost:5432/jugueteria_db
```

### 6. Inicializar la base de datos

```bash
python init_db.py
```

Este script creará todas las tablas y datos iniciales incluyendo:
- Usuario administrador
- Usuarios de ejemplo
- Configuración básica
- Tipos de servicio
- Categorías
- Formas de pago

### 7. Ejecutar la aplicación

```bash
python app.py
```

O usando Flask CLI:

```bash
flask run
```

La aplicación estará disponible en: `http://localhost:5000`

## Usuarios por Defecto

Después de inicializar la base de datos, podrás acceder con:

| Usuario  | Contraseña  | Rol    |
|----------|-------------|--------|
| admin    | admin123    | Administrador |
| vendedor | vendedor123 | Vendedor |
| cajero   | cajero123   | Cajero |

**IMPORTANTE**: Cambiar estas contraseñas en producción.

## Estructura del Proyecto

```
Jugueteria/
│
├── app/
│   ├── __init__.py
│   ├── models/              # Modelos de base de datos
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── cliente.py
│   │   ├── producto.py
│   │   ├── servicio.py
│   │   ├── venta.py
│   │   ├── compra.py
│   │   ├── empleado.py
│   │   └── configuracion.py
│   │
│   ├── routes/              # Rutas/Controladores
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── clientes.py
│   │   ├── productos.py
│   │   ├── servicios.py
│   │   ├── ventas.py
│   │   ├── compras.py
│   │   ├── rrhh.py
│   │   ├── reportes.py
│   │   └── configuracion.py
│   │
│   ├── templates/           # Templates HTML
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── clientes/
│   │   ├── productos/
│   │   ├── servicios/
│   │   ├── ventas/
│   │   ├── compras/
│   │   ├── rrhh/
│   │   ├── reportes/
│   │   └── configuracion/
│   │
│   └── static/              # Archivos estáticos
│       └── uploads/
│
├── migrations/              # Migraciones de base de datos
├── app.py                   # Punto de entrada de la aplicación
├── config.py                # Configuración
├── init_db.py              # Script de inicialización
├── requirements.txt         # Dependencias
├── .env.example            # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## Flujos Principales

### Flujo de Servicio
1. Cliente solicita servicio → **Solicitud de Servicio**
2. Se elabora → **Presupuesto**
3. Cliente aprueba presupuesto
4. Se crea → **Orden de Servicio**
5. Técnico realiza el trabajo y registra insumos
6. Se finaliza el servicio
7. Se genera → **Venta/Factura**

### Flujo de Compra
1. Se identifica necesidad → **Pedido de Compra**
2. Se solicitan presupuestos a proveedores → **Presupuestos de Proveedores**
3. Se selecciona mejor opción → **Orden de Compra**
4. Se recibe mercadería → **Compra** (actualiza stock automáticamente)
5. Si es a crédito → Se genera **Cuenta por Pagar**

### Flujo de Venta
1. Cajero abre caja → **Apertura de Caja**
2. Se registra la venta (productos y/o servicios)
3. Se registran pagos (puede ser múltiples formas de pago)
4. Se descuenta stock automáticamente
5. Se genera factura con opción de imprimir PDF
6. Al finalizar el día → **Cierre de Caja** y **Arqueo**

## Migraciones de Base de Datos

Si necesitas hacer cambios en los modelos:

```bash
# Crear una migración
flask db migrate -m "Descripción del cambio"

# Aplicar migraciones
flask db upgrade

# Revertir última migración
flask db downgrade
```

## Desarrollo

### Agregar un nuevo módulo

1. Crear modelo en `app/models/`
2. Importar en `app/models/__init__.py`
3. Crear rutas en `app/routes/`
4. Registrar blueprint en `app.py`
5. Crear templates en `app/templates/`
6. Crear migración: `flask db migrate`
7. Aplicar migración: `flask db upgrade`

## Producción

### Recomendaciones para despliegue:

1. **Cambiar SECRET_KEY** a un valor seguro y aleatorio
2. **Usar FLASK_ENV=production**
3. **Configurar HTTPS**
4. **Usar un servidor WSGI** como Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
5. **Configurar Nginx** como proxy inverso
6. **Configurar backups automáticos** de PostgreSQL
7. **Cambiar todas las contraseñas por defecto**
8. **Configurar logs apropiados**

## Soporte y Contribuciones

Para reportar errores o solicitar funcionalidades, crear un issue en el repositorio.

## Licencia

Este proyecto es propiedad privada y está desarrollado para uso interno de la juguetería.

## Notas Importantes

- El sistema maneja la moneda en Guaraníes (Gs.)
- El IVA está configurado al 10% por defecto
- Las ventas a crédito tienen un máximo de 30 días
- El sistema genera números de factura automáticamente según el timbrado configurado
- Se mantiene auditoría de cambios críticos (precios, movimientos de stock)

## Próximas Mejoras Sugeridas

- [ ] Dashboard con gráficos interactivos
- [ ] Exportación de reportes a Excel
- [ ] Integración con servicios de mensajería (SMS/WhatsApp)
- [ ] App móvil para técnicos
- [ ] Portal web para clientes
- [ ] Integración con pasarelas de pago online
- [ ] Sistema de garantías
- [ ] Control de comisiones por vendedor
