from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from utils.auth import redirect_staff_to_dashboard
from utils.db import db
from models.reserva import Reserva
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
from models.usuario import Usuario
from datetime import datetime, date
import uuid
from sqlalchemy import and_, or_

reservas = Blueprint('reservas', __name__, url_prefix='/reservas')


def _cargar_habitacion_con_imagenes(idhabitacion):
    habitacion = Habitacion.query.get_or_404(idhabitacion)
    imagenes = ImagenHabitacion.query.filter_by(
        idhabitacion=idhabitacion
    ).order_by(ImagenHabitacion.orden).all()
    habitacion_data = habitacion.to_dict()
    habitacion_data['imagenes'] = [
        f"/static/uploads/{img.url}" for img in imagenes
    ] if imagenes else ["/static/images/index/hab1.avif"]
    return habitacion_data


@reservas.before_request
def _bloquear_trabajadores_en_reservas():
    rol = session.get('user_rol')
    if rol in (2, 3, 4):
        # Para endpoints tipo API/POST devolvemos JSON 403
        if request.method != 'GET' or request.is_json:
            return jsonify({'success': False, 'message': 'Acceso no autorizado para trabajadores'}), 403
        flash('Acceso no autorizado para trabajadores.', 'error')
        resp = redirect_staff_to_dashboard()
        return resp if resp is not None else redirect('/trabajadores')

