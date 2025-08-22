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
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    if session.get('user_rol', 0) < 1:
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
            habitaciones_list.append(habitacion.to_dict())
        
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
        estados_validos = ['disponible', 'ocupada', 'mantenimiento']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido'}), 400
        
        habitacion.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({'message': f'Estado de habitación {habitacion.numero} actualizado a {nuevo_estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500

# ============ RUTAS PARA GESTIÓN DE USUARIOS (SOLO CLIENTES) ============

# API para obtener todos los usuarios con rol 1 (clientes activos)
# Nota: rol 0 son cuentas eliminadas/desactivadas
@recepcionista.route('/api/usuarios-clientes', methods=['GET'])
def obtener_usuarios_clientes():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        # Solo obtener usuarios con rol 1 (clientes activos) - rol 0 son cuentas eliminadas
        usuarios = Usuario.query.filter_by(rol=1).all()
        usuarios_list = [usuario.to_dict() for usuario in usuarios]
        
        return jsonify(usuarios_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuarios: {str(e)}'}), 500

# API para obtener usuarios desactivados (rol 0)
@recepcionista.route('/api/usuarios-desactivados', methods=['GET'])
def obtener_usuarios_desactivados():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        # Obtener usuarios con rol 0 (cuentas desactivadas)
        usuarios = Usuario.query.filter_by(rol=0).all()
        usuarios_list = [usuario.to_dict() for usuario in usuarios]
        
        return jsonify(usuarios_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuarios desactivados: {str(e)}'}), 500

# API para crear un nuevo usuario cliente (rol 0)
@recepcionista.route('/api/usuarios-clientes', methods=['POST'])
def crear_usuario_cliente():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        data = request.get_json()
        
        # Validar que el DNI no exista
        if Usuario.query.filter_by(dni=data['dni']).first():
            return jsonify({'error': 'Ya existe un usuario con este DNI'}), 400
        
        # Validar que el correo no exista
        if Usuario.query.filter_by(correo=data['correo']).first():
            return jsonify({'error': 'Ya existe un usuario con este correo'}), 400

        # Hashear la contraseña con MD5
        password_hash = hashlib.md5(data['clave'].encode()).hexdigest()

        nuevo_usuario = Usuario(
            nombre=data['nombre'],
            apellidos=data['apellidos'],
            dni=data['dni'],
            correo=data['correo'],
            telefono=data.get('telefono'),
            clave=password_hash,
            rol=1  # Rol 1 para clientes activos
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return jsonify({'message': 'Usuario cliente creado exitosamente'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500

# API para actualizar un usuario cliente
@recepcionista.route('/api/usuarios-clientes/<uuid:id>', methods=['PUT'])
def actualizar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        usuario = Usuario.query.get_or_404(id)
        
        # Verificar que sea un cliente (rol 1) y no esté desactivado (rol 0)
        if usuario.rol != 1:
            return jsonify({'error': 'Solo se pueden editar usuarios clientes activos'}), 403
        
        data = request.get_json()
        
        # Validar DNI único si se está cambiando
        if 'dni' in data and data['dni'] != usuario.dni:
            if Usuario.query.filter_by(dni=data['dni']).first():
                return jsonify({'error': 'Ya existe un usuario con este DNI'}), 400
        
        # Validar correo único si se está cambiando
        if 'correo' in data and data['correo'] != usuario.correo:
            if Usuario.query.filter_by(correo=data['correo']).first():
                return jsonify({'error': 'Ya existe un usuario con este correo'}), 400
        
        # Actualizar campos
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

# API para desactivar un usuario cliente (eliminación lógica)
@recepcionista.route('/api/usuarios-clientes/<uuid:id>', methods=['DELETE'])
def eliminar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        usuario = Usuario.query.get_or_404(id)
        
        # Verificar que sea un cliente activo (rol 1) - rol 0 son cuentas ya eliminadas
        if usuario.rol != 1:
            return jsonify({'error': 'Solo se pueden desactivar usuarios clientes activos'}), 403
        
        # Eliminación lógica: cambiar rol a 0 (cuenta desactivada) en lugar de borrar físicamente
        # Esto preserva los datos para auditorías y referencias de reservas
        usuario.rol = 0
        
        db.session.commit()
        
        return jsonify({'message': 'Usuario desactivado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al desactivar usuario: {str(e)}'}), 500

# API para reactivar un usuario cliente
@recepcionista.route('/api/usuarios-clientes/<uuid:id>/reactivar', methods=['PUT'])
def reactivar_usuario_cliente(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        usuario = Usuario.query.get_or_404(id)
        
        # Verificar que sea una cuenta desactivada (rol 0)
        if usuario.rol != 0:
            return jsonify({'error': 'Solo se pueden reactivar usuarios desactivados'}), 403
        
        # Reactivar: cambiar rol a 1 (cliente activo)
        usuario.rol = 1
        
        db.session.commit()
        
        return jsonify({'message': 'Usuario reactivado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al reactivar usuario: {str(e)}'}), 500

# ============ RUTAS PARA GESTIÓN DE RESERVAS ============

# API para obtener todas las reservas
@recepcionista.route('/recep/api/reservas', methods=['GET'])
def obtener_reservas():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        # Filtrar reservas excluyendo las completadas (no se muestran en este menú)
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

# API para obtener estadísticas de reservas
@recepcionista.route('/recep/api/reservas/estadisticas', methods=['GET'])
def obtener_estadisticas_reservas():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        # Total excluyendo las completadas (no se muestran en este menú)
        total = Reserva.query.filter(Reserva.estado != 'completada').count()
        pendientes = Reserva.query.filter_by(estado='pendiente').count()
        confirmadas = Reserva.query.filter_by(estado='confirmada').count()
        activas = Reserva.query.filter_by(estado='activa').count()
        canceladas = Reserva.query.filter_by(estado='cancelada').count()
        
        estadisticas = {
            'total': total,
            'pendientes': pendientes,
            'confirmadas': confirmadas,
            'activas': activas,
            'canceladas': canceladas
        }
        
        return jsonify(estadisticas)
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

# API para crear una nueva reserva
@recepcionista.route('/recep/api/reservas', methods=['POST'])
def crear_reserva():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        campos_requeridos = ['idusuario', 'idhabitacion', 'fechainicio', 'fechafin']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'error': f'Campo requerido: {campo}'}), 400
        
        # Validar fechas
        fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        
        if fecha_inicio >= fecha_fin:
            return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400
        
        if fecha_inicio < date.today():
            return jsonify({'error': 'La fecha de inicio no puede ser en el pasado'}), 400
        
        # Validar que el usuario exista
        usuario = Usuario.query.get(data['idusuario'])
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Validar que la habitación exista
        habitacion = Habitacion.query.get(data['idhabitacion'])
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        
        # Verificar disponibilidad de la habitación
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
        
        # Crear la reserva
        estado = data.get('estado', 'pendiente')
        nueva_reserva = Reserva(
            idusuario=data['idusuario'],
            idhabitacion=data['idhabitacion'],
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            estado=estado
        )
        
        db.session.add(nueva_reserva)
        db.session.flush()  # obtener idreserva antes de commit
        
        # Si se crea ya confirmada, registrar ingreso inmediatamente
        if estado == 'confirmada':
            registrar_ingreso_por_confirmacion(nueva_reserva, habitacion=habitacion)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reserva creada exitosamente',
            'codigo_reserva': nueva_reserva.codigoreserva
        }), 201
    except ValueError as e:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear reserva: {str(e)}'}), 500

# API para actualizar el estado de una reserva
@recepcionista.route('/recep/api/reservas/<int:id>/estado', methods=['PUT'])
def actualizar_estado_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        reserva = Reserva.query.get_or_404(id)
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        # Validar estados permitidos (excluyendo 'activa' que solo se asigna por check-in)
        estados_validos = ['pendiente', 'confirmada', 'cancelada']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido. El estado "activa" solo se asigna mediante check-in.'}), 400
        
        # Si pasa a confirmada y antes no lo estaba, registrar ingreso
        crear_ingreso = (nuevo_estado == 'confirmada' and reserva.estado != 'confirmada')
        
        reserva.estado = nuevo_estado
        
        if crear_ingreso:
            # calcular y crear ingreso asociado a la reserva confirmada
            habitacion = Habitacion.query.get(reserva.idhabitacion)
            registrar_ingreso_por_confirmacion(reserva, habitacion=habitacion)
        
        db.session.commit()
        
        return jsonify({'message': f'Estado de reserva actualizado a {nuevo_estado}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500

# API para eliminar una reserva
@recepcionista.route('/recep/api/reservas/<int:id>', methods=['DELETE'])
def eliminar_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        reserva = Reserva.query.get_or_404(id)
        
        # Solo permitir eliminar reservas pendientes o canceladas
        if reserva.estado in ['confirmada', 'completada']:
            return jsonify({'error': 'No se pueden eliminar reservas confirmadas o completadas'}), 400
        
        db.session.delete(reserva)
        db.session.commit()
        
        return jsonify({'message': 'Reserva eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar reserva: {str(e)}'}), 500

# API para obtener una reserva específica
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

# API para actualizar una reserva completa
@recepcionista.route('/recep/api/reservas/<int:id>', methods=['PUT'])
def actualizar_reserva(id):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400

        # Buscar la reserva
        reserva = Reserva.query.filter_by(idreserva=id).first()
        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        prev_estado = reserva.estado

        # Verificar si ya pasó la fecha de inicio
        hoy = date.today()
        ya_comenzo = reserva.fechainicio <= hoy
        es_pendiente = reserva.estado == 'pendiente'

        # Solo se puede editar completamente si es pendiente Y no ha comenzado
        puede_editar_completo = es_pendiente and not ya_comenzo

        # Si no se puede editar completamente, solo permitir cambio de estado
        if not puede_editar_completo:
            if 'estado' not in data:
                if not es_pendiente and not ya_comenzo:
                    return jsonify({'error': 'Solo las reservas pendientes pueden editarse completamente. Esta reserva solo permite cambio de estado.'}), 400
                elif ya_comenzo and es_pendiente:
                    return jsonify({'error': 'La reserva ya comenzó. Solo se puede cambiar el estado.'}), 400
                else:
                    return jsonify({'error': 'La reserva ya comenzó y no está pendiente. Solo se puede cambiar el estado.'}), 400

            # Solo actualizar el estado (excluyendo 'activa' que solo se asigna por check-in)
            estados_validos = ['pendiente', 'confirmada', 'cancelada']
            if data['estado'] not in estados_validos:
                return jsonify({'error': 'Estado de reserva inválido. El estado "activa" solo se asigna mediante check-in.'}), 400

            reserva.estado = data['estado']
            # Si cambia a confirmada y no lo estaba, registrar ingreso
            if data['estado'] == 'confirmada' and prev_estado != 'confirmada':
                hab = Habitacion.query.get(reserva.idhabitacion)
                registrar_ingreso_por_confirmacion(reserva, habitacion=hab)
            db.session.commit()

            return jsonify({
                'mensaje': 'Estado de reserva actualizado exitosamente',
                'reserva': reserva.to_dict(),
                'solo_estado': True
            })

        # Si se puede editar completamente, validar todos los campos
        required_fields = ['idhabitacion', 'fechainicio', 'fechafin', 'estado']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400

        # El usuario nunca se puede cambiar, usar el de la reserva actual
        data['idusuario'] = reserva.idusuario

        # Validar que el usuario existe
        usuario = Usuario.query.filter_by(idusuario=data['idusuario']).first()
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 400

        # Validar que la habitación existe
        habitacion = Habitacion.query.filter_by(idhabitacion=data['idhabitacion']).first()
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 400

        # Validar fechas
        try:
            fecha_inicio = datetime.strptime(data['fechainicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(data['fechafin'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400

        if fecha_inicio >= fecha_fin:
            return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400

        # Validar que la habitación esté disponible para las nuevas fechas
        # (excepto si no cambió la habitación o las fechas)
        if (reserva.idhabitacion != data['idhabitacion'] or
            reserva.fechainicio != fecha_inicio or
            reserva.fechafin != fecha_fin):

            reservas_conflicto = Reserva.query.filter(
                Reserva.idhabitacion == data['idhabitacion'],
                Reserva.idreserva != id,  # Excluir la reserva actual
                Reserva.estado.in_(['confirmada', 'activa']),
                or_(
                    and_(Reserva.fechainicio <= fecha_inicio, Reserva.fechafin > fecha_inicio),
                    and_(Reserva.fechainicio < fecha_fin, Reserva.fechafin >= fecha_fin),
                    and_(Reserva.fechainicio >= fecha_inicio, Reserva.fechafin <= fecha_fin)
                )
            ).first()

            if reservas_conflicto:
                return jsonify({'error': 'La habitación no está disponible para las fechas seleccionadas'}), 400

        # Validar estado válido (solo los que se pueden crear manualmente)
        estados_validos = ['pendiente', 'confirmada']
        if data['estado'] not in estados_validos:
            return jsonify({'error': 'Estado de reserva inválido. Solo se permiten: pendiente, confirmada'}), 400

        # Actualizar la reserva
        reserva.idusuario = data['idusuario']
        reserva.idhabitacion = data['idhabitacion']
        reserva.fechainicio = fecha_inicio
        reserva.fechafin = fecha_fin
        reserva.estado = data['estado']

        # Recalcular el total si cambió la habitación o las fechas
        if (reserva.idhabitacion != data['idhabitacion'] or
            reserva.fechainicio != fecha_inicio or
            reserva.fechafin != fecha_fin):

            dias = (fecha_fin - fecha_inicio).days
            reserva.total = habitacion.precio_noche * dias

        # Si cambia a confirmada y no lo estaba, registrar ingreso
        if data['estado'] == 'confirmada' and prev_estado != 'confirmada':
            registrar_ingreso_por_confirmacion(reserva, habitacion=habitacion)
        db.session.commit()

        return jsonify({
            'mensaje': 'Reserva actualizada exitosamente',
            'reserva': reserva.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar reserva: {str(e)}'}), 500

# ============ RUTAS PARA CHECK-IN / CHECK-OUT ============

# API para obtener reservas para check-in/check-out
@recepcionista.route('/api/check/reservas', methods=['GET'])
def obtener_reservas_check():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        # Obtener reservas confirmadas que están en las fechas actuales o próximas
        hoy = date.today()
        
        # Reservas para check-in (fecha de inicio es hoy o en el pasado y aún no tienen check-in)
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
        
        # Reservas para check-out (habitaciones ocupadas)
        reservas_checkout = db.session.query(Reserva, Usuario, Habitacion).join(
            Usuario, Reserva.idusuario == Usuario.idusuario
        ).join(
            Habitacion, Reserva.idhabitacion == Habitacion.idhabitacion
        ).filter(
            Reserva.estado == 'activa'  # Estado activa significa que ya hicieron check-in
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

# API para obtener estadísticas de check-in/check-out
@recepcionista.route('/api/check/estadisticas', methods=['GET'])
def obtener_estadisticas_check():
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        hoy = date.today()
        
        # Reservas pendientes de check-in
        pendientes_checkin = Reserva.query.filter(
            and_(
                Reserva.estado == 'confirmada',
                Reserva.fechainicio <= hoy
            )
        ).count()
        
        # Reservas pendientes de check-out
        pendientes_checkout = Reserva.query.filter_by(estado='activa').count()
        
        # Habitaciones ocupadas
        habitaciones_ocupadas = Habitacion.query.filter_by(estado='ocupada').count()
        
        estadisticas = {
            'pendientes_checkin': pendientes_checkin,
            'pendientes_checkout': pendientes_checkout,
            'habitaciones_ocupadas': habitaciones_ocupadas
        }
        
        return jsonify(estadisticas)
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

# API para realizar check-in
@recepcionista.route('/api/check/checkin/<int:id_reserva>', methods=['POST'])
def realizar_checkin(id_reserva):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        reserva = Reserva.query.get_or_404(id_reserva)
        
        # Validar que la reserva esté en estado confirmada
        if reserva.estado != 'confirmada':
            return jsonify({'error': 'Solo se puede hacer check-in a reservas confirmadas'}), 400
        
        # Verificar que la fecha de inicio sea hoy o en el pasado
        if reserva.fechainicio > date.today():
            return jsonify({'error': 'La fecha de check-in aún no ha llegado'}), 400
        
        # Obtener la habitación
        habitacion = Habitacion.query.get(reserva.idhabitacion)
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        
        # Verificar que la habitación esté disponible
        if habitacion.estado != 'disponible':
            return jsonify({'error': 'La habitación no está disponible para check-in'}), 400
        
        # Realizar el check-in
        reserva.estado = 'activa'  # Cambiar estado a activa
        habitacion.estado = 'ocupada'  # Marcar habitación como ocupada
        
        # Registrar o actualizar registro en checkinout
        registro = CheckInOut.query.filter_by(idreserva=reserva.idreserva).first()
        if not registro:
            registro = CheckInOut(idreserva=reserva.idreserva, checkin=datetime.now())
            db.session.add(registro)
        else:
            registro.checkin = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Check-in realizado exitosamente',
            'reserva': reserva.codigoreserva,
            'habitacion': habitacion.numero
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al realizar check-in: {str(e)}'}), 500

# API para realizar check-out
@recepcionista.route('/api/check/checkout/<int:id_reserva>', methods=['POST'])
def realizar_checkout(id_reserva):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        reserva = Reserva.query.get_or_404(id_reserva)
        
        # Validar que la reserva esté en estado activa (con check-in realizado)
        if reserva.estado != 'activa':
            return jsonify({'error': 'Solo se puede hacer check-out a reservas activas'}), 400
        
        # Obtener la habitación
        habitacion = Habitacion.query.get(reserva.idhabitacion)
        if not habitacion:
            return jsonify({'error': 'Habitación no encontrada'}), 404
        
        # Verificar que la habitación esté ocupada
        if habitacion.estado != 'ocupada':
            return jsonify({'error': 'La habitación no está marcada como ocupada'}), 400
        
        # Realizar el check-out
        reserva.estado = 'completada'  # Cambiar estado a completada
        habitacion.estado = 'mantenimiento'  # Marcar habitación para limpieza
        
        # Registrar checkout en tabla checkinout
        registro = CheckInOut.query.filter_by(idreserva=reserva.idreserva).first()
        if not registro:
            # Si por alguna razón no hay registro de check-in previo, crear uno con checkout
            registro = CheckInOut(idreserva=reserva.idreserva, checkout=datetime.now())
            db.session.add(registro)
        else:
            registro.checkout = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Check-out realizado exitosamente',
            'reserva': reserva.codigoreserva,
            'habitacion': habitacion.numero
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al realizar check-out: {str(e)}'}), 500

# API para marcar habitación como disponible después de limpieza
@recepcionista.route('/api/check/habitacion/<int:id_habitacion>/disponible', methods=['PUT'])
def marcar_habitacion_disponible(id_habitacion):
    error = verificar_recepcionista()
    if error:
        return error
    
    try:
        habitacion = Habitacion.query.get_or_404(id_habitacion)
        
        # Solo permitir cambiar de mantenimiento a disponible
        if habitacion.estado != 'mantenimiento':
            return jsonify({'error': 'Solo se pueden marcar como disponibles las habitaciones en mantenimiento'}), 400
        
        habitacion.estado = 'disponible'
        db.session.commit()
        
        return jsonify({
            'message': f'Habitación {habitacion.numero} marcada como disponible',
            'habitacion': habitacion.numero
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al marcar habitación como disponible: {str(e)}'}), 500