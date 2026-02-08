from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.db import db
from models.habitaciones import Habitacion
from models.usuario import Usuario
from models.reserva import Reserva
from models.checkinout import CheckInOut
from models.ingreso import registrar_ingreso_por_confirmacion
import hashlib
from datetime import datetime, date
from sqlalchemy import and_, or_

recepcionista = Blueprint('recepcionista', __name__)

def verificar_recepcionista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    rol = session.get('user_rol', 0)
    if rol != 2 and rol < 4:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de recepcionista'}), 403
    return None

@recepcionista.route('/estado-habitaciones')
def estado_habitaciones():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    rol = session.get('user_rol', 0)
    if rol != 2 and rol < 4:
        return redirect(url_for('auth.login_page'))
    return render_template('recepcionista/estado-hab.html')

@recepcionista.route('/gestion-reservas')
def gestion_reservas():
    error = verificar_recepcionista()
    if error:
        return redirect(url_for('auth.login_page'))
    return render_template('recepcionista/gestion_reservas.html')

@recepcionista.route('/check')
def check_in_out():
    error = verificar_recepcionista()
    if error:
        return redirect(url_for('auth.login_page'))
    return render_template('recepcionista/check.html')

@recepcionista.route('/gestion-usuario')
def gestion_usuarios():
    error = verificar_recepcionista()
    if error:
        return redirect(url_for('auth.login_page'))
    return render_template('recepcionista/gestion_usuario.html')

