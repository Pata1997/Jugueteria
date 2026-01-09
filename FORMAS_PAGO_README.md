# Sistema de Formas de Pago Múltiples y Vuelto

## Descripción

Sistema completo de facturación con **formas de pago múltiples** (efectivo, tarjeta débito, tarjeta crédito, cheque, transferencia) y **cálculo automático de vuelto**.

## Características Implementadas

✅ Múltiples formas de pago simultáneamente en una sola factura
✅ Cálculo automático de vuelto en tiempo real
✅ Validación de efectivo suficiente para el vuelto
✅ Generación de tickets con detalle de formas de pago y vuelto
✅ Modal de confirmación con monto de vuelto
✅ Deshabilitación automática del botón "Facturar" si el pago es insuficiente

---

## Archivos Modificados/Creados

### Modelos
- `app/models/venta.py` - Actualizado modelo `FormaPago` con campos `descripcion` y `requiere_referencia`

### Rutas
- `app/routes/ventas.py`:
  - Actualizada ruta `facturar()` para cargar formas de pago y calcular vuelto
  - Nueva ruta `confirmar_vuelto()` para mostrar modal de confirmación
  - Nueva ruta `descargar_ticket()` para generar ticket con formas de pago

### Templates
- `app/templates/ventas/facturar.html`:
  - Formas de pago cargadas dinámicamente desde BD
  - Cálculo de vuelto en tiempo real
  - Validación de efectivo para vuelto
  - Alerta visual cuando hay vuelto sin suficiente efectivo
  
- `app/templates/ventas/confirmar_vuelto.html` (NUEVO):
  - Modal de confirmación con monto de vuelto
  - Descarga automática de ticket
  - Redirección automática después de 10 segundos

### Utilidades
- `app/utils/ticket.py` - Actualizado generador de tickets para incluir formas de pago y vuelto

### Scripts
- `inicializar_formas_pago.py` - Script para inicializar formas de pago en BD
- `migracion_formas_pago.sql` - Script SQL para migrar base de datos
- `INSTRUCCIONES_MIGRACION.py` - Guía de migración

---

## Instalación y Configuración

### Paso 1: Migrar la Base de Datos

**Opción A: Con Flask-Migrate**
```bash
# Generar migración
flask db migrate -m "Agregar descripcion y requiere_referencia a FormaPago"

# Aplicar migración
flask db upgrade
```

**Opción B: Con SQL Directo**
```bash
# Ejecutar script SQL
psql -U usuario -d nombre_bd -f migracion_formas_pago.sql
```

### Paso 2: Inicializar Formas de Pago

```bash
python inicializar_formas_pago.py
```

Este script creará las siguientes formas de pago:
- Efectivo (sin referencia)
- Tarjeta de Débito (requiere referencia)
- Tarjeta de Crédito (requiere referencia)
- Cheque (requiere referencia)
- Transferencia Bancaria (requiere referencia)

### Paso 3: Reiniciar el Servidor

```bash
flask run
```

---

## Uso del Sistema

### 1. Facturar una Venta

1. Ir a **Ventas → Listar Ventas**
2. Seleccionar una venta pendiente y hacer clic en **"Facturar"**
3. En la pantalla de facturación:
   - Seleccionar forma de pago
   - Ingresar monto
   - Agregar referencia si es necesario (cheque, tarjeta, etc.)
   - Hacer clic en **"Agregar otra forma de pago"** para pagos mixtos

### 2. Cálculo Automático

El sistema calcula automáticamente:
- **Total Pagos**: Suma de todos los pagos ingresados
- **Faltante**: Cuánto falta para cubrir el total
- **Vuelto**: Cuánto se debe devolver al cliente

### 3. Validaciones

- ✅ El botón "Facturar y Cobrar" se **habilita** solo cuando: Total Pagos ≥ Total a Cobrar
- ⚠️ Si hay vuelto, el sistema verifica que haya **suficiente efectivo** para devolverlo
- ❌ No permite facturar con pago insuficiente

### 4. Confirmación y Ticket

