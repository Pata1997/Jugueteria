"""
Alembic migration para crear las tablas notas_credito_compra y nota_credito_compra_detalles
Revision ID: 20260605_crear_notas_credito_compra
"""
from alembic import op
import sqlalchemy as sa

revision = '20260605_crear_notas_credito_compra'
down_revision = '20260201nc'
branch_labels = None
depends_on = None

def upgrade():
    # Crear tabla notas_credito_compra
    op.create_table(
        'notas_credito_compra',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero_nota', sa.String(50), nullable=False, unique=True),
        sa.Column('fecha_emision', sa.DateTime(), nullable=True),
        sa.Column('compra_id', sa.Integer(), nullable=False),
        sa.Column('proveedor_id', sa.Integer(), nullable=False),
        sa.Column('motivo', sa.String(200), nullable=False),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(20), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['compra_id'], ['compras.id'], ),
        sa.ForeignKeyConstraint(['proveedor_id'], ['proveedores.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.UniqueConstraint('numero_nota')
    )
    op.create_index(op.f('ix_notas_credito_compra_numero_nota'), 'notas_credito_compra', ['numero_nota'], unique=True)

    # Crear tabla nota_credito_compra_detalles
    op.create_table(
        'nota_credito_compra_detalles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nota_credito_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.String(255), nullable=False),
        sa.Column('cantidad', sa.Numeric(10, 2), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['nota_credito_id'], ['notas_credito_compra.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], )
    )

def downgrade():
    op.drop_table('nota_credito_compra_detalles')
    op.drop_table('notas_credito_compra')
