"""add credit fields to compra

Revision ID: a1b2c3d4e5f6
Revises: c20c9cd1446c
Create Date: 2026-01-10
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c20c9cd1446c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('compras', sa.Column('plazo_credito_dias', sa.Integer(), nullable=True))
    op.add_column('compras', sa.Column('fecha_vencimiento_credito', sa.Date(), nullable=True))
    op.add_column('compras', sa.Column('observaciones_credito', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('compras', 'observaciones_credito')
    op.drop_column('compras', 'fecha_vencimiento_credito')
    op.drop_column('compras', 'plazo_credito_dias')
