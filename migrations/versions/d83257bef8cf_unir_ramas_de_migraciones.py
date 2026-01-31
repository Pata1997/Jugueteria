"""Unir ramas de migraciones

Revision ID: d83257bef8cf
Revises: 0761a22cbad5, remove_audit_logs
Create Date: 2026-01-26 09:42:05.840159

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd83257bef8cf'
down_revision = ('0761a22cbad5', 'remove_audit_logs')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