Después de facturar:
1. Se muestra un **modal con el vuelto** a devolver
2. Se **descarga automáticamente** el ticket con:
   - Detalle de productos/servicios
   - Formas de pago utilizadas
   - Total recibido
   - Vuelto
3. Presionar cualquier tecla para continuar

---

## Ejemplos de Uso

### Caso 1: Pago Exacto en Efectivo
```
Total: 350.000 Gs.
Forma de Pago: Efectivo
Monto: 350.000 Gs.
---
Vuelto: 0 Gs. ✓
```

### Caso 2: Pago en Efectivo con Vuelto
```
Total: 350.000 Gs.
Forma de Pago: Efectivo
Monto: 400.000 Gs.
---
Vuelto: 50.000 Gs. ✓
Modal muestra: "Vuelto a Devolver: 50.000 Gs."
```

### Caso 3: Pago Mixto (Efectivo + Tarjeta)
```
Total: 1.200.000 Gs.
Forma de Pago 1: Efectivo - 800.000 Gs.
Forma de Pago 2: Tarjeta Débito - 400.000 Gs.
---
Total Pagos: 1.200.000 Gs.
Vuelto: 0 Gs. ✓
```

### Caso 4: Pago Mixto con Vuelto
```
Total: 500.000 Gs.
Forma de Pago 1: Efectivo - 300.000 Gs.
Forma de Pago 2: Tarjeta Crédito - 300.000 Gs.
---
Total Pagos: 600.000 Gs.
Vuelto: 100.000 Gs. ✓
Efectivo disponible: 300.000 Gs. ✓
```

### Caso 5: Advertencia - Vuelto sin Suficiente Efectivo
```
Total: 600.000 Gs.
Forma de Pago: Tarjeta Crédito - 700.000 Gs.
---
Total Pagos: 700.000 Gs.
Vuelto requerido: 100.000 Gs.
Efectivo disponible: 0 Gs.
⚠️ Advertencia: "Faltan 100.000 Gs. en efectivo para cubrir el vuelto"
```

---

## Formato del Ticket

```
        JUGUETERÍA EJEMPLO
    De: Juan Pérez
    RUC: 80012345-6 - Tel: 0981-123456
    Av. Principal 123
----------------------------------------
TIMBRADO: 12345678
Vence: 31/DIC/2026
FACTURA Nro: 001-001-0000123
Fecha: 06/01/2026 14:30
Condición: CONTADO
----------------------------------------
CLIENTE: CLIENTE FINAL
RUC/CI: 1234567
----------------------------------------
ITEM         CANT   IVA    PRECIO   SUBT
----------------------------------------
Producto 1      2   10%    150.000  300.000
Servicio 1      1   10%     50.000   50.000
----------------------------------------
SUBTOTAL 10%:                     350.000
----------------------------------------
TOTAL A PAGAR:                    350.000 Gs.
----------------------------------------
FORMAS DE PAGO
----------------------------------------
Efectivo:                         400.000 Gs.
----------------------------------------
TOTAL RECIBIDO:                   400.000 Gs.
VUELTO:                            50.000 Gs.
----------------------------------------
TOTAL EN LETRAS: 350.000
guaraníes.

LIQUIDACIÓN DEL IVA
IVA 10%:  31.818
TOTAL IVA:  31.818
----------------------------------------
    ¡Gracias por su compra!
    Original: Cliente (Blanco)
```

---

## Validaciones Implementadas

### Frontend (JavaScript)
- ✅ Deshabilitar botón "Facturar" si pago insuficiente
- ✅ Cambiar color del resumen (amarillo → verde) cuando se completa el pago
- ✅ Calcular vuelto en tiempo real
- ✅ Validar efectivo suficiente para vuelto
- ✅ Mostrar alertas visuales cuando hay inconsistencias
- ✅ Permitir Enter para agregar nueva forma de pago

### Backend (Python)
- ✅ Validar que haya al menos una forma de pago
- ✅ Validar que el total pagado cubra el total de la venta
- ✅ Calcular vuelto correctamente
- ✅ Registrar cada pago por separado en la BD
- ✅ Actualizar estado de pago de la venta
- ✅ Generar ticket con detalle completo

