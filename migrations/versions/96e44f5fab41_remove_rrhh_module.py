"""remove_rrhh_module

Revision ID: 96e44f5fab41
Revises: 54b65781f03c
Create Date: 2026-01-10 10:34:51.201761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96e44f5fab41'
down_revision = '54b65781f03c'
branch_labels = None
depends_on = None


def upgrade():
    # IMPORTANTE: Primero eliminar la foreign key que apunta a empleados
    op.drop_constraint('ordenes_servicio_tecnico_id_fkey', 'ordenes_servicio', type_='foreignkey')
    
    # Crear nueva foreign key apuntando a usuarios
    op.create_foreign_key('ordenes_servicio_tecnico_id_fkey', 'ordenes_servicio', 'usuarios', ['tecnico_id'], ['id'])
    
    # Ahora sí eliminar las tablas del módulo RRHH en orden correcto (respetando foreign keys)
    op.drop_table('asistencias')
    op.drop_table('permisos')
    op.drop_table('vacaciones')
    op.drop_table('horarios_atencion')
    op.drop_table('empleados')


def downgrade():
    # Recrear tablas en orden inverso (para rollback)
    op.create_table('empleados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('ci', sa.String(length=50), nullable=False),
        sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
        sa.Column('direccion', sa.String(length=255), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('cargo', sa.String(length=100), nullable=True),
        sa.Column('departamento', sa.String(length=100), nullable=True),
        sa.Column('fecha_ingreso', sa.Date(), nullable=False),
        sa.Column('fecha_egreso', sa.Date(), nullable=True),
        sa.Column('salario', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ci'),
        sa.UniqueConstraint('codigo'),
        sa.UniqueConstraint('usuario_id')
    )
    
    op.create_table('horarios_atencion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.String(length=20), nullable=False),
        sa.Column('hora_apertura', sa.Time(), nullable=True),
        sa.Column('hora_cierre', sa.Time(), nullable=True),
        sa.Column('cerrado', sa.Boolean(), nullable=True),
        sa.Column('observaciones', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('vacaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empleado_id', sa.Integer(), nullable=False),
        sa.Column('fecha_solicitud', sa.DateTime(), nullable=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('dias_solicitados', sa.Integer(), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('fecha_aprobacion', sa.DateTime(), nullable=True),
        sa.Column('aprobado_por_id', sa.Integer(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['aprobado_por_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleados.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('permisos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empleado_id', sa.Integer(), nullable=False),
        sa.Column('fecha_solicitud', sa.DateTime(), nullable=True),
        sa.Column('fecha_permiso', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=True),
        sa.Column('hora_fin', sa.Time(), nullable=True),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('fecha_aprobacion', sa.DateTime(), nullable=True),
        sa.Column('aprobado_por_id', sa.Integer(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['aprobado_por_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleados.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('asistencias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empleado_id', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('hora_entrada', sa.Time(), nullable=True),
        sa.Column('hora_salida', sa.Time(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleados.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
