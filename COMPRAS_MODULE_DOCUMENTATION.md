# MÓDULO DE COMPRAS - FLUJO SIMPLIFICADO
## Implementación Completa

### ARQUITECTURA IMPLEMENTADA

El nuevo módulo de compras sigue un **flujo simplificado** que permite:
1. **Registrar** compras sin pagar inmediatamente
2. **Stock se actualiza automáticamente** si es tipo 'producto'
3. **Pagar posteriormente** con origen flexible:
   - **Caja Chica**: Descuenta de apertura de caja
   - **Otra Fuente**: No afecta caja (pago externo)
   - **Dejar a Crédito**: Crea Cuenta por Pagar

---

## COMPONENTES IMPLEMENTADOS

### 1. MODELOS (app/models/compra.py)

#### Compra (Actualizado)
```python
- numero_compra: str (único)
- tipo: str  # producto, servicio, factura, gasto
- descripcion: str
- fecha_compra: datetime
- fecha_documento: date
- proveedor_id: FK
- usuario_registra_id: FK
- subtotal, iva, total: Numeric
- estado: str  # registrada, pagada, parcial_pagada
- stock_actualizado: bool
```

#### PagoCompra (NUEVO)
```python
- compra_id: FK
- monto: Numeric
- fecha_pago: datetime
- origen_pago: str  # caja_chica, otra_fuente
- apertura_caja_id: FK (nullable)
- movimiento_caja_id: FK (nullable)
- referencia: str (nullable)
- usuario_paga_id: FK
```

#### MovimientoCaja (NUEVO)
```python
- apertura_caja_id: FK
- tipo: str  # ingreso, egreso
- concepto: str
- monto: Numeric
- referencia_tipo: str  # compra, venta, etc
- referencia_id: int
- usuario_id: FK
```

#### CompraDetalle (Actualizado)
```python
- compra_id: FK
- producto_id: FK (nullable - para servicios/facturas)
- cantidad: Numeric (nullable)
- precio_unitario: Numeric
- subtotal: Numeric
- concepto: str (para servicios/facturas sin producto)
- stock_actualizado: bool
```

#### CuentaPorPagar (Actualizado)
```python
- compra_id: FK
- proveedor_id: FK
- monto_adeudado: Numeric
- monto_pagado: Numeric
- fecha_creacion: datetime
- fecha_vencimiento: date
- estado: str  # pendiente, pagada, parcial
```

---

### 2. RUTAS (app/routes/compras.py)

#### `/compras/registrar-compra` (GET/POST)
**Función:** Registra compra sin pagar (estado='registrada')

**Proceso:**
1. Genera número de compra: `C-000001`
2. Crea registro Compra
3. Procesa detalles (productos o servicios/facturas)
4. Si tipo='producto':
   - Actualiza `producto.stock_actual`
   - Crea `MovimientoProducto`
   - Actualiza `producto.precio_compra` si cambió
   - Marca `compra.stock_actualizado=True`
5. Calcula subtotal, IVA (10%), total
6. Redirige a `/pendientes-pago`

#### `/compras/pendientes-pago` (GET)
**Función:** Lista compras con estado='registrada' o 'parcial_pagada'

**Muestra:** Tabla con número, proveedor, tipo, total, estado, acciones (Ver, Pagar)

#### `/compras/<id>/pagar` (POST)
**Función:** Registra pago con origen flexible

**Parámetros:**
- `monto`: decimal
- `origen_pago`: 'caja_chica' | 'otra_fuente' | 'dejar_credito'
- `referencia`: string (opcional)

**Lógica por origen:**

**A) caja_chica:**
```python
1. Busca apertura abierta
2. Crea MovimientoCaja (tipo='egreso')
3. Crea PagoCompra con apertura_caja_id
4. Descuenta de apertura.monto_final
5. Actualiza compra.estado:
   - Si monto >= total: 'pagada'
   - Si monto < total: 'parcial_pagada' + crea CxP por diferencia
```

**B) otra_fuente:**
```python
1. Crea PagoCompra sin apertura_caja_id
2. Actualiza compra.estado igual que (A)
3. NO afecta apertura de caja
```

**C) dejar_credito:**
```python
1. Crea CuentaPorPagar
2. monto_adeudado = compra.total
3. estado = 'pendiente'
4. NO crea PagoCompra
5. compra.estado queda 'registrada'
```

#### `/compras/cuentas-por-pagar-compras` (GET)
**Función:** Lista CuentaPorPagar pendientes

