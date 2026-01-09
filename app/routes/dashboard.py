from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Cliente, Producto, Venta, OrdenServicio
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    # Estadísticas generales
    total_clientes = Cliente.query.filter_by(activo=True).count()
    total_productos = Producto.query.filter_by(activo=True).count()
    
    # Ventas del mes
    inicio_mes = datetime.now().replace(day=1)
    ventas_mes = Venta.query.filter(
        Venta.fecha_venta >= inicio_mes,
        Venta.estado == 'completada'
    ).all()
    total_ventas_mes = sum(v.total for v in ventas_mes)
    
    # Servicios pendientes
    servicios_pendientes = OrdenServicio.query.filter(
        OrdenServicio.estado.in_(['pendiente', 'en_proceso'])
    ).count()
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).all()
    
    # Ventas por día (últimos 7 días)
    hace_7_dias = datetime.now() - timedelta(days=7)
    ventas_por_dia = db.session.query(
        func.date(Venta.fecha_venta).label('fecha'),
        func.sum(Venta.total).label('total')
    ).filter(
        Venta.fecha_venta >= hace_7_dias,
        Venta.estado == 'completada'
    ).group_by(func.date(Venta.fecha_venta)).all()
    
    return render_template('dashboard/index.html',
                         total_clientes=total_clientes,
                         total_productos=total_productos,
                         total_ventas_mes=total_ventas_mes,
                         servicios_pendientes=servicios_pendientes,
                         productos_stock_bajo=productos_stock_bajo,
                         ventas_por_dia=ventas_por_dia)