@recepcionista.route('/api/habitaciones-estado', methods=['GET'])
def obtener_habitaciones_estado():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        habitaciones = Habitacion.query.all()
        habitaciones_list = [h.to_dict() for h in habitaciones]
        return jsonify(habitaciones_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener habitaciones: {str(e)}'}), 500

@recepcionista.route('/api/habitaciones/<int:id>/estado', methods=['PUT'])
def cambiar_estado_habitacion(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        habitacion = Habitacion.query.get_or_404(id)
        data = request.get_json()
        nuevo_estado = data.get('estado')
        estados_validos = ['disponible', 'ocupada', 'mantenimiento']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido'}), 400
        habitacion.estado = nuevo_estado
        db.session.commit()
        return jsonify({'message': f'Estado de habitación {habitacion.numero} actualizado a {nuevo_estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500

# Usuarios clientes
@recepcionista.route('/api/usuarios-clientes', methods=['GET'])
def obtener_usuarios_clientes():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        usuarios = Usuario.query.filter_by(rol=1).all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuarios: {str(e)}'}), 500

@recepcionista.route('/api/usuarios-desactivados', methods=['GET'])
def obtener_usuarios_desactivados():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        usuarios = Usuario.query.filter_by(rol=0).all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuarios desactivados: {str(e)}'}), 500

@recepcionista.route('/api/usuarios-clientes', methods=['POST'])
def crear_usuario_cliente():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        data = request.get_json()
        if Usuario.query.filter_by(dni=data['dni']).first():
            return jsonify({'error': 'Ya existe un usuario con este DNI'}), 400
        if Usuario.query.filter_by(correo=data['correo']).first():
            return jsonify({'error': 'Ya existe un usuario con este correo'}), 400
        password_hash = hashlib.md5(data['clave'].encode()).hexdigest()
        nuevo_usuario = Usuario(
            nombre=data['nombre'],
            apellidos=data['apellidos'],
            dni=data['dni'],
            correo=data['correo'],
            telefono=data.get('telefono'),
            clave=password_hash,
            rol=1
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({'message': 'Usuario cliente creado exitosamente'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500

@recepcionista.route('/api/usuarios-clientes/<uuid:id>', methods=['PUT'])
def actualizar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(id)
        if usuario.rol != 1:
            return jsonify({'error': 'Solo se pueden editar usuarios clientes activos'}), 403
        data = request.get_json()
        if 'dni' in data and data['dni'] != usuario.dni:
            if Usuario.query.filter_by(dni=data['dni']).first():
                return jsonify({'error': 'Ya existe un usuario con este DNI'}), 400
        if 'correo' in data and data['correo'] != usuario.correo:
            if Usuario.query.filter_by(correo=data['correo']).first():
                return jsonify({'error': 'Ya existe un usuario con este correo'}), 400
        if 'nombre' in data:
            usuario.nombre = data['nombre']
        if 'apellidos' in data:
            usuario.apellidos = data['apellidos']
        if 'dni' in data:
            usuario.dni = data['dni']
        if 'correo' in data:
            usuario.correo = data['correo']
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        if 'clave' in data and data['clave']:
            usuario.clave = hashlib.md5(data['clave'].encode()).hexdigest()
        db.session.commit()
        return jsonify({'message': 'Usuario actualizado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar usuario: {str(e)}'}), 500

@recepcionista.route('/api/usuarios-clientes/<uuid:id>', methods=['DELETE'])
def eliminar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(id)
        if usuario.rol != 1:
            return jsonify({'error': 'Solo se pueden desactivar usuarios clientes activos'}), 403
        usuario.rol = 0
        db.session.commit()
        return jsonify({'message': 'Usuario desactivado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al desactivar usuario: {str(e)}'}), 500

@recepcionista.route('/api/usuarios-clientes/<uuid:id>/reactivar', methods=['PUT'])
def reactivar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(id)
        if usuario.rol != 0:
            return jsonify({'error': 'Solo se pueden reactivar usuarios desactivados'}), 403
        usuario.rol = 1
        db.session.commit()
        return jsonify({'message': 'Usuario reactivado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al reactivar usuario: {str(e)}'}), 500

# Reservas
@recepcionista.route('/recep/api/reservas', methods=['GET'])
def obtener_reservas():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        reservas = db.session.query(Reserva, Usuario, Habitacion).join(
            Usuario, Reserva.idusuario == Usuario.idusuario
        ).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(Reserva.estado != 'completada').all()
        reservas_list = []
        for reserva, usuario, habitacion in reservas:
            reserva_dict = reserva.to_dict()
            reserva_dict['usuario'] = {
                'nombre': usuario.nombre,
                'apellidos': usuario.apellidos,
                'correo': usuario.correo,
                'dni': usuario.dni
            }
            reserva_dict['habitacion'] = {
                'numero': habitacion.numero,
                'nombre': habitacion.nombre
            }
            reservas_list.append(reserva_dict)
        return jsonify(reservas_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener reservas: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas/estadisticas', methods=['GET'])
def obtener_estadisticas_reservas():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        total = Reserva.query.filter(Reserva.estado != 'completada').count()
        pendientes = Reserva.query.filter_by(estado='pendiente').count()
        confirmadas = Reserva.query.filter_by(estado='confirmada').count()
        activas = Reserva.query.filter_by(estado='activa').count()
        canceladas = Reserva.query.filter_by(estado='cancelada').count()
        return jsonify({
            'total': total,
            'pendientes': pendientes,
            'confirmadas': confirmadas,
            'activas': activas,
            'canceladas': canceladas
        })
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas', methods=['POST'])
def crear_reserva():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        data = request.get_json()
        campos_requeridos = ['idusuario', 'idhabitacion', 'fechainicio', 'fechafin']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'error': f'Campo requerido: {campo}'}), 400
        fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        if fecha_inicio >= fecha_fin:
            return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400
        if fecha_inicio < date.today():
            return jsonify({'error': 'La fecha de inicio no puede ser en el pasado'}), 400
        usuario = Usuario.query.get(data['idusuario'])
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        habitacion = Habitacion.query.get(data['idhabitacion'])
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        reservas_existentes = Reserva.query.filter(
            and_(
                Reserva.idhabitacion == data['idhabitacion'],
                Reserva.estado != 'cancelada',
                or_(
                    and_(Reserva.fechainicio <= fecha_inicio, Reserva.fechafin > fecha_inicio),
                    and_(Reserva.fechainicio < fecha_fin, Reserva.fechafin >= fecha_fin),
                    and_(Reserva.fechainicio >= fecha_inicio, Reserva.fechafin <= fecha_fin)
                )
            )
        ).first()
        if reservas_existentes:
            return jsonify({'error': 'La habitación no está disponible en las fechas seleccionadas'}), 400
        estado = data.get('estado', 'pendiente')
        nueva_reserva = Reserva(
            idusuario=data['idusuario'],
            idhabitacion=data['idhabitacion'],
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            estado=estado
        )
        db.session.add(nueva_reserva)
        db.session.flush()
        if estado == 'confirmada':
            registrar_ingreso_por_confirmacion(nueva_reserva, habitacion=habitacion)
        db.session.commit()
        return jsonify({'message': 'Reserva creada exitosamente', 'codigo_reserva': nueva_reserva.codigoreserva}), 201
    except ValueError as e:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear reserva: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas/<int:id>/estado', methods=['PUT'])
def actualizar_estado_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(id)
        data = request.get_json()
        nuevo_estado = data.get('estado')
        estados_validos = ['pendiente', 'confirmada', 'cancelada']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido. El estado "activa" solo se asigna mediante check-in.'}), 400
        crear_ingreso = (nuevo_estado == 'confirmada' and reserva.estado != 'confirmada')
        reserva.estado = nuevo_estado
        if crear_ingreso:
            habitacion = Habitacion.query.get(reserva.idhabitacion)
            registrar_ingreso_por_confirmacion(reserva, habitacion=habitacion)
        db.session.commit()
        return jsonify({'message': f'Estado de reserva actualizado a {nuevo_estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas/<int:id>', methods=['DELETE'])
def eliminar_reserva(id):
    from models.ingreso import Ingreso
    error = verificar_recepcionista()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(id)
        # No se pueden eliminar reservas activas o completadas
        if reserva.estado in ['activa', 'completada']:
            return jsonify({'error': 'No se pueden eliminar reservas activas o completadas'}), 400
        
        # Verificar si existen ingresos asociados a esta reserva
        ingreso_existente = Ingreso.query.filter_by(idreserva=id).first()
        if ingreso_existente:
            return jsonify({'error': 'No se puede eliminar una reserva que tiene ingresos registrados. Contacte al administrador.'}), 400
        
        db.session.delete(reserva)
        db.session.commit()
        return jsonify({'message': 'Reserva eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar reserva: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas/<int:id>', methods=['GET'])
def obtener_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        resultado = db.session.query(Reserva, Usuario, Habitacion).join(
            Usuario, Reserva.idusuario == Usuario.idusuario
        ).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(Reserva.idreserva == id).first()
        if not resultado:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        reserva, usuario, habitacion = resultado
        reserva_dict = reserva.to_dict()
        reserva_dict['usuario'] = {
            'nombre': usuario.nombre,
            'apellidos': usuario.apellidos,
            'correo': usuario.correo,
            'dni': usuario.dni,
            'telefono': usuario.telefono
        }
        reserva_dict['habitacion'] = {
            'numero': habitacion.numero,
            'nombre': habitacion.nombre,
            'precio_noche': float(habitacion.precio_noche) if habitacion.precio_noche else 0.0
        }
        return jsonify(reserva_dict)
    except Exception as e:
        return jsonify({'error': f'Error al obtener reserva: {str(e)}'}), 500

@recepcionista.route('/recep/api/reservas/<int:id>', methods=['PUT'])
def actualizar_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        reserva = Reserva.query.filter_by(idreserva=id).first()
        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        prev_estado = reserva.estado
        hoy = date.today()
        ya_comenzo = reserva.fechainicio <= hoy
        es_pendiente = reserva.estado == 'pendiente'
        puede_editar_completo = es_pendiente and not ya_comenzo
        if not puede_editar_completo:
            if 'estado' not in data:
                if not es_pendiente and not ya_comenzo:
                    return jsonify({'error': 'Solo las reservas pendientes pueden editarse completamente. Esta reserva solo permite cambio de estado.'}), 400
                elif ya_comenzo and es_pendiente:
                    return jsonify({'error': 'La reserva ya comenzó. Solo se puede cambiar el estado.'}), 400
                else:
                    return jsonify({'error': 'La reserva ya comenzó y no está pendiente. Solo se puede cambiar el estado.'}), 400
            estados_validos = ['pendiente', 'confirmada', 'cancelada']
            if data['estado'] not in estados_validos:
                return jsonify({'error': 'Estado de reserva inválido. El estado "activa" solo se asigna mediante check-in.'}), 400
            reserva.estado = data['estado']
            if data['estado'] == 'confirmada' and prev_estado != 'confirmada':
                hab = Habitacion.query.get(reserva.idhabitacion)
                registrar_ingreso_por_confirmacion(reserva, habitacion=hab)
            db.session.commit()
            return jsonify({'mensaje': 'Estado de reserva actualizado exitosamente', 'reserva': reserva.to_dict(), 'solo_estado': True})
        required_fields = ['idhabitacion', 'fechainicio', 'fechafin', 'estado']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        data['idusuario'] = reserva.idusuario
        usuario = Usuario.query.filter_by(idusuario=data['idusuario']).first()
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 400
        habitacion = Habitacion.query.filter_by(idhabitacion=data['idhabitacion']).first()
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 400
        try:
            fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        if fecha_inicio >= fecha_fin:
            return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400
        if (reserva.idhabitacion != data['idhabitacion'] or
            reserva.fechainicio != fecha_inicio or
            reserva.fechafin != fecha_fin):
            reservas_conflicto = Reserva.query.filter(
                Reserva.idhabitacion == data['idhabitacion'],
                Reserva.idreserva != id,
                Reserva.estado.in_(['confirmada', 'activa']),
                or_(
                    and_(Reserva.fechainicio <= fecha_inicio, Reserva.fechafin > fecha_inicio),
                    and_(Reserva.fechainicio < fecha_fin, Reserva.fechafin >= fecha_fin),
                    and_(Reserva.fechainicio >= fecha_inicio, Reserva.fechafin <= fecha_fin)
                )
            ).first()
            if reservas_conflicto:
                return jsonify({'error': 'La habitación no está disponible para las fechas seleccionadas'}), 400
        estados_validos = ['pendiente', 'confirmada']
        if data['estado'] not in estados_validos:
            return jsonify({'error': 'Estado de reserva inválido. Solo se permiten: pendiente, confirmada'}), 400
        reserva.idusuario = data['idusuario']
        reserva.idhabitacion = data['idhabitacion']
        reserva.fechainicio = fecha_inicio
        reserva.fechafin = fecha_fin
        reserva.estado = data['estado']
        if (reserva.idhabitacion != data['idhabitacion'] or
            reserva.fechainicio != fecha_inicio or
            reserva.fechafin != fecha_fin):
            dias = (fecha_fin - fecha_inicio).days
            reserva.total = habitacion.precio_noche * dias
        if data['estado'] == 'confirmada' and prev_estado != 'confirmada':
            registrar_ingreso_por_confirmacion(reserva, habitacion=habitacion)
        db.session.commit()
        return jsonify({'mensaje': 'Reserva actualizada exitosamente', 'reserva': reserva.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar reserva: {str(e)}'}), 500

# Check-in / Check-out
@recepcionista.route('/api/check/reservas', methods=['GET'])
def obtener_reservas_check():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        hoy = date.today()
        reservas_checkin = db.session.query(Reserva, Usuario, Habitacion).join(
            Usuario, Reserva.idusuario == Usuario.idusuario
        ).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(
            and_(
                Reserva.estado == 'confirmada',
                Reserva.fechainicio <= hoy
            )
        ).all()
        reservas_checkout = db.session.query(Reserva, Usuario, Habitacion).join(
            Usuario, Reserva.idusuario == Usuario.idusuario
        ).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(
            Reserva.estado == 'activa'
        ).all()
        def formatear_reserva_check(reserva, usuario, habitacion, tipo_check):
            return {
                'idreserva': reserva.idreserva,
                'codigoreserva': reserva.codigoreserva,
                'fechainicio': reserva.fechainicio.isoformat(),
                'fechafin': reserva.fechafin.isoformat(),
                'estado': reserva.estado,
                'tipo_check': tipo_check,
                'usuario': {
                    'idusuario': str(usuario.idusuario),
                    'nombre': usuario.nombre,
                    'apellidos': usuario.apellidos,
                    'correo': usuario.correo,
                    'dni': usuario.dni,
                    'telefono': usuario.telefono
                },
                'habitacion': {
                    'idhabitacion': habitacion.idhabitacion,
                    'numero': habitacion.numero,
                    'nombre': habitacion.nombre,
                    'estado': habitacion.estado
                }
            }
        resultado = {
            'checkin': [formatear_reserva_check(r, u, h, 'checkin') for r, u, h in reservas_checkin],
            'checkout': [formatear_reserva_check(r, u, h, 'checkout') for r, u, h in reservas_checkout]
        }
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': f'Error al obtener reservas para check: {str(e)}'}), 500

@recepcionista.route('/api/check/estadisticas', methods=['GET'])
def obtener_estadisticas_check():
    error = verificar_recepcionista()
    if error:
        return error
    try:
        hoy = date.today()
        pendientes_checkin = Reserva.query.filter(
            and_(
                Reserva.estado == 'confirmada',
                Reserva.fechainicio <= hoy
            )
        ).count()
        pendientes_checkout = Reserva.query.filter_by(estado='activa').count()
        habitaciones_ocupadas = Habitacion.query.filter_by(estado='ocupada').count()
        return jsonify({
            'pendientes_checkin': pendientes_checkin,
            'pendientes_checkout': pendientes_checkout,
            'habitaciones_ocupadas': habitaciones_ocupadas
        })
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

@recepcionista.route('/api/check/checkin/<int:id_reserva>', methods=['POST'])
def realizar_checkin(id_reserva):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(id_reserva)
        if reserva.estado != 'confirmada':
            return jsonify({'error': 'Solo se puede hacer check-in a reservas confirmadas'}), 400
        if reserva.fechainicio > date.today():
            return jsonify({'error': 'La fecha de check-in aún no ha llegado'}), 400
        habitacion = Habitacion.query.get(reserva.idhabitacion)
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        if habitacion.estado != 'disponible':
            return jsonify({'error': 'La habitación no está disponible para check-in'}), 400
        reserva.estado = 'activa'
        habitacion.estado = 'ocupada'
        registro = CheckInOut.query.filter_by(idreserva=reserva.idreserva).first()
        if not registro:
            registro = CheckInOut(idreserva=reserva.idreserva, checkin=datetime.now())
            db.session.add(registro)
        else:
            registro.checkin = datetime.now()
        db.session.commit()
        return jsonify({'message': 'Check-in realizado exitosamente', 'reserva': reserva.codigoreserva, 'habitacion': habitacion.numero})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al realizar check-in: {str(e)}'}), 500

@recepcionista.route('/api/check/checkout/<int:id_reserva>', methods=['POST'])
def realizar_checkout(id_reserva):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(id_reserva)
        if reserva.estado != 'activa':
            return jsonify({'error': 'Solo se puede hacer check-out a reservas activas'}), 400
        habitacion = Habitacion.query.get(reserva.idhabitacion)
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        if habitacion.estado != 'ocupada':
            return jsonify({'error': 'La habitación no está marcada como ocupada'}), 400
        reserva.estado = 'completada'
        habitacion.estado = 'mantenimiento'
        registro = CheckInOut.query.filter_by(idreserva=reserva.idreserva).first()
        if not registro:
            registro = CheckInOut(idreserva=reserva.idreserva, checkout=datetime.now())
            db.session.add(registro)
        else:
            registro.checkout = datetime.now()
        db.session.commit()
        return jsonify({'message': 'Check-out realizado exitosamente', 'reserva': reserva.codigoreserva, 'habitacion': habitacion.numero})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al realizar check-out: {str(e)}'}), 500

@recepcionista.route('/api/check/habitacion/<int:id_habitacion>/disponible', methods=['PUT'])
def marcar_habitacion_disponible(id_habitacion):
    error = verificar_recepcionista()
    if error:
        return error
    try:
        habitacion = Habitacion.query.get_or_404(id_habitacion)
        if habitacion.estado != 'mantenimiento':
            return jsonify({'error': 'Solo se pueden marcar como disponibles las habitaciones en mantenimiento'}), 400
        habitacion.estado = 'disponible'
        db.session.commit()
        return jsonify({'message': f'Habitación {habitacion.numero} marcada como disponible', 'habitacion': habitacion.numero})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al marcar habitación como disponible: {str(e)}'}), 500