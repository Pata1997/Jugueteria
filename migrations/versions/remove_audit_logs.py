"""
Migration: Elimina la tabla audit_logs
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.drop_table('audit_logs')

def downgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('usuario_id', sa.Integer),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('modulo', sa.String(50), nullable=False),
        sa.Column('descripcion', sa.Text),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('fecha', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