@reservas.route('/crear', methods=['POST'])
def crear_reserva():
    """Crear una nueva reserva"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Debe iniciar sesión para hacer una reserva'}), 401
        
        data = request.get_json()
        
        if not all(k in data for k in ['idhabitacion', 'fechainicio', 'fechafin']):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400

        plan = data.get('plan', 'total')
        if plan not in ('parcial', 'total'):
            plan = 'total'
        
        fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        
        if fecha_inicio < date.today():
            return jsonify({'success': False, 'message': 'La fecha de inicio no puede ser en el pasado'}), 400
        
        if fecha_fin <= fecha_inicio:
            return jsonify({'success': False, 'message': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        
        habitacion = Habitacion.query.get(data['idhabitacion'])
        if not habitacion:
            return jsonify({'success': False, 'message': 'Habitación no encontrada'}), 404
        
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
        
        user_uuid = uuid.UUID(session['user_id']) if isinstance(session['user_id'], str) else session['user_id']
        estado_reserva = 'pendiente' if plan == 'parcial' else 'confirmada'
        nueva_reserva = Reserva(
            idusuario=user_uuid,
            idhabitacion=data['idhabitacion'],
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            estado=estado_reserva
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


@reservas.route('/paso-1/<int:idhabitacion>')
def reserva_paso1(idhabitacion):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    habitacion_data = _cargar_habitacion_con_imagenes(idhabitacion)
    return render_template('pages/reserva_fechas.html', habitacion=habitacion_data)


@reservas.route('/paso-2/<int:idhabitacion>')
def reserva_paso2(idhabitacion):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    habitacion_data = _cargar_habitacion_con_imagenes(idhabitacion)
    fechainicio = request.args.get('inicio')
    fechafin = request.args.get('fin')
    noches = None
    total = None
    monto_parcial = None
    saldo = None
    error = None

    if fechainicio and fechafin:
        try:
            inicio = datetime.strptime(fechainicio, '%Y-%m-%d').date()
            fin = datetime.strptime(fechafin, '%Y-%m-%d').date()
            if fin <= inicio:
                error = 'La fecha de salida debe ser posterior a la fecha de llegada'
            else:
                noches = (fin - inicio).days
                total = int(noches * (habitacion_data.get('precio_noche') or 0))
                monto_parcial = int(round(total * 0.6))
                saldo = total - monto_parcial
        except ValueError:
            error = 'Fechas invalidas. Vuelve al paso anterior.'
    else:
        error = 'Faltan fechas. Vuelve al paso anterior.'

    monto_parcial = int(round((total or 0) * 0.6)) if total is not None else None
    saldo = (total - monto_parcial) if total is not None else None

    return render_template(
        'pages/reserva_plan.html',
        habitacion=habitacion_data,
        fechainicio=fechainicio,
        fechafin=fechafin,
        noches=noches,
        total=total,
        monto_parcial=monto_parcial,
        saldo=saldo,
        error=error
    )


@reservas.route('/paso-3/<int:idhabitacion>')
def reserva_paso3(idhabitacion):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    habitacion_data = _cargar_habitacion_con_imagenes(idhabitacion)
    fechainicio = request.args.get('inicio')
    fechafin = request.args.get('fin')
    plan = request.args.get('plan', 'total')
    if plan not in ('parcial', 'total'):
        plan = 'total'
    noches = None
    total = None
    monto_parcial = None
    saldo = None
    error = None

    if fechainicio and fechafin:
        try:
            inicio = datetime.strptime(fechainicio, '%Y-%m-%d').date()
            fin = datetime.strptime(fechafin, '%Y-%m-%d').date()
            if fin <= inicio:
                error = 'La fecha de salida debe ser posterior a la fecha de llegada'
            else:
                noches = (fin - inicio).days
                total = int(noches * (habitacion_data.get('precio_noche') or 0))
                monto_parcial = int(round(total * 0.6))
                saldo = total - monto_parcial
        except ValueError:
            error = 'Fechas invalidas. Vuelve al paso anterior.'
    else:
        error = 'Faltan fechas. Vuelve al paso anterior.'

    return render_template(
        'pages/reserva_pago.html',
        habitacion=habitacion_data,
        fechainicio=fechainicio,
        fechafin=fechafin,
        noches=noches,
        total=total,
        monto_parcial=monto_parcial,
        saldo=saldo,
        plan=plan,
        error=error
    )

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

        reservas_principales = [
            r for r in reservas_data if r.get('estado') in ('pendiente', 'confirmada')
        ]
        reservas_canceladas = [
            r for r in reservas_data if r.get('estado') == 'cancelada'
        ]
        
        return render_template(
            'pages/mis_reservas.html',
            reservas=reservas_principales,
            reservas_canceladas=reservas_canceladas
        )
        
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


@reservas.route('/bloqueadas/<int:idhabitacion>')
def fechas_bloqueadas(idhabitacion):
    """Fechas bloqueadas (reservadas) para una habitacion"""
    try:
        hoy = date.today()
        reservas_bloqueadas = Reserva.query.filter(
            Reserva.idhabitacion == idhabitacion,
            Reserva.estado.in_(['pendiente', 'confirmada', 'activa']),
            Reserva.fechafin >= hoy
        ).all()

        rangos = [
            {
                'inicio': r.fechainicio.isoformat(),
                'fin': r.fechafin.isoformat()
            }
            for r in reservas_bloqueadas
        ]

        return jsonify({'rangos': rangos})
    except Exception as e:
        print(f"Error al obtener fechas bloqueadas: {str(e)}")
        return jsonify({'rangos': []}), 500

@reservas.route('/cancelar/<codigo_reserva>', methods=['POST'])
def cancelar_reserva(codigo_reserva):
    """Cancelar una reserva"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Debe iniciar sesión'}), 401
        
        user_uuid = uuid.UUID(session['user_id']) if isinstance(session['user_id'], str) else session['user_id']
        reserva = Reserva.query.filter_by(
            codigoreserva=codigo_reserva,
            idusuario=user_uuid
        ).first()
        
        if not reserva:
            return jsonify({'success': False, 'message': 'Reserva no encontrada'}), 404
        
        if reserva.estado == 'cancelada':
            return jsonify({'success': False, 'message': 'La reserva ya está cancelada'}), 400
        
        if reserva.estado == 'completada':
            return jsonify({'success': False, 'message': 'No se puede cancelar una reserva completada'}), 400
        
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