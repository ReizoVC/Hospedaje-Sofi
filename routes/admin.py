from flask import Blueprint, render_template, request, jsonify, session
from utils.db import db
from models.habitaciones import Habitacion

admin = Blueprint('admin', __name__)

# Middleware para verificar permisos de administrador
def verificar_admin():
    print(f"Verificando admin - user_id: {session.get('user_id')}, user_rol: {session.get('user_rol')}")
    if 'user_id' not in session:
        print("No hay user_id en session")
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 3:
        print(f"Rol insuficiente: {session.get('user_rol')}")
        return jsonify({'error': 'Acceso no autorizado - rol insuficiente'}), 403
    return None

@admin.route('/gestion')
def gestion():
    # Verificar en el frontend con JavaScript, no bloquear aquí
    return render_template('admin/gestion.html')

# API para obtener todas las habitaciones
@admin.route('/api/habitaciones', methods=['GET'])
def obtener_habitaciones():
    print("Intentando obtener habitaciones...")
    error = verificar_admin()
    if error:
        print("Error de verificación de admin")
        return error
    
    try:
        print("Consultando base de datos...")
        habitaciones = Habitacion.query.all()
        print(f"Encontradas {len(habitaciones)} habitaciones")
        
        habitaciones_list = []
        for habitacion in habitaciones:
            try:
                habitacion_dict = habitacion.to_dict()
                habitaciones_list.append(habitacion_dict)
            except Exception as e:
                print(f"Error al convertir habitación {habitacion.idhabitacion}: {str(e)}")
                # Fallback manual
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
        
        print(f"Devolviendo {len(habitaciones_list)} habitaciones")
        return jsonify(habitaciones_list)
    except Exception as e:
        print(f"Error al obtener habitaciones: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al obtener habitaciones: {str(e)}'}), 500

# API para obtener una habitación específica
@admin.route('/api/habitaciones/<int:id>', methods=['GET'])
def obtener_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    
    try:
        habitacion = Habitacion.query.get_or_404(id)
        return jsonify(habitacion.to_dict())
    except Exception as e:
        print(f"Error al obtener habitación {id}: {str(e)}")
        return jsonify({'error': f'Error al obtener habitación: {str(e)}'}), 500

# API para crear una nueva habitación
@admin.route('/api/habitaciones', methods=['POST'])
def crear_habitacion():
    error = verificar_admin()
    if error:
        return error
    
    try:
        data = request.get_json()
        print(f"Datos recibidos para crear habitación: {data}")
        
        # Validar que el número de habitación no exista
        if Habitacion.query.filter_by(numero=data['numero']).first():
            return jsonify({'error': 'Ya existe una habitación con ese número'}), 400
        
        nueva_habitacion = Habitacion(
            numero=data['numero'],
            estado=data['estado'],
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
        print(f"Error al crear habitación: {str(e)}")
        return jsonify({'error': f'Error al crear habitación: {str(e)}'}), 500

# API para actualizar una habitación
@admin.route('/api/habitaciones/<int:id>', methods=['PUT'])
def actualizar_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    
    try:
        habitacion = Habitacion.query.get_or_404(id)
        data = request.get_json()
        
        # Validar que el número de habitación no exista en otra habitación
        habitacion_existente = Habitacion.query.filter_by(numero=data['numero']).first()
        if habitacion_existente and habitacion_existente.idhabitacion != id:
            return jsonify({'error': 'Ya existe una habitación con ese número'}), 400
        
        habitacion.numero = data['numero']
        habitacion.estado = data['estado']
        habitacion.nombre = data['nombre']
        habitacion.descripcion = data.get('descripcion')
        habitacion.capacidad = data['capacidad']
        habitacion.precio_noche = data['precio_noche']
        habitacion.tamano_m2 = data.get('tamano_m2')
        habitacion.camas = data.get('camas')
        habitacion.servicios = data.get('servicios', [])
        
        db.session.commit()
        
        return jsonify({'message': 'Habitación actualizada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# API para eliminar una habitación
@admin.route('/api/habitaciones/<int:id>', methods=['DELETE'])
def eliminar_habitacion(id):
    error = verificar_admin()
    if error:
        return error
    
    try:
        habitacion = Habitacion.query.get_or_404(id)
        
        # Aquí podrías agregar validaciones adicionales
        # Por ejemplo, verificar si la habitación tiene reservas activas
        
        db.session.delete(habitacion)
        db.session.commit()
        
        return jsonify({'message': 'Habitación eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500