---

## Estructura de Datos

### Tabla `formas_pago`
```sql
CREATE TABLE formas_pago (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    requiere_referencia BOOLEAN DEFAULT FALSE
);
```

### Tabla `pagos`
```sql
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id),
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forma_pago_id INTEGER REFERENCES formas_pago(id),
    monto NUMERIC(12, 2) NOT NULL,
    referencia VARCHAR(100),
    banco VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'confirmado',
    observaciones TEXT
);
```

---

## Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│           FACTURA LISTA PARA COBRAR                         │
│           Total: 350.000 Gs.                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
            ┌──────────────────────────────┐
            │  Agregar Formas de Pago      │
            │  - Efectivo: 200.000 Gs.     │
            │  - Tarjeta: 200.000 Gs.      │
            └──────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────┐
        │  Total Recibido: 400.000 Gs.        │
        │  Vuelto: 50.000 Gs. ✓               │
        │  Efectivo: 200.000 Gs. ✓            │
        │  Botón "Facturar" HABILITADO        │
        └─────────────────────────────────────┘
                            ↓
    ┌───────────────────────────────────────────┐
    │  Click "Facturar y Cobrar"                │
    │  → Backend valida y procesa pagos         │
    │  → Guarda Venta + Pagos en BD             │
    │  → Calcula vuelto                         │
    └───────────────────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────┐
        │      MODAL: VUELTO 50.000 Gs.       │
        │  "Presione cualquier tecla"         │
        │  (Descarga ticket automático)        │
        └─────────────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────┐
        │   ✓ Factura Completada              │
        │   → Lista de ventas                  │
        └─────────────────────────────────────┘
```

---

## Consideraciones Técnicas

### Moneda
- **Guaraní Paraguayo (Gs.)**
- Separador de miles: punto (.)
- Ejemplo: 1.234.567 Gs.

### IVA
- **IVA 10%**: Productos gravados
- **IVA 5%**: Productos con tasa reducida
- **Exentas**: Productos sin IVA
- Servicios siempre llevan **IVA 10%** (ley paraguaya)

### Redondeo
- Todos los montos se redondean al guaraní más cercano
- JavaScript: `Math.round()`
- Python: `int()`

### Seguridad
- ✅ Validación en cliente Y servidor
- ✅ Auditoría de transacciones
- ✅ Solo usuarios autenticados pueden facturar
- ✅ Transacciones atómicas (rollback en caso de error)

---

## Solución de Problemas

### Error: "Debe registrar al menos una forma de pago"
- **Causa**: No se agregó ninguna forma de pago
- **Solución**: Agregar al menos una forma de pago antes de facturar

### Error: "El monto recibido no cubre el total de la factura"
- **Causa**: Total de pagos < Total de la venta
- **Solución**: Completar el monto faltante o ajustar los pagos

### Advertencia: "Falta efectivo para cubrir el vuelto"
- **Causa**: Vuelto > Efectivo ingresado
- **Solución**: Aumentar el monto en efectivo o solicitar pago exacto

### No se descarga el ticket
- **Causa**: Bloqueador de ventanas emergentes
- **Solución**: Permitir ventanas emergentes en el navegador

---

## Próximas Mejoras (Opcional)

- [ ] Impresión directa en impresora térmica
- [ ] Generación de tickets en PDF
- [ ] Historial de pagos por cliente
- [ ] Reportes de formas de pago más utilizadas
- [ ] Integración con pasarelas de pago online
- [ ] QR de transferencia bancaria
- [ ] Envío de ticket por WhatsApp/Email

---

## Soporte

Para consultas o problemas, revisar:
- `app/routes/ventas.py` - Lógica de facturación
- `app/templates/ventas/facturar.html` - Interfaz de usuario
- `app/utils/ticket.py` - Generación de tickets
- `inicializar_formas_pago.py` - Inicialización de formas de pago

---

## Licencia

Sistema desarrollado para Juguetería - Paraguay
Basado en el modelo del sistema de consultorio médico
