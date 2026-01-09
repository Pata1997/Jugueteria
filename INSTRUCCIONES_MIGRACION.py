"""
Script de migración para agregar campos a FormaPago
Ejecutar con: flask db migrate -m "Agregar descripcion y requiere_referencia a FormaPago"
Luego: flask db upgrade
"""

# IMPORTANTE: Este es solo un ejemplo de cómo debería verse la migración
# Debes ejecutar los comandos de Flask-Migrate para generar la migración real

# Pasos para aplicar la migración:
# 1. Asegúrate de que Flask-Migrate esté instalado: pip install Flask-Migrate
# 2. Si no tienes la carpeta migrations/, ejecuta: flask db init
# 3. Genera la migración: flask db migrate -m "Agregar descripcion y requiere_referencia a FormaPago"
# 4. Aplica la migración: flask db upgrade
# 5. Ejecuta el script de inicialización: python inicializar_formas_pago.py

# Alternativamente, si prefieres ejecutar SQL directo:
"""
-- Agregar columnas a formas_pago
ALTER TABLE formas_pago ADD COLUMN descripcion TEXT;
ALTER TABLE formas_pago ADD COLUMN requiere_referencia BOOLEAN DEFAULT FALSE;
"""