**Muestra:** Fecha, compra, proveedor, total, adeudado, vencimiento, estado, acciones

#### `/compras/api/compra/<id>` (GET)
**Función:** API endpoint para obtener datos de compra (usado por modales)

**Retorna JSON:**
```json
{
  "id": 1,
  "numero_compra": "C-000001",
  "proveedor": "Proveedor XYZ",
  "tipo": "producto",
  "total": 1100000.00,
  "subtotal": 1000000.00,
  "iva": 100000.00,
  "estado": "registrada"
}
```

---

### 3. TEMPLATES

#### `compras/registrar_compra.html`
**Características:**
- Formulario con selección de proveedor y tipo de compra
- Tabla dinámica de detalles (cambia según tipo)
- Si tipo='producto': busca y selecciona productos, actualiza precios
- Si tipo='servicio/factura/gasto': ingresa concepto y monto
- Cálculo automático de subtotal, IVA (10%), total
- JavaScript para agregar/eliminar líneas

**JavaScript clave:**
```javascript
- cambiarTipoCompra(): Alterna encabezado producto vs otro
- agregarDetalle(): Agrega fila según tipo
- abrirSeleccionarProducto(id): Modal de búsqueda de productos
- calcularSubtotal(id): Calcula cantidad * precio
- actualizarTotales(): Suma todos los detalles + IVA
```

#### `compras/pendientes_pago.html`
**Características:**
- Tabla con compras estado='registrada' o 'parcial_pagada'
- Botón "Pagar" abre modal con 3 opciones:
  1. **Caja Chica** (descuenta de apertura)
  2. **Otra Fuente** (no afecta caja)
  3. **Dejar a Crédito** (crea CxP)
- Resumen de totales pendientes

**Modal de Pago:**
```html
- Input: monto a pagar (pre-cargado con total)
- Radio buttons: 3 orígenes de pago
- Input: referencia (opcional)
- Submit: POST a /compras/<id>/pagar
```

#### `compras/ver.html`
**Características:**
- Información general de la compra
- Totales (subtotal, IVA, total)
- Badge de estado (registrada, parcial_pagada, pagada)
- Tabla de detalles (productos o conceptos según tipo)
- Historial de pagos (si existe)
- Botón "Pagar" si estado='registrada'

#### `compras/cuentas_por_pagar_compras.html`
**Características:**
- Lista de CxP con estado='pendiente' o 'parcial'
- Resumen: Total pendiente, Vencidas, Proveedores
- Tabla con indicadores de vencimiento (rojo si vencida)
- Botón "Pagar" abre modal para registrar pago directo a CxP

---

### 4. RELACIONES ACTUALIZADAS

#### AperturaCaja (app/models/venta.py)
**Añadido:**
```python
movimientos = db.relationship('MovimientoCaja', backref='apertura_caja', 
                             lazy='dynamic', cascade='all, delete-orphan')
```

#### Productos API (app/routes/productos.py)
**Añadido endpoint:**
```python
@bp.route('/api/productos')
def api_productos():
    """Retorna lista JSON de productos activos"""
    # Usado por registrar_compra.html para cargar lista de productos
```

---

## FLUJO COMPLETO DE USO

### CASO 1: Compra de Productos - Pago Inmediato con Caja Chica

1. Usuario va a `/compras/registrar-compra`
2. Selecciona proveedor y tipo='producto'
3. Agrega líneas de productos (busca por código/nombre)
4. Sistema calcula subtotal + IVA automáticamente
5. Guarda compra → **Stock actualizado inmediatamente**
6. Redirige a `/pendientes-pago`
7. Usuario hace clic en "Pagar"
8. Selecciona "Caja Chica"
9. Sistema:
   - Crea MovimientoCaja (egreso)
   - Descuenta de apertura.monto_final
   - Marca compra.estado='pagada'

### CASO 2: Compra de Servicio - Pagar Después con Otra Fuente

1. Usuario va a `/compras/registrar-compra`
2. Selecciona proveedor y tipo='servicio'
3. Ingresa concepto: "Reparación de equipo" y monto
4. Guarda compra → estado='registrada'
5. Más tarde, en `/pendientes-pago`, hace clic en "Pagar"
6. Selecciona "Otra Fuente"
7. Ingresa referencia: "Transferencia 1234"
8. Sistema:
   - Crea PagoCompra (sin apertura_caja_id)
   - Marca compra.estado='pagada'
   - **NO afecta caja**

### CASO 3: Compra de Productos - Dejar a Crédito

