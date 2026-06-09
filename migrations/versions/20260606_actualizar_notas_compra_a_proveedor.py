"""Actualizar notas de compra para registrar emitidas por proveedor en lugar de emitidas por nosotros

Revision ID: 20260606_actualizar_notas_compra_a_proveedor
Revises: 20260205pd
Create Date: 2026-06-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260606_actualizar_notas_compra_a_proveedor'
down_revision = '20260205pd'
branch_labels = None
depends_on = None


def upgrade():
    # Actualizar tabla notas_credito_compra
    with op.batch_alter_table('notas_credito_compra', schema=None) as batch_op:
        # Renombrar numero_nota a numero_nota_proveedor
        batch_op.alter_column('numero_nota', new_column_name='numero_nota_proveedor')
        # Renombrar fecha_emision a fecha_nota_proveedor
        batch_op.alter_column('fecha_emision', new_column_name='fecha_nota_proveedor')
        # Agregar fecha_registro
        batch_op.add_column(sa.Column('fecha_registro', sa.DateTime(), nullable=True))
        # Remover unique constraint de numero_nota_proveedor
        batch_op.drop_index('ix_notas_credito_compra_numero_nota')
        batch_op.create_index(op.f('ix_notas_credito_compra_numero_nota_proveedor'), 
                             ['numero_nota_proveedor'], unique=False)
    
    # Actualizar tabla notas_debito_compra
    with op.batch_alter_table('notas_debito_compra', schema=None) as batch_op:
        # Renombrar numero_nota a numero_nota_proveedor
        batch_op.alter_column('numero_nota', new_column_name='numero_nota_proveedor')
        # Renombrar fecha_emision a fecha_nota_proveedor
        batch_op.alter_column('fecha_emision', new_column_name='fecha_nota_proveedor')
        # Agregar fecha_registro
        batch_op.add_column(sa.Column('fecha_registro', sa.DateTime(), nullable=True))
        # Remover unique constraint de numero_nota_proveedor
        batch_op.drop_index('ix_notas_debito_compra_numero_nota')
        batch_op.create_index(op.f('ix_notas_debito_compra_numero_nota_proveedor'), 
                             ['numero_nota_proveedor'], unique=False)


def downgrade():
    # Revertir tabla notas_debito_compra
    with op.batch_alter_table('notas_debito_compra', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_notas_debito_compra_numero_nota_proveedor'))
        batch_op.drop_column('fecha_registro')
        batch_op.alter_column('fecha_nota_proveedor', new_column_name='fecha_emision')
        batch_op.alter_column('numero_nota_proveedor', new_column_name='numero_nota')
        batch_op.create_index('ix_notas_debito_compra_numero_nota', ['numero_nota'], unique=True)
    
    # Revertir tabla notas_credito_compra
    with op.batch_alter_table('notas_credito_compra', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_notas_credito_compra_numero_nota_proveedor'))
        batch_op.drop_column('fecha_registro')
        batch_op.alter_column('fecha_nota_proveedor', new_column_name='fecha_emision')
        batch_op.alter_column('numero_nota_proveedor', new_column_name='numero_nota')
        batch_op.create_index('ix_notas_credito_compra_numero_nota', ['numero_nota'], unique=True)
