"""Migración limpia: Mejorar Notas de Débito y Crédito (no-op)

Revision ID: 20260205nc
Revises: 20260205nd
Create Date: 2026-02-05 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20260205nc'
down_revision = '20260205nd'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
