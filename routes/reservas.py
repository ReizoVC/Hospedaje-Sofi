from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from utils.db import db
from models.reserva import Reserva
from models.habitaciones import Habitacion
from models.usuario import Usuario
from datetime import datetime, date
import uuid
from sqlalchemy import and_, or_

reservas = Blueprint('reservas', __name__, url_prefix='/reservas')

@reservas.route('/crear', methods=['POST'])
def crear_reserva():
    """Crear una nueva reserva"""
    try:
        # Verificar que el usuario esté logueado
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Debe iniciar sesión para hacer una reserva'}), 401
        
        data = request.get_json()
        
        # Validar datos requeridos
        if not all(k in data for k in ['idhabitacion', 'fechainicio', 'fechafin']):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
        
        # Convertir fechas
        fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        
        # Validar fechas
        if fecha_inicio < date.today():
            return jsonify({'success': False, 'message': 'La fecha de inicio no puede ser en el pasado'}), 400
        
        if fecha_fin <= fecha_inicio:
            return jsonify({'success': False, 'message': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        
        # Verificar que la habitación existe
        habitacion = Habitacion.query.get(data['idhabitacion'])
        if not habitacion:
            return jsonify({'success': False, 'message': 'Habitación no encontrada'}), 404
        
        # Verificar disponibilidad (que no haya reservas confirmadas en esas fechas)
        reservas_existentes = Reserva.query.filter(
            Reserva.idhabitacion == data['idhabitacion'],
            Reserva.estado.in_(['pendiente', 'confirmada']),
            or_(
                and_(Reserva.fechainicio <= fecha_inicio, Reserva.fechafin > fecha_inicio),
                and_(Reserva.fechainicio < fecha_fin, Reserva.fechafin >= fecha_fin),
                and_(Reserva.fechainicio >= fecha_inicio, Reserva.fechafin <= fecha_fin)
            )
        ).first()
        
        if reservas_existentes:
            return jsonify({'success': False, 'message': 'La habitación no está disponible en esas fechas'}), 400
        
        # Crear la reserva
        user_uuid = uuid.UUID(session['user_id']) if isinstance(session['user_id'], str) else session['user_id']
        nueva_reserva = Reserva(
            idusuario=user_uuid,
            idhabitacion=data['idhabitacion'],
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            estado='pendiente'
        )
        
        db.session.add(nueva_reserva)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Reserva creada exitosamente',
            'codigo_reserva': nueva_reserva.codigoreserva,
            'idreserva': nueva_reserva.idreserva
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear reserva: {str(e)}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@reservas.route('/mis-reservas')
def mis_reservas():
    """Mostrar las reservas del usuario actual"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    try:
        user_uuid = uuid.UUID(session['user_id']) if isinstance(session['user_id'], str) else session['user_id']
        reservas_usuario = db.session.query(Reserva, Habitacion).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(Reserva.idusuario == user_uuid).order_by(
            Reserva.fecha_creacion.desc()
        ).all()
        
        reservas_data = []
        for reserva, habitacion in reservas_usuario:
            reserva_dict = reserva.to_dict()
            reserva_dict['habitacion'] = habitacion.to_dict()
            reservas_data.append(reserva_dict)
        
        return render_template('pages/mis_reservas.html', reservas=reservas_data)
        
    except Exception as e:
        print(f"Error al cargar reservas: {str(e)}")
        flash('Error al cargar las reservas', 'error')
        return redirect(url_for('inicio.index'))

@reservas.route('/verificar-disponibilidad', methods=['POST'])
def verificar_disponibilidad():
    """Verificar si una habitación está disponible en fechas específicas"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['idhabitacion', 'fechainicio', 'fechafin']):
            return jsonify({'disponible': False, 'message': 'Faltan datos requeridos'}), 400
        
        fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        
        # Verificar disponibilidad
        reservas_existentes = Reserva.query.filter(
            Reserva.idhabitacion == data['idhabitacion'],
            Reserva.estado.in_(['pendiente', 'confirmada']),
            or_(
                and_(Reserva.fechainicio <= fecha_inicio, Reserva.fechafin > fecha_inicio),
                and_(Reserva.fechainicio < fecha_fin, Reserva.fechafin >= fecha_fin),
                and_(Reserva.fechainicio >= fecha_inicio, Reserva.fechafin <= fecha_fin)
            )
        ).first()
        
        disponible = reservas_existentes is None
        
        return jsonify({
            'disponible': disponible,
            'message': 'Habitación disponible' if disponible else 'Habitación no disponible en esas fechas'
        })
        
    except Exception as e:
        print(f"Error al verificar disponibilidad: {str(e)}")
        return jsonify({'disponible': False, 'message': 'Error al verificar disponibilidad'}), 500

@reservas.route('/cancelar/<codigo_reserva>', methods=['POST'])
def cancelar_reserva(codigo_reserva):
    """Cancelar una reserva"""
    try:
        # Verificar que el usuario esté logueado
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Debe iniciar sesión'}), 401
        
        # Buscar la reserva
        user_uuid = uuid.UUID(session['user_id']) if isinstance(session['user_id'], str) else session['user_id']
        reserva = Reserva.query.filter_by(
            codigoreserva=codigo_reserva,
            idusuario=user_uuid
        ).first()
        
        if not reserva:
            return jsonify({'success': False, 'message': 'Reserva no encontrada'}), 404
        
        # Verificar que se pueda cancelar
        if reserva.estado == 'cancelada':
            return jsonify({'success': False, 'message': 'La reserva ya está cancelada'}), 400
        
        if reserva.estado == 'completada':
            return jsonify({'success': False, 'message': 'No se puede cancelar una reserva completada'}), 400
        
        # Cancelar la reserva
        reserva.estado = 'cancelada'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reserva cancelada exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al cancelar reserva: {str(e)}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500