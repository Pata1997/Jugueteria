"""Merge heads: notas y audit_logs

Revision ID: 20260205mh
Revises: 20260205nc, remove_audit_logs
Create Date: 2026-02-05 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20260205mh'
down_revision = ('20260205nc', 'remove_audit_logs')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
