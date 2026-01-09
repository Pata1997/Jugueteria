# GUÍA DE INICIO RÁPIDO

## Pasos para ejecutar el sistema por primera vez

### 1. Verificar que Python está instalado
```bash
python --version
```
Debe mostrar Python 3.8 o superior.

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual
**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar PostgreSQL

**Opción A - Instalar PostgreSQL localmente:**
1. Descargar de: https://www.postgresql.org/download/windows/
2. Instalar con puerto 5432 (por defecto)
3. Configurar password para usuario postgres

**Opción B - Usar PostgreSQL existente**

Crear la base de datos:
```sql
-- Conectarse a PostgreSQL con pgAdmin o psql
CREATE DATABASE jugueteria_db;
```

### 6. Configurar archivo .env

Copiar `.env.example` a `.env`:
```bash
copy .env.example .env
```

Editar `.env` y configurar la conexión a PostgreSQL:
```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/jugueteria_db
```

Reemplazar `TU_PASSWORD` con tu contraseña de PostgreSQL.

### 7. Inicializar la base de datos
```bash
python init_db.py
```

Este comando:
- Crea todas las tablas
- Inserta datos iniciales
- Crea usuarios de prueba

### 8. Ejecutar la aplicación
```bash
python app.py
```

O usando Flask CLI:
```bash
flask run
```

### 9. Acceder al sistema

Abrir navegador en: **http://localhost:5000**

**Usuarios de prueba:**
- Usuario: `admin` | Contraseña: `admin123` (Administrador completo)
- Usuario: `vendedor` | Contraseña: `vendedor123` (Vendedor)
- Usuario: `cajero` | Contraseña: `cajero123` (Cajero)

---

## Solución de Problemas Comunes

### Error: "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Error: "Could not connect to database"
- Verificar que PostgreSQL esté corriendo
- Verificar que el DATABASE_URL en .env sea correcto
- Verificar que la base de datos exista

### Error: "Address already in use"
- Otro proceso está usando el puerto 5000
- Cambiar el puerto en app.py: `app.run(port=5001)`

### Error en Windows: "cannot be loaded because running scripts is disabled"
Ejecutar PowerShell como administrador:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Primer Uso del Sistema

### 1. Configurar la Empresa
1. Ir a **Configuración → Empresa**
2. Completar:
   - Nombre de la empresa
   - RUC
   - Dirección y contactos
   - Datos de timbrado (para facturación)

### 2. Crear Productos
1. Ir a **Productos → Categorías** y crear categorías
2. Ir a **Productos → Nuevo Producto**
3. Crear productos para venta
4. Crear insumos para servicios

### 3. Crear Clientes
1. Ir a **Clientes → Nuevo Cliente**
2. Registrar clientes con sus datos

### 4. Configurar Empleados
1. Ir a **RRHH → Empleados → Nuevo Empleado**
2. Crear técnicos y personal

### 5. Abrir Caja
1. Ir a **Ventas → Apertura de Caja**
2. Seleccionar caja y monto inicial
3. Ahora puede realizar ventas

### 6. Realizar Primera Venta
1. Ir a **Ventas → Nueva Venta**
2. Seleccionar cliente
3. Agregar productos
4. Registrar pago
5. Guardar e imprimir factura

---

## Flujos Completos

### Servicio Completo
1. **Clientes → Nueva Solicitud de Servicio**
   - Registrar lo que el cliente necesita
   
2. **Servicios → Crear Presupuesto**
   - Elaborar presupuesto con costos detallados
   
3. **Cliente aprueba → Aprobar Presupuesto**
   
4. **Servicios → Nueva Orden de Servicio**
   - Asignar a técnico
   - Registrar insumos utilizados
   - Actualizar estado
   
5. **Ventas → Nueva Venta**
   - Facturar el servicio realizado

### Compra Completa
1. **Compras → Proveedores → Nuevo Proveedor**
   
2. **Compras → Nuevo Pedido**
   - Solicitar productos necesarios
   
3. **Compras → Registrar Presupuesto de Proveedor**
   - Comparar precios
   
4. **Compras → Nueva Orden de Compra**
   - Aprobar compra
   
5. **Compras → Registrar Compra**
   - Al recibir mercadería
   - Stock se actualiza automáticamente
   - Si es a crédito, se crea cuenta por pagar

---

## Atajos y Tips

### Búsquedas Rápidas
- La mayoría de listados tienen búsqueda en tiempo real
- Los campos de cliente/producto tienen autocompletado

### Dashboard
- Muestra resumen de operaciones
- Alertas de stock bajo
- Servicios pendientes

### Reportes
- Todos los reportes se pueden exportar a PDF
- Configurar fechas para filtrar períodos

### Cierre de Caja
- Al finalizar el día hacer cierre de caja
- Comparar monto físico vs sistema
- Ver arqueo detallado

---

## Estructura de Permisos por Rol

| Función | Admin | Vendedor | Cajero |
|---------|-------|----------|--------|
| Dashboard | ✓ | ✓ | ✓ |
| Clientes | ✓ | ✓ | ✓ |
| Productos | ✓ | ✓ | Solo lectura |
| Servicios | ✓ | ✓ | Solo lectura |
| Ventas | ✓ | ✓ | ✓ |
| Compras | ✓ | ✗ | ✗ |
| RRHH | ✓ | ✗ | ✗ |
| Reportes | ✓ | ✓ | ✓ |
| Configuración | ✓ | ✗ | ✗ |

---

## Backup de Base de Datos

### Crear backup
```bash
pg_dump -U postgres -d jugueteria_db > backup.sql
```

### Restaurar backup
```bash
psql -U postgres -d jugueteria_db < backup.sql
```

**Recomendación:** Hacer backups diarios automáticos.

---

## Contacto Soporte

Para problemas técnicos o consultas, contactar al administrador del sistema.
