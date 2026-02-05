"""Alembic migration para mejorar tabla notas_debito

Revision ID: 20260205nd
Revises: 20260201nc
Create Date: 2026-02-05 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260205nd'
down_revision = '20260201nc'
branch_labels = None
depends_on = None

def upgrade():
    # Agregar campos a notas_debito
    with op.batch_alter_table('notas_debito', schema=None) as batch_op:
        # Agregar tipo de ND
        batch_op.add_column(sa.Column('tipo', sa.String(20), nullable=False, server_default='cargo'))
        
        # Renombrar estado a estado_emision (para distinguir de pago)
        batch_op.add_column(sa.Column('estado_emision', sa.String(20), nullable=False, server_default='activa'))
        
        # Agregar estado de pago
        batch_op.add_column(sa.Column('estado_pago', sa.String(20), nullable=False, server_default='pendiente'))
        
        # Agregar timestamp de modificación
        batch_op.add_column(sa.Column('fecha_modificacion', sa.DateTime, nullable=False, server_default=sa.func.now()))
    
    # Agregar venta_detalle_id a notas_debito_detalle
    with op.batch_alter_table('notas_debito_detalle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('venta_detalle_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key('fk_ndd_venta_detalle', 'venta_detalles', ['venta_detalle_id'], ['id'])

def downgrade():
    # Revertir cambios
    with op.batch_alter_table('notas_debito_detalle', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ndd_venta_detalle', type_='foreignkey')
        batch_op.drop_column('venta_detalle_id')
    
    with op.batch_alter_table('notas_debito', schema=None) as batch_op:
        batch_op.drop_column('fecha_modificacion')
        batch_op.drop_column('estado_pago')
        batch_op.drop_column('estado_emision')
        batch_op.drop_column('tipo')
