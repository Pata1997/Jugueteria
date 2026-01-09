from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Empleado, Vacacion, Permiso, Asistencia, HorarioAtencion, Usuario
from datetime import datetime

bp = Blueprint('rrhh', __name__, url_prefix='/rrhh')

# ===== EMPLEADOS =====
@bp.route('/empleados')
@login_required
def empleados():
    empleados = Empleado.query.filter_by(activo=True).all()
    return render_template('rrhh/empleados.html', empleados=empleados)

@bp.route('/empleados/crear', methods=['GET', 'POST'])
@login_required
def crear_empleado():
    if request.method == 'POST':
        try:
            ultimo = Empleado.query.order_by(Empleado.id.desc()).first()
            codigo = f"EMP-{(ultimo.id + 1 if ultimo else 1):04d}"
            
            empleado = Empleado(
                codigo=codigo,
                nombre=request.form.get('nombre'),
                apellido=request.form.get('apellido'),
                ci=request.form.get('ci'),
                fecha_nacimiento=request.form.get('fecha_nacimiento'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                email=request.form.get('email'),
                cargo=request.form.get('cargo'),
                departamento=request.form.get('departamento'),
                fecha_ingreso=request.form.get('fecha_ingreso'),
                salario=request.form.get('salario'),
                observaciones=request.form.get('observaciones')
            )
            
            db.session.add(empleado)
            db.session.commit()
            
            flash('Empleado creado correctamente', 'success')
            return redirect(url_for('rrhh.ver_empleado', id=empleado.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('rrhh/crear_empleado.html')

@bp.route('/empleados/<int:id>')
@login_required
def ver_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    return render_template('rrhh/ver_empleado.html', empleado=empleado)

# ===== VACACIONES =====
@bp.route('/vacaciones')
@login_required
def vacaciones():
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = Vacacion.query
    if estado:
        query = query.filter_by(estado=estado)
    
    vacaciones = query.order_by(Vacacion.fecha_solicitud.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('rrhh/vacaciones.html', vacaciones=vacaciones)

@bp.route('/vacaciones/crear', methods=['GET', 'POST'])
@login_required
def crear_vacacion():
    if request.method == 'POST':
        try:
            from datetime import datetime
            fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
            dias = (fecha_fin - fecha_inicio).days + 1
            
            vacacion = Vacacion(
                empleado_id=request.form.get('empleado_id'),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                dias_solicitados=dias,
                motivo=request.form.get('motivo')
            )
            
            db.session.add(vacacion)
            db.session.commit()
            
            flash('Solicitud de vacación creada', 'success')
            return redirect(url_for('rrhh.vacaciones'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    empleados = Empleado.query.filter_by(activo=True).all()
    return render_template('rrhh/crear_vacacion.html', empleados=empleados)

# ===== PERMISOS =====
@bp.route('/permisos')
@login_required
def permisos():
    page = request.args.get('page', 1, type=int)
    permisos = Permiso.query.order_by(Permiso.fecha_solicitud.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('rrhh/permisos.html', permisos=permisos)

# ===== ASISTENCIAS =====
@bp.route('/asistencias')
@login_required
def asistencias():
    fecha = request.args.get('fecha', datetime.now().date())
    empleados = Empleado.query.filter_by(activo=True).all()
    
    asistencias = {}
    for emp in empleados:
        asist = Asistencia.query.filter_by(
            empleado_id=emp.id,
            fecha=fecha
        ).first()
        asistencias[emp.id] = asist
    
    return render_template('rrhh/asistencias.html', 
                         empleados=empleados, 
                         asistencias=asistencias,
                         fecha=fecha)

@bp.route('/asistencias/registrar', methods=['POST'])
@login_required
def registrar_asistencia():
    try:
        empleado_id = request.form.get('empleado_id')
        fecha = request.form.get('fecha')
        estado = request.form.get('estado')
        
        asistencia = Asistencia.query.filter_by(
            empleado_id=empleado_id,
            fecha=fecha
        ).first()
        
        if asistencia:
            asistencia.estado = estado
            asistencia.hora_entrada = request.form.get('hora_entrada')
            asistencia.hora_salida = request.form.get('hora_salida')
        else:
            asistencia = Asistencia(
                empleado_id=empleado_id,
                fecha=fecha,
                estado=estado,
                hora_entrada=request.form.get('hora_entrada'),
                hora_salida=request.form.get('hora_salida')
            )
            db.session.add(asistencia)
        
        db.session.commit()
        flash('Asistencia registrada', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('rrhh.asistencias'))
