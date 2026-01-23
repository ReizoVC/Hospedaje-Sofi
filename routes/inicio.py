from flask import Blueprint, render_template, redirect, url_for, session
from utils.auth import redirect_staff_to_dashboard
from utils.db import db
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
from datetime import date
from sqlalchemy import func

inicio = Blueprint('inicio', __name__)


@inicio.before_request
def _bloquear_trabajadores_en_publico():
    return redirect_staff_to_dashboard()

@inicio.app_template_global()
def fecha_minima():
    """Retorna la fecha mínima para las reservas (hoy)"""
    return date.today().isoformat()

@inicio.route('/')
def index():
    try:

        habitaciones_populares = db.session.query(Habitacion).order_by(func.random()).limit(3).all()
        
        habitaciones_lujosas = db.session.query(Habitacion).order_by(Habitacion.precio_noche.desc()).limit(3).all()

        def preparar_habitaciones(habitaciones):
            habitaciones_data = []
            for habitacion in habitaciones:
                imagen_principal = ImagenHabitacion.query.filter_by(
                    idhabitacion=habitacion.idhabitacion, 
                    orden=1
                ).first()

                if not imagen_principal:
                    imagen_principal = ImagenHabitacion.query.filter_by(
                        idhabitacion=habitacion.idhabitacion
                    ).order_by(ImagenHabitacion.orden).first()
                
                habitacion_dict = habitacion.to_dict()
                habitacion_dict['imagen_url'] = f"/static/uploads/{imagen_principal.url}" if imagen_principal else "/static/images/index/hab1.avif"
                habitaciones_data.append(habitacion_dict)
            return habitaciones_data
        
        populares_data = preparar_habitaciones(habitaciones_populares)
        lujosas_data = preparar_habitaciones(habitaciones_lujosas)
        
        return render_template('pages/index.html', 
                            habitaciones_populares=populares_data,
                            habitaciones_lujosas=lujosas_data)
    except Exception as e:
        return render_template('pages/index.html', 
                            habitaciones_populares=[],
                            habitaciones_lujosas=[])

@inicio.route('/habitaciones')
def habitaciones():
    try:
        habitaciones = Habitacion.query.all()
        
        habitaciones_data = []
        for habitacion in habitaciones:
            imagen_principal = ImagenHabitacion.query.filter_by(
                idhabitacion=habitacion.idhabitacion, 
                orden=1
            ).first()
            
            if not imagen_principal:
                imagen_principal = ImagenHabitacion.query.filter_by(
                    idhabitacion=habitacion.idhabitacion
                ).order_by(ImagenHabitacion.orden).first()
            
            habitacion_dict = habitacion.to_dict()
            habitacion_dict['imagen_url'] = f"/static/uploads/{imagen_principal.url}" if imagen_principal else "/static/images/index/hab1.avif"
            habitaciones_data.append(habitacion_dict)
        
        return render_template('pages/habitaciones.html', habitaciones=habitaciones_data)
    except Exception as e:
        return render_template('pages/habitaciones.html', habitaciones=[])

@inicio.route('/nosotros')
def nosotros():
    return render_template('pages/nosotros.html')

@inicio.route('/habitacion/<int:id>')
def detalle_habitacion(id):
    try:
        habitacion = Habitacion.query.get_or_404(id)
        

        imagenes = ImagenHabitacion.query.filter_by(
            idhabitacion=id
        ).order_by(ImagenHabitacion.orden).all()
        
        habitacion_data = habitacion.to_dict()
        habitacion_data['imagenes'] = [
            f"/static/uploads/{img.url}" for img in imagenes
        ] if imagenes else ["/static/images/index/hab1.avif"]
        
        return render_template('pages/detalle_habitacion.html', habitacion=habitacion_data)
    except Exception as e:
        return render_template('errors/error.html', mensaje="Habitación no encontrada"), 404

@inicio.route('/_legacy/login')
def login():
    return redirect(url_for('auth.login_page'))

@inicio.route('/_legacy/register')
def register():
    return redirect(url_for('auth.register_page'))