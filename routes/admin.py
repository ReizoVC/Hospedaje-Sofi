from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import os
import uuid
import hashlib
from werkzeug.utils import secure_filename
from utils.db import db
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
from sqlalchemy import text
from models.reserva import Reserva
from models.movimientos import MovimientoInventario
from models.producto import Producto
from models.movimientos import Movimientos
from models.egreso import Egreso
from models.usuario import Usuario
from models.ingreso import Ingreso, registrar_ingreso_por_confirmacion
from datetime import datetime, date
import calendar
from sqlalchemy import and_, or_
from utils.auth import role_required, ROL_ADMIN

admin = Blueprint('admin', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_ESTADOS_HAB = {'disponible', 'ocupada', 'mantenimiento'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verificar_admin():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 4:
        return jsonify({'error': 'Acceso no autorizado - rol insuficiente'}), 403
    return None

def verificar_recepcionista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 2:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de recepcionista o superior'}), 403
    return None

def verificar_almacenista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 3:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
    return None

@admin.route('/gestion')
@role_required(ROL_ADMIN)
def gestion():
    return render_template('admin/gestion.html')

@admin.route('/reportes-admin')
@role_required(ROL_ADMIN)
def reportes_admin():
    return render_template('admin/reportes.html')

@admin.route('/api/habitaciones', methods=['GET'])
def obtener_habitaciones():
    error = verificar_admin()
    if error:
        return error
    try:
        habitaciones = Habitacion.query.all()
        habitaciones_list = []
        for habitacion in habitaciones:
            try:
                habitaciones_list.append(habitacion.to_dict())
            except Exception:
                habitaciones_list.append({
                    'idhabitacion': habitacion.idhabitacion,
                    'numero': habitacion.numero,
                    'estado': habitacion.estado,
                    'nombre': habitacion.nombre,
                    'descripcion': habitacion.descripcion or '',
                    'capacidad': habitacion.capacidad or 0,
                    'precio_noche': float(habitacion.precio_noche) if habitacion.precio_noche else 0.0,
                    'tamano_m2': habitacion.tamano_m2 or 0,
                    'camas': habitacion.camas or '',
                    'servicios': habitacion.servicios or []
                })
        return jsonify(habitaciones_list)
    except Exception as e:
        return jsonify({'error': f'Error al obtener habitaciones: {str(e)}'}), 500

@admin.route('/api/habitaciones/<int:id>', methods=['GET'])
def obtener_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    try:
        habitacion = Habitacion.query.get_or_404(id)
        return jsonify(habitacion.to_dict())
    except Exception as e:
        return jsonify({'error': f'Error al obtener habitación: {str(e)}'}), 500

@admin.route('/api/habitaciones', methods=['POST'])
def crear_habitacion():
    error = verificar_admin()
    if error:
        return error
    try:
        data = request.get_json()
        estado = str(data.get('estado', '')).strip().lower()
        if estado not in ALLOWED_ESTADOS_HAB:
            return jsonify({'error': 'Estado inválido. Permitidos: disponible, ocupada, mantenimiento'}), 400
        numero_str = str(data['numero'])
        if Habitacion.query.filter_by(numero=numero_str).first():
            return jsonify({'error': 'Ya existe una habitación con ese número'}), 400
        nueva_habitacion = Habitacion(
            numero=str(data['numero']),
            estado=estado,
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            capacidad=data['capacidad'],
            precio_noche=data['precio_noche'],
            tamano_m2=data.get('tamano_m2'),
            camas=data.get('camas'),
            servicios=data.get('servicios', [])
        )
        db.session.add(nueva_habitacion)
        db.session.commit()
        return jsonify({'message': 'Habitación creada exitosamente', 'id': nueva_habitacion.idhabitacion}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear habitación: {str(e)}'}), 500

@admin.route('/api/habitaciones/<int:id>', methods=['PUT'])
def actualizar_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    try:
        habitacion = Habitacion.query.get_or_404(id)
        data = request.get_json()
        if 'numero' in data:
            numero_str = str(data['numero'])
            habitacion_existente = Habitacion.query.filter_by(numero=numero_str).first()
            if habitacion_existente and habitacion_existente.idhabitacion != id:
                return jsonify({'error': 'Ya existe una habitación con ese número'}), 400
        if 'numero' in data:
            habitacion.numero = str(data['numero'])
        if 'estado' in data:
            estado = str(data.get('estado', '')).strip().lower()
            if estado not in ALLOWED_ESTADOS_HAB:
                return jsonify({'error': 'Estado inválido. Permitidos: disponible, ocupada, mantenimiento'}), 400
            habitacion.estado = estado
        if 'nombre' in data:
            habitacion.nombre = data['nombre']
        if 'descripcion' in data:
            habitacion.descripcion = data['descripcion']
        if 'capacidad' in data:
            habitacion.capacidad = data['capacidad']
        if 'precio_noche' in data:
            habitacion.precio_noche = data['precio_noche']
        if 'tamano_m2' in data:
            habitacion.tamano_m2 = data['tamano_m2']
        if 'camas' in data:
            habitacion.camas = data['camas']
        if 'servicios' in data:
            habitacion.servicios = data['servicios']
        db.session.commit()
        return jsonify({'message': 'Habitación actualizada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar habitación: {str(e)}'}), 500

@admin.route('/api/habitaciones/<int:id>', methods=['DELETE'])
def eliminar_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    try:
        habitacion = Habitacion.query.get_or_404(id)
        db.session.delete(habitacion)
        db.session.commit()
        return jsonify({'message': 'Habitación eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Imágenes habitaciones
@admin.route('/api/imagenes-habitacion/<int:idhabitacion>', methods=['GET'])
def obtener_imagenes_habitacion(idhabitacion):
    error = verificar_admin()
    if error:
        return error
    try:
        imagenes = ImagenHabitacion.query.filter_by(idhabitacion=idhabitacion).order_by(ImagenHabitacion.orden).all()
        return jsonify([imagen.to_dict() for imagen in imagenes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/imagenes-habitacion', methods=['POST'])
def subir_imagen_habitacion():
    error = verificar_admin()
    if error:
        return error
    try:
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        file = request.files['imagen']
        idhabitacion = request.form.get('idhabitacion')
        orden = request.form.get('orden', 1)
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        Habitacion.query.get_or_404(idhabitacion)
        upload_path = os.path.join('static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        filename = secure_filename(file.filename)
        unique_filename = f"hab_{idhabitacion}_{len(os.listdir(upload_path))}_{filename}"
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        nueva_imagen = ImagenHabitacion(
            idhabitacion=idhabitacion,
            url=unique_filename,
            orden=int(orden)
        )
        db.session.add(nueva_imagen)
        db.session.commit()
        return jsonify({'message': 'Imagen subida exitosamente', 'id': nueva_imagen.idimagen}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/api/imagenes-habitacion/<int:idimagen>', methods=['PUT'])
def actualizar_imagen(idimagen):
    error = verificar_admin()
    if error:
        return error
    try:
        imagen = ImagenHabitacion.query.get_or_404(idimagen)
        data = request.get_json()
        imagen.orden = data.get('orden', imagen.orden)
        db.session.commit()
        return jsonify({'message': 'Imagen actualizada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/api/imagenes-habitacion/<int:idimagen>', methods=['DELETE'])
def eliminar_imagen(idimagen):
    error = verificar_admin()
    if error:
        return error
    try:
        imagen = ImagenHabitacion.query.get_or_404(idimagen)
        file_path = os.path.join('static', 'uploads', imagen.url)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(imagen)
        db.session.commit()
        return jsonify({'message': 'Imagen eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Reservas

def _reserva_to_dict_ext(reserva: Reserva, incluir_relaciones=True):
    data = reserva.to_dict()
    if incluir_relaciones:
        try:
            data['usuario'] = reserva.usuario.to_dict() if reserva.usuario else None
        except Exception:
            if reserva.usuario:
                data['usuario'] = {
                    'idusuario': str(reserva.usuario.idusuario),
                    'nombre': reserva.usuario.nombre,
                    'apellidos': reserva.usuario.apellidos,
                    'correo': reserva.usuario.correo,
                    'rol': reserva.usuario.rol,
                }
            else:
                data['usuario'] = None
        try:
            data['habitacion'] = reserva.habitacion.to_dict() if reserva.habitacion else None
        except Exception:
            if reserva.habitacion:
                data['habitacion'] = {
                    'idhabitacion': reserva.habitacion.idhabitacion,
                    'numero': reserva.habitacion.numero,
                    'nombre': reserva.habitacion.nombre,
                    'estado': reserva.habitacion.estado,
                }
            else:
                data['habitacion'] = None
    return data

@admin.route('/api/reservas', methods=['GET'])
def admin_listar_reservas():
    error = verificar_admin()
    if error:
        return error
    try:
        reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).all()
        return jsonify([_reserva_to_dict_ext(r) for r in reservas])
    except Exception as e:
        return jsonify({'error': f'Error al obtener reservas: {str(e)}'}), 500

@admin.route('/api/reservas/<int:idreserva>', methods=['GET'])
def admin_obtener_reserva(idreserva):
    error = verificar_admin()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(idreserva)
        return jsonify(_reserva_to_dict_ext(reserva))
    except Exception as e:
        return jsonify({'error': f'Error al obtener reserva: {str(e)}'}), 500

@admin.route('/api/reservas/opciones', methods=['GET'])
def admin_reservas_opciones():
    error = verificar_admin()
    if error:
        return error
    try:
        usuarios = Usuario.query.filter(Usuario.rol > 0).order_by(Usuario.nombre.asc()).all()
        habitaciones = Habitacion.query.order_by(Habitacion.numero.asc()).all()
        return jsonify({
            'usuarios': [u.to_dict() for u in usuarios],
            'habitaciones': [h.to_dict() for h in habitaciones]
        })
    except Exception as e:
        return jsonify({'error': f'Error al cargar opciones: {str(e)}'}), 500

def _parse_fecha(fecha_str: str):
    return datetime.strptime(fecha_str, '%Y-%m-%d').date()

def _validar_disponibilidad(idhabitacion, fechainicio, fechafin, ignorar_id=None):
    q = Reserva.query.filter(
        Reserva.idhabitacion == idhabitacion,
        Reserva.estado.in_(['pendiente', 'confirmada']),
        or_(
            and_(Reserva.fechainicio <= fechainicio, Reserva.fechafin > fechainicio),
            and_(Reserva.fechainicio < fechafin, Reserva.fechafin >= fechafin),
            and_(Reserva.fechainicio >= fechainicio, Reserva.fechafin <= fechafin)
        )
    )
    if ignorar_id is not None:
        q = q.filter(Reserva.idreserva != ignorar_id)
    return q.first() is None

@admin.route('/api/reservas', methods=['POST'])
def admin_crear_reserva():
    error = verificar_admin()
    if error:
        return error
    try:
        data = request.get_json()
        requeridos = ['idusuario', 'idhabitacion', 'fechainicio', 'fechafin']
        if not data or not all(k in data for k in requeridos):
            return jsonify({'error': 'Faltan datos requeridos'}), 400
        fechainicio = _parse_fecha(data['fechainicio'])
        fechafin = _parse_fecha(data['fechafin'])
        if fechainicio < date.today():
            return jsonify({'error': 'La fecha de inicio no puede ser en el pasado'}), 400
        if fechafin <= fechainicio:
            return jsonify({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        habitacion = Habitacion.query.get_or_404(data['idhabitacion'])
        usuario = Usuario.query.get_or_404(uuid.UUID(str(data['idusuario'])))
        if not _validar_disponibilidad(habitacion.idhabitacion, fechainicio, fechafin):
            return jsonify({'error': 'La habitación no está disponible en esas fechas'}), 400
        nueva = Reserva(
            idusuario=usuario.idusuario,
            idhabitacion=habitacion.idhabitacion,
            fechainicio=fechainicio,
            fechafin=fechafin,
            estado=data.get('estado', 'pendiente')
        )
        db.session.add(nueva)
        db.session.commit()
        return jsonify({'message': 'Reserva creada', 'reserva': _reserva_to_dict_ext(nueva)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear reserva: {str(e)}'}), 500

@admin.route('/api/reservas/<int:idreserva>', methods=['PUT'])
def admin_actualizar_reserva(idreserva):
    error = verificar_admin()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(idreserva)
        data = request.get_json() or {}
        
        # Validar primero datos antes de modificar
        id_hab_nuevo = data.get('idhabitacion', reserva.idhabitacion)
        fecha_inicio_nuevo = _parse_fecha(data['fechainicio']) if 'fechainicio' in data else reserva.fechainicio
        fecha_fin_nuevo = _parse_fecha(data['fechafin']) if 'fechafin' in data else reserva.fechafin
        
        # Validación de fechas
        if fecha_inicio_nuevo >= fecha_fin_nuevo:
            return jsonify({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        
        # Validación de disponibilidad (antes de modificar)
        if not _validar_disponibilidad(id_hab_nuevo, fecha_inicio_nuevo, fecha_fin_nuevo, ignorar_id=idreserva):
            return jsonify({'error': 'La habitación no está disponible en esas fechas'}), 400
        
        # Aplicar cambios
        if 'idusuario' in data:
            usuario = Usuario.query.get_or_404(uuid.UUID(str(data['idusuario'])))
            reserva.idusuario = usuario.idusuario
        if 'idhabitacion' in data:
            habitacion = Habitacion.query.get_or_404(data['idhabitacion'])
            reserva.idhabitacion = habitacion.idhabitacion
        if 'fechainicio' in data:
            reserva.fechainicio = fecha_inicio_nuevo
        if 'fechafin' in data:
            reserva.fechafin = fecha_fin_nuevo
        if 'estado' in data:
            estado_nuevo = str(data.get('estado', '')).strip().lower()
            reserva.estado = estado_nuevo
        
        db.session.commit()
        return jsonify({'message': 'Reserva actualizada', 'reserva': _reserva_to_dict_ext(reserva)})
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': f'Error al parsear fecha: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar reserva: {str(e)}'}), 500

@admin.route('/api/reservas/<int:idreserva>/estado', methods=['PUT'])
def admin_actualizar_estado_reserva(idreserva):
    error = verificar_admin()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(idreserva)
        data = request.get_json() or {}
        nuevo_estado = data.get('estado')
        if not nuevo_estado:
            return jsonify({'error': 'Estado requerido'}), 400
        if nuevo_estado not in ['pendiente', 'confirmada', 'cancelada', 'activa', 'completada']:
            return jsonify({'error': 'Estado inválido'}), 400
        crear_ingreso = (
            (nuevo_estado in ['confirmada', 'completada']) and (reserva.estado != nuevo_estado)
        )
        reserva.estado = nuevo_estado
        if crear_ingreso:
            habitacion = Habitacion.query.get(reserva.idhabitacion)
            registrar_ingreso_por_confirmacion(reserva, habitacion=habitacion)
        db.session.commit()
        return jsonify({'message': 'Estado actualizado', 'reserva': reserva.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500

@admin.route('/api/reservas/<int:idreserva>', methods=['DELETE'])
def admin_eliminar_reserva(idreserva):
    error = verificar_admin()
    if error:
        return error
    try:
        reserva = Reserva.query.get_or_404(idreserva)
        if reserva.estado in ['activa', 'completada']:
            return jsonify({'error': 'No se puede eliminar una reserva activa o completada'}), 400
        db.session.delete(reserva)
        db.session.commit()
        return jsonify({'message': 'Reserva eliminada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar reserva: {str(e)}'}), 500

# Reportes admin: ingresos / egresos

def _rango_fechas_default():
    from datetime import timedelta
    hoy = date.today()
    return hoy - timedelta(days=30), hoy

@admin.route('/api/reportes/admin/ingresos', methods=['GET'])
def api_reportes_admin_ingresos():
    error = verificar_admin()
    if error:
        return error
    try:
        desde_str = request.args.get('desde')
        hasta_str = request.args.get('hasta')
        estados_str = request.args.get('estados')
        d_desde = None
        d_hasta = None
        if desde_str and hasta_str:
            d_desde = _parse_fecha(desde_str)
            d_hasta = _parse_fecha(hasta_str)
        estados = ['confirmada', 'completada']
        if estados_str:
            estados = [e.strip() for e in estados_str.split(',') if e.strip()]
        q = Reserva.query.filter(Reserva.estado.in_(estados))
        if d_desde and d_hasta:
            q = q.filter(
                Reserva.fechainicio >= d_desde,
                Reserva.fechainicio <= d_hasta
            )
        q = q.order_by(Reserva.fechainicio.asc())
        items = []
        total = 0.0
        for r in q.all():
            try:
                noches = (r.fechafin - r.fechainicio).days
                precio = float(r.habitacion.precio_noche) if r.habitacion and r.habitacion.precio_noche else 0.0
                monto = max(noches, 0) * precio
                total += monto
                items.append({
                    'idreserva': r.idreserva,
                    'fecha_inicio': r.fechainicio.isoformat() if r.fechainicio else None,
                    'fecha_fin': r.fechafin.isoformat() if r.fechafin else None,
                    'estado': r.estado,
                    'habitacion': r.habitacion.to_dict() if r.habitacion else None,
                    'noches': noches,
                    'monto': round(monto, 2),
                })
            except Exception:
                continue
        return jsonify({
            'desde': d_desde.isoformat() if d_desde else None,
            'hasta': d_hasta.isoformat() if d_hasta else None,
            'items': items,
            'total': round(total, 2),
        })
    except Exception as e:
        return jsonify({'error': f'Error al generar reporte de ingresos: {str(e)}'}), 500

@admin.route('/api/reportes/admin/ingresos/total-general', methods=['GET'])
def api_reportes_admin_ingresos_total_general():
    error = verificar_admin()
    if error:
        return error
    try:
        estados = ['confirmada', 'completada']
        hoy = date.today()
        q = Reserva.query.filter(
            Reserva.estado.in_(estados),
            Reserva.fechainicio.isnot(None),
            Reserva.fechainicio <= hoy
        )
        total = 0.0
        for r in q.all():
            try:
                noches = (r.fechafin - r.fechainicio).days if r.fechafin and r.fechainicio else 0
                precio = float(r.habitacion.precio_noche) if r.habitacion and r.habitacion.precio_noche else 0.0
                monto = max(noches, 0) * precio
                total += monto
            except Exception:
                continue
        return jsonify({'total': round(total, 2)})
    except Exception as e:
        return jsonify({'error': f'Error al obtener total general de ingresos: {str(e)}'}), 500

@admin.route('/api/reportes/admin/ingresos/periodos', methods=['GET'])
def api_reportes_admin_ingresos_periodos():
    error = verificar_admin()
    if error:
        return error
    try:
        estados_str = request.args.get('estados')
        estados = ['confirmada', 'completada']
        if estados_str:
            estados = [e.strip() for e in estados_str.split(',') if e.strip()]

        fechas = (Reserva.query
            .filter(
                Reserva.estado.in_(estados),
                Reserva.fechainicio.isnot(None)
            )
            .with_entities(Reserva.fechainicio)
            .all())

        dias_set = set()
        semanas_set = set()
        meses_set = set()
        for (fecha,) in fechas:
            if not fecha:
                continue
            dias_set.add(fecha)
            iso = fecha.isocalendar()
            semanas_set.add((iso[0], iso[1]))
            meses_set.add((fecha.year, fecha.month))

        dias = sorted(dias_set, reverse=True)
        semanas = sorted(semanas_set, reverse=True)
        meses = sorted(meses_set, reverse=True)

        dias_payload = [
            {
                'value': d.isoformat(),
                'label': d.isoformat(),
                'desde': d.isoformat(),
                'hasta': d.isoformat()
            }
            for d in dias
        ]

        semanas_payload = []
        for y, w in semanas:
            inicio = date.fromisocalendar(y, w, 1)
            fin = date.fromisocalendar(y, w, 7)
            semanas_payload.append({
                'value': f'{y}-W{w:02d}',
                'label': f'{y} Semana {w:02d} ({inicio.isoformat()} - {fin.isoformat()})',
                'desde': inicio.isoformat(),
                'hasta': fin.isoformat()
            })

        meses_payload = []
        for y, m in meses:
            inicio = date(y, m, 1)
            fin = date(y, m, calendar.monthrange(y, m)[1])
            meses_payload.append({
                'value': f'{y}-{m:02d}',
                'label': f'{y}-{m:02d}',
                'desde': inicio.isoformat(),
                'hasta': fin.isoformat()
            })

        return jsonify({
            'dias': dias_payload,
            'semanas': semanas_payload,
            'meses': meses_payload
        })
    except Exception as e:
        return jsonify({'error': f'Error al cargar periodos de ingresos: {str(e)}'}), 500

@admin.route('/api/reportes/admin/egresos', methods=['GET'])
def api_reportes_admin_egresos():
    error = verificar_admin()
    if error:
        return error
    try:
        desde_str = request.args.get('desde')
        hasta_str = request.args.get('hasta')
        if desde_str and hasta_str:
            d_desde = _parse_fecha(desde_str)
            d_hasta = _parse_fecha(hasta_str)
        else:
            d_desde, d_hasta = _rango_fechas_default()
        q = Egreso.query.filter(
            Egreso.fechaegreso >= d_desde,
            Egreso.fechaegreso <= d_hasta
        ).order_by(Egreso.fechaegreso.asc())
        items = []
        total = 0.0
        egresos = q.all()
        productos_cache = {}
        mov_cache = {}
        for e in egresos:
            try:
                m = getattr(e, 'movimiento', None) or mov_cache.get(e.idmovimiento) or Movimientos.query.get(e.idmovimiento)
                mov_cache[e.idmovimiento] = m
                p = None
                if m and m.idproducto is not None:
                    p = productos_cache.get(m.idproducto) or Producto.query.get(m.idproducto)
                    productos_cache[m.idproducto] = p
                cantidad = int(m.cantidad or 0) if m else 0
                costo_unit = 0.0
                if m and cantidad:
                    try:
                        costo_unit = float(m.costototal or 0) / cantidad
                    except Exception:
                        costo_unit = 0.0
                monto = float(e.monto or 0.0)
                total += monto
                items.append({
                    'idegreso': e.idegreso,
                    'fecha': e.fechaegreso.isoformat() if e.fechaegreso else None,
                    'producto': p.to_dict() if p else ({'idproducto': m.idproducto} if m and m.idproducto is not None else None),
                    'tipo': (m.tipo if m else None),
                    'cantidad': cantidad,
                    'costo_unitario': round(costo_unit, 2),
                    'monto': round(monto, 2),
                })
            except Exception:
                continue
        return jsonify({
            'desde': d_desde.isoformat(),
            'hasta': d_hasta.isoformat(),
            'items': items,
            'total': round(total, 2),
        })
    except Exception as e:
        return jsonify({'error': f'Error al generar reporte de egresos: {str(e)}'}), 500

# Personal

def _validar_rol_personal(rol: int):
    try:
        r = int(rol)
    except Exception:
        return False
    return r in [2, 3, 4]

@admin.route('/api/personal', methods=['GET'])
def admin_listar_personal():
    error = verificar_admin()
    if error:
        return error
    try:
        personal = Usuario.query.filter(Usuario.rol.in_([2, 3, 4])).order_by(Usuario.nombre.asc()).all()
        return jsonify([u.to_dict() for u in personal])
    except Exception as e:
        return jsonify({'error': f'Error al obtener personal: {str(e)}'}), 500

@admin.route('/api/personal/desactivados', methods=['GET'])
def admin_listar_personal_desactivado():
    error = verificar_admin()
    if error:
        return error
    try:
        personal = Usuario.query.filter(Usuario.rol == 0).order_by(Usuario.nombre.asc()).all()
        return jsonify([u.to_dict() for u in personal])
    except Exception as e:
        return jsonify({'error': f'Error al obtener personal desactivado: {str(e)}'}), 500

@admin.route('/api/personal', methods=['POST'])
def admin_crear_personal():
    error = verificar_admin()
    if error:
        return error
    try:
        raw = request.get_json() or {}
        data = {
            'nombre': (raw.get('nombre') or '').strip(),
            'apellidos': (raw.get('apellidos') or '').strip(),
            'dni': (raw.get('dni') or '').strip(),
            'correo': (raw.get('correo') or '').strip().lower(),
            'telefono': (raw.get('telefono') or '').strip() or None,
            'clave': raw.get('clave') or '',
            'rol': raw.get('rol')
        }
        requeridos = ['nombre', 'apellidos', 'dni', 'correo', 'clave', 'rol']
        faltantes = [k for k in requeridos if not data.get(k)]
        if faltantes:
            return jsonify({'error': f'Faltan datos requeridos: {", ".join(faltantes)}'}), 400
        if not data['dni'].isdigit() or len(data['dni']) not in (8, 9):
            return jsonify({'error': 'DNI inválido'}), 400
        if '@' not in data['correo'] or '.' not in data['correo'].split('@')[-1]:
            return jsonify({'error': 'Correo inválido'}), 400
        if not _validar_rol_personal(data['rol']):
            return jsonify({'error': 'Rol inválido'}), 400
        if Usuario.query.filter_by(correo=data['correo']).first():
            return jsonify({'error': 'El correo ya está registrado'}), 400
        if Usuario.query.filter_by(dni=data['dni']).first():
            return jsonify({'error': 'El DNI ya está registrado'}), 400
        nuevo = Usuario(
            nombre=data['nombre'],
            apellidos=data['apellidos'],
            dni=data['dni'],
            correo=data['correo'],
            telefono=data.get('telefono'),
            clave=hashlib.md5(data['clave'].encode()).hexdigest(),
            rol=int(data['rol'])
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({'message': 'Personal creado', 'usuario': nuevo.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear personal: {str(e)}'}), 500

@admin.route('/api/personal/<uuid:idusuario>', methods=['PUT'])
def admin_actualizar_personal(idusuario):
    error = verificar_admin()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(idusuario)
        data = request.get_json() or {}
        if 'correo' in data and data['correo'] != usuario.correo:
            if Usuario.query.filter(Usuario.correo == data['correo'], Usuario.idusuario != usuario.idusuario).first():
                return jsonify({'error': 'El correo ya está registrado'}), 400
            usuario.correo = data['correo']
        if 'dni' in data and data['dni'] != usuario.dni:
            if Usuario.query.filter(Usuario.dni == data['dni'], Usuario.idusuario != usuario.idusuario).first():
                return jsonify({'error': 'El DNI ya está registrado'}), 400
            usuario.dni = data['dni']
        if 'nombre' in data:
            usuario.nombre = data['nombre']
        if 'apellidos' in data:
            usuario.apellidos = data['apellidos']
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        if 'rol' in data:
            if not _validar_rol_personal(data['rol']) and int(data['rol']) != 0:
                return jsonify({'error': 'Rol inválido'}), 400
            usuario.rol = int(data['rol'])
        if 'clave' in data and data['clave']:
            usuario.clave = hashlib.md5(data['clave'].encode()).hexdigest()
        db.session.commit()
        return jsonify({'message': 'Personal actualizado', 'usuario': usuario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar personal: {str(e)}'}), 500

@admin.route('/api/personal/<uuid:idusuario>', methods=['DELETE'])
def admin_desactivar_personal(idusuario):
    error = verificar_admin()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(idusuario)
        if usuario.rol == 4 and str(usuario.idusuario) == str(session.get('user_id')):
            return jsonify({'error': 'No puede desactivar su propia cuenta'}), 400
        usuario.rol = 0
        db.session.commit()
        return jsonify({'message': 'Personal desactivado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al desactivar personal: {str(e)}'}), 500

@admin.route('/api/personal/<uuid:idusuario>/reactivar', methods=['PUT'])
def admin_reactivar_personal(idusuario):
    error = verificar_admin()
    if error:
        return error
    try:
        usuario = Usuario.query.get_or_404(idusuario)
        data = request.get_json() or {}
        rol = int(data.get('rol', 2))
        if not _validar_rol_personal(rol):
            return jsonify({'error': 'Rol inválido'}), 400
        usuario.rol = rol
        db.session.commit()
        return jsonify({'message': 'Personal reactivado', 'usuario': usuario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al reactivar personal: {str(e)}'}), 500