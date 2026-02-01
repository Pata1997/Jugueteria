"""
Alembic migration para crear la tabla notas_credito_detalle
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'notas_credito_detalle',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nota_credito_id', sa.Integer, sa.ForeignKey('notas_credito.id', ondelete='CASCADE'), nullable=False),
        sa.Column('venta_detalle_id', sa.Integer, sa.ForeignKey('venta_detalles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cantidad', sa.Numeric(12, 2), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime, server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('notas_credito_detalle')
