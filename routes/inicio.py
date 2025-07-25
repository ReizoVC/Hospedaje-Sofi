from flask import Blueprint, render_template, jsonify
from utils.db import db
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion

inicio = Blueprint('inicio', __name__)

@inicio.route('/')
def index():
    return render_template('pages/index.html')

@inicio.route('/habitaciones')
def habitaciones():
    try:
        # Obtener todas las habitaciones disponibles
        habitaciones = Habitacion.query.filter_by(estado='disponible').all()
        
        # Preparar datos con imágenes
        habitaciones_data = []
        for habitacion in habitaciones:
            # Buscar imagen con orden 1 (imagen principal)
            imagen_principal = ImagenHabitacion.query.filter_by(
                idhabitacion=habitacion.idhabitacion, 
                orden=1
            ).first()
            
            # Si no hay imagen con orden 1, tomar la primera disponible
            if not imagen_principal:
                imagen_principal = ImagenHabitacion.query.filter_by(
                    idhabitacion=habitacion.idhabitacion
                ).order_by(ImagenHabitacion.orden).first()
            
            habitacion_dict = habitacion.to_dict()
            habitacion_dict['imagen_url'] = f"/static/uploads/{imagen_principal.url}" if imagen_principal else "/static/images/index/hab1.avif"
            habitaciones_data.append(habitacion_dict)
        
        return render_template('pages/habitaciones.html', habitaciones=habitaciones_data)
    except Exception as e:
        print(f"Error al cargar habitaciones: {str(e)}")
        # En caso de error, mostrar página vacía
        return render_template('pages/habitaciones.html', habitaciones=[])

@inicio.route('/nosotros')
def nosotros():
    return render_template('pages/nosotros.html')

@inicio.route('/habitacion/<int:id>')
def detalle_habitacion(id):
    try:
        habitacion = Habitacion.query.get_or_404(id)
        
        # Obtener todas las imágenes de la habitación ordenadas
        imagenes = ImagenHabitacion.query.filter_by(
            idhabitacion=id
        ).order_by(ImagenHabitacion.orden).all()
        
        # Preparar datos
        habitacion_data = habitacion.to_dict()
        habitacion_data['imagenes'] = [
            f"/static/uploads/{img.url}" for img in imagenes
        ] if imagenes else ["/static/images/index/hab1.avif"]
        
        return render_template('pages/detalle_habitacion.html', habitacion=habitacion_data)
    except Exception as e:
        print(f"Error al cargar habitación {id}: {str(e)}")
        return render_template('pages/error.html', mensaje="Habitación no encontrada"), 404

@inicio.route('/login')
def login():
    return render_template('auth/login.html')

@inicio.route('/register')
def register():
    return render_template('auth/register.html')