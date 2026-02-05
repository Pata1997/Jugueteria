"""Agregar apertura_caja_id a pagos_nota_debito

Revision ID: 20260205pd
Revises: 20260205mh
Create Date: 2026-02-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260205pd'
down_revision = '20260205mh'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pagos_nota_debito', sa.Column('apertura_caja_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_pagos_nd_apertura',
        'pagos_nota_debito',
        'aperturas_caja',
        ['apertura_caja_id'],
        ['id']
    )


def downgrade():
    op.drop_constraint('fk_pagos_nd_apertura', 'pagos_nota_debito', type_='foreignkey')
    op.drop_column('pagos_nota_debito', 'apertura_caja_id')
