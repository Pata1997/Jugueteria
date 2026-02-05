"""
Alembic migration para crear la tabla notas_credito_detalle
Revision ID: 20260201nc
"""
from alembic import op
import sqlalchemy as sa

revision = '20260201nc'
down_revision = '98fccbef7687'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notas_credito_detalle (
            id SERIAL NOT NULL,
            nota_credito_id INTEGER NOT NULL,
            venta_detalle_id INTEGER NOT NULL,
            cantidad NUMERIC(12, 2) NOT NULL,
            precio_unitario NUMERIC(12, 2) NOT NULL,
            subtotal NUMERIC(12, 2) NOT NULL,
            fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(nota_credito_id) REFERENCES notas_credito (id) ON DELETE CASCADE,
            FOREIGN KEY(venta_detalle_id) REFERENCES venta_detalles (id) ON DELETE CASCADE
        )
        """
    )

def downgrade():
    op.drop_table('notas_credito_detalle')