1. Usuario registra compra normal (tipo='producto')
2. Stock se actualiza inmediatamente
3. En pendientes_pago, hace clic en "Pagar"
4. Selecciona "Dejar a Crédito"
5. Sistema:
   - Crea CuentaPorPagar con monto_adeudado=total
   - compra.estado queda 'registrada'
   - **NO crea PagoCompra**
6. Más tarde, en `/cuentas-por-pagar-compras`, puede pagar CxP

---

## DIFERENCIAS CLAVE CON FLUJO ANTERIOR

### ANTES (Complejo):
```
Pedido → Presupuesto → Orden → Compra → Pago
- Muchos pasos intermedios
- Pago obligatorio al registrar
- tipo_pago='contado'|'credito' mezclado con origen
```

### AHORA (Simplificado):
```
Registrar Compra → Pagar (Flexible)
- 1 paso para registrar (sin pagar)
- Stock actualizado inmediatamente si tipo='producto'
- Pago posterior con origen independiente
- origen_pago (caja_chica/otra_fuente) separado de decisión de crédito
```

---

## CONFIGURACIONES NECESARIAS

### Base de datos:
Ejecutar migraciones para crear/actualizar tablas:
```bash
flask db migrate -m "Add new compras simplified flow"
flask db upgrade
```

### Navegación (opcional):
Añadir en sidebar/menú:
```html
<a href="{{ url_for('compras.registrar_compra') }}">Registrar Compra</a>
<a href="{{ url_for('compras.pendientes_pago') }}">Pendientes de Pago</a>
<a href="{{ url_for('compras.cuentas_por_pagar_compras') }}">Cuentas por Pagar</a>
```

---

## VALIDACIONES Y CONTROLES

### Validaciones en Registrar Compra:
- ✓ Proveedor requerido
- ✓ Tipo de compra requerido
- ✓ Al menos 1 línea de detalle
- ✓ Si tipo='producto': producto_id requerido
- ✓ Cantidad y precio > 0

### Validaciones en Pagar:
- ✓ Monto > 0 (excepto si dejar_credito)
- ✓ Si origen='caja_chica': debe haber apertura abierta
- ✓ No puede pagar más del total pendiente

### Controles de Seguridad:
- ✓ Todos los endpoints requieren @login_required
- ✓ Transacciones con db.session.rollback() en excepciones
- ✓ Validación de FK antes de crear registros

---

## PRÓXIMOS PASOS RECOMENDADOS

1. **Ejecutar migraciones** para crear las nuevas tablas
2. **Probar flujo completo**:
   - Registrar compra de productos
   - Verificar stock actualizado
   - Probar pago con caja chica
   - Probar pago con otra fuente
   - Probar dejar a crédito
3. **Añadir al dashboard** tarjetas de resumen:
   - Compras registradas hoy
   - Compras pendientes de pago
   - Cuentas por pagar vencidas
4. **Opcional:** Añadir filtros en pendientes_pago por fecha, proveedor, tipo

---

## ARCHIVOS MODIFICADOS/CREADOS

### Modelos:
- ✅ `app/models/compra.py` - Actualizado (Compra, nuevos PagoCompra, MovimientoCaja)
- ✅ `app/models/venta.py` - Actualizado (AperturaCaja.movimientos)
- ✅ `app/models/__init__.py` - Actualizado (exports)

### Rutas:
- ✅ `app/routes/compras.py` - Actualizado (nuevos endpoints)
- ✅ `app/routes/productos.py` - Actualizado (api_productos endpoint)

### Templates:
- ✅ `app/templates/compras/registrar_compra.html` - CREADO
- ✅ `app/templates/compras/pendientes_pago.html` - CREADO
- ✅ `app/templates/compras/ver.html` - CREADO
- ✅ `app/templates/compras/cuentas_por_pagar_compras.html` - CREADO
- ✅ `app/templates/compras/listar.html` - Ya existía

---

## NOTAS IMPORTANTES

1. **Stock se actualiza SIEMPRE** al registrar si tipo='producto', sin importar estado de pago
2. **origen_pago es independiente** de la decisión de crédito
3. **Backward compatible**: Los modelos legacy (PedidoCompra, OrdenCompra) siguen funcionando
4. **MovimientoCaja** solo se crea si origen='caja_chica'
5. **CuentaPorPagar** se crea si:
   - origen='dejar_credito' (sin pago), o
   - pago parcial (monto < total)

---

**Implementación completada exitosamente! 🎉**
