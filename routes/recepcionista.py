from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.db import db
from models.habitaciones import Habitacion

recepcionista = Blueprint('recepcionista', __name__)

# Middleware para verificar permisos de recepcionista o superior
def verificar_recepcionista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 1:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de recepcionista o superior'}), 403
    return None

@recepcionista.route('/estado-habitaciones')
def estado_habitaciones():
    # Verificar permisos de recepcionista o superior
    error = verificar_recepcionista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))

    return render_template('recepcionista/estado-hab.html')

@recepcionista.route('/gestion-reservas')
def gestion_reservas():
    # Verificar permisos de recepcionista o superior
    error = verificar_recepcionista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))

    return render_template('recepcionista/gestion_reservas.html')

@recepcionista.route('/check')
def check_in_out():
    # Verificar permisos de recepcionista o superior
    error = verificar_recepcionista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))

    return render_template('recepcionista/check.html')

@recepcionista.route('/gestion-usuario')
def gestion_usuarios():
    # Verificar permisos de recepcionista o superior
    error = verificar_recepcionista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))

    return render_template('recepcionista/gestion_usuario.html')

# API para obtener todas las habitaciones (solo lectura para recepcionista)
@recepcionista.route('/api/habitaciones-estado', methods=['GET'])
def obtener_habitaciones_estado():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        habitaciones = Habitacion.query.all()
        habitaciones_list = []
        
        for habitacion in habitaciones:
            habitacion_dict = {
                'idhabitacion': habitacion.idhabitacion,
                'numero': habitacion.numero,
                'estado': habitacion.estado,
                'nombre': habitacion.nombre,
                'capacidad': habitacion.capacidad
            }
            habitaciones_list.append(habitacion_dict)
        
        return jsonify(habitaciones_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener habitaciones: {str(e)}'}), 500

# API para cambiar el estado de una habitación
@recepcionista.route('/api/habitaciones/<int:id>/estado', methods=['PUT'])
def cambiar_estado_habitacion(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        habitacion = Habitacion.query.get_or_404(id)
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        # Validar estados permitidos
        estados_validos = ['disponible', 'ocupada', 'mantenimiento', 'limpieza']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido'}), 400
        
        habitacion.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({'message': f'Estado de habitación {habitacion.numero} actualizado a {nuevo_estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500