# Cambios implementados para SET Compliance - PDFs de Notas de Crédito y Débito

Fecha: 5 de febrero de 2026

## 📋 Resumen de mejoras

Se han reemplazado completamente los generadores de PDF para Notas de Crédito (NC) y Notas de Débito (ND) para cumplir con los requisitos de la SET (Superintendencia de Impuestos y Aduanas) de Paraguay.

### Archivos modificados:

1. **app/utils/nota_debito_ticket.py** - Generador de PDF para ND
2. **app/utils/nota_credito_ticket.py** - Generador de PDF para NC
3. **app/routes/ventas.py** - Ruta actualizada para descargar PDF de ND
4. **app/routes/notas_credito_pdf.py** - Ruta actualizada para descargar PDF de NC

---

## ✅ Elementos incluidos en NOTA DE DÉBITO

### Sección 1: Encabezado
- ✅ Logo de la empresa (si existe)
- ✅ Nombre de empresa en negrita (12pt)
- ✅ RUC y teléfono centrados

### Sección 2: Identificación del Documento
- ✅ **NOTA DE DÉBITO** (título destacado, 14pt)
- ✅ Timbrado: XXXXXXXX
- ✅ **Vence: DD/MM/YYYY** (OBLIGATORIO SET)
- ✅ Establecimiento y Punto de Expedición (implícito en número)
- ✅ N°: 001-001-0000007
- ✅ Fecha: DD/MM/YYYY HH:MM

### Sección 3: Factura Original Referenciada (NUEVA)
- ✅ **MODIFICA FACTURA:**
- ✅ N°: 001-001-0000456
- ✅ **Fecha: DD/MM/YYYY** (NUEVA - requerida para SET)

### Sección 4: Datos del Cliente
- ✅ CLIENTE: Nombre completo
- ✅ RUC/CI: Documento

### Sección 5: Motivo (MEJORADO)
- ✅ MOTIVO: (con word-wrap si es largo)
- ✅ Ejemplo: "Intereses por mora", "Gastos administrativos", etc.

### Sección 6: Detalle de Cargos
- ✅ Tabla con: Descripción, Cantidad, Monto
- ✅ Items que se están cobrando como débito

### Sección 7: Cálculo del Nuevo Total (NUEVO DISEÑO)
```
Factura Original:       100.000 Gs.
Débito Adicional:     +  10.000 Gs.
─────────────────────────────────
NUEVO TOTAL A PAGAR:   110.000 Gs.
```
- ✅ Muestra claramente la operación matemática
- ✅ Destaca el nuevo total en negrita (11pt)

### Sección 8: Información de Pago (NUEVA)
- ✅ PAGO:
- ✅ Estado: pendiente / pagado
- ✅ Mostrará "Crédito devuelto" si aplica

### Pie de página
- ✅ "Documento tributario válido"
- ✅ "Original: Cliente"

---

## ✅ Elementos incluidos en NOTA DE CRÉDITO

### Sección 1-3: Encabezado e Identificación
- ✅ Logo, Empresa, RUC (mismo que ND)
- ✅ **NOTA DE CRÉDITO** (título destacado, 14pt)
- ✅ Timbrado y Vence
- ✅ N° y Fecha

### Sección 4-6: Factura, Cliente, Motivo
- ✅ Igual que ND
- ✅ **Motivo:**  "Devolución de productos", etc.

### Sección 7: Productos Devueltos (DESTACADO)
```
PRODUCTOS DEVUELTOS:
DESCRIPCIÓN         CANT    MONTO
─────────────────────────────────
Montaje de Juguetes  1      50.000
Gravada 10%               4.545
```
- ✅ Tabla clara con productos devueltos
- ✅ Obtiene descripción desde VentaDetalle
- ✅ Muestra cantidad y monto individual

### Sección 8: Cálculo del Nuevo Saldo (NUEVO DISEÑO)
```
Factura Original:       50.000 Gs.
Crédito a Favor:     -  50.000 Gs.
─────────────────────────────────
NUEVO SALDO:                0 Gs.
```
- ✅ Muestra operación matemática clara
- ✅ Destaca nuevo saldo en negrita

### Pie de página
- ✅ "Documento tributario válido"
- ✅ "Original: Cliente"

---

## 🔄 Flujo de integración

1. Usuario descarga PDF desde ruta `/ventas/notas-debito/pdf/<id>` o `/ventas/notas-credito/pdf/<id>`
2. Ruta llama a `generar_nota_debito_ticket_pdf(nota)` o `generar_nota_credito_ticket_pdf(nota)`
3. Generadores crean PDF con ReportLab en formato 80mm x A4
4. PDF se devuelve al navegador para descargar

---

## 💾 Datos obtenidos de:

- **Factura original**: `nota.venta` (relación con Venta)
- **Motivo**: `nota.motivo` (campo del modelo)
- **Cliente**: `nota.venta.cliente` (relación)
- **Productos devueltos (NC)**: `nota.detalles` → `VentaDetalle.query.get(venta_detalle_id)`
- **Estado**: `nota.estado_pago`, `nota.estado_emision`
- **Empresa**: `ConfiguracionEmpresa.get_config()`

---

## 🧪 Testing

Para probar los PDFs:

1. Crear una venta
2. Crear una Nota de Débito o Crédito
3. Hacer clic en "Descargar PDF"
4. Verificar que se muestre:
   - ✅ Factura original referenciada con fecha
   - ✅ Timbrado vence correctamente
   - ✅ Cálculo claro: Original ± Cargo/Crédito = Nuevo Total/Saldo
   - ✅ Motivo completo
   - ✅ Para NC: Productos devueltos listados

---

## 🇵🇾 Cumplimiento SET Paraguay

Requisitos cumplidos:
- ✅ Factura original referenciada (N° y fecha)
- ✅ Timbrado y vencimiento del timbrado
- ✅ Establecimiento y punto de expedición
- ✅ Motivo del débito/crédito
- ✅ Cálculo claro del nuevo total/saldo
- ✅ Cliente identificado (RUC/CI)
- ✅ Productos/servicios detallados
- ✅ Estado del documento
- ✅ Firma visual: "Documento tributario válido"

---

## 📝 Notas técnicas

- **Formato**: 80mm x 297mm (papel térmico estándar)
- **Font**: Helvetica (estándar en PDFs)
- **Validación**: Todos los PDFs se validan antes de devolverse
- **Error handling**: Si algo falla, se loguea en stderr con prefijo [nota_credito_pdf] o [nota_debito_pdf]

---

## ✨ Cambios visuales desde versión anterior

### ANTES (usando GeneradorTicket genérico)
- Mostraba "FACTURA" como título
- Solo decía "Condición: NOTA DE DÉBITO/CRÉDITO"
- No mostraba factura original
- No mostraba cálculo del nuevo total
- Mostraba motivo incompleto
- No diferenciaba claramente el tipo de documento

### AHORA (PDF SET-compliant)
- Título destacado: "NOTA DE DÉBITO" o "NOTA DE CRÉDITO"
- Sección "MODIFICA FACTURA" con N° y fecha
- Cálculo claro: Original ± Cargo/Crédito = Nuevo Total/Saldo
- Motivo completo con word-wrap si es necesario
- Sección específica "PRODUCTOS DEVUELTOS" en NC
- Mejor organización visual con líneas separadoras
- Estado de pago claramente visible
- Más información tributaria para SET

---

*Documento generado automáticamente. Última actualización: 2026-02-05*
