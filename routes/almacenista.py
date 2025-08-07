from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.db import db
from models.habitaciones import Habitacion

almacenista = Blueprint('almacenista', __name__)

# Middleware para verificar permisos de almacenista o superior
def verificar_almacenista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 2:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
    return None

@almacenista.route('/inventario')
def inventario():
    # Verificar permisos de almacenista o superior
    error = verificar_almacenista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))
    
    return render_template('almacenista/inventario.html')

@almacenista.route('/reportes-almacen')
def reportes_almacen():
    # Verificar permisos de almacenista o superior
    error = verificar_almacenista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))
    
    return render_template('almacenista/reportes.html')

@almacenista.route('/estado-habitaciones')
def estado_habitaciones():
    # Verificar permisos de almacenista o superior
    error = verificar_almacenista()
    if error:
        # Redirigir a login si no está autenticado
        return redirect(url_for('auth.login_page'))
    
    return render_template('almacenista/estado_habitaciones.html')

# API para obtener estadísticas de habitaciones para reportes
@almacenista.route('/api/estadisticas-habitaciones', methods=['GET'])
def obtener_estadisticas_habitaciones():
    error = verificar_almacenista()
    if error:
        return error
    
    try:
        habitaciones = Habitacion.query.all()
        
        # Contar por estado
        estadisticas = {
            'total': len(habitaciones),
            'disponible': len([h for h in habitaciones if h.estado == 'disponible']),
            'ocupada': len([h for h in habitaciones if h.estado == 'ocupada']),
            'mantenimiento': len([h for h in habitaciones if h.estado == 'mantenimiento']),
            'limpieza': len([h for h in habitaciones if h.estado == 'limpieza'])
        }
        
        return jsonify(estadisticas)
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

# API para obtener habitaciones con filtros para inventario
@almacenista.route('/api/habitaciones-inventario', methods=['GET'])
def obtener_habitaciones_inventario():
    error = verificar_almacenista()
    if error:
        return error
    
    try:
        estado_filtro = request.args.get('estado', None)
        
        if estado_filtro:
            habitaciones = Habitacion.query.filter_by(estado=estado_filtro).all()
        else:
            habitaciones = Habitacion.query.all()
        
        habitaciones_list = []
        for habitacion in habitaciones:
            habitacion_dict = {
                'idhabitacion': habitacion.idhabitacion,
                'numero': habitacion.numero,
                'estado': habitacion.estado,
                'nombre': habitacion.nombre,
                'capacidad': habitacion.capacidad,
                'servicios': habitacion.servicios or []
            }
            habitaciones_list.append(habitacion_dict)
        
        return jsonify(habitaciones_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener habitaciones: {str(e)}'}), 500