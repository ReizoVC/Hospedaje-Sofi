from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from utils.db import db
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
import os

admin = Blueprint('admin', __name__)

# Configuración para subida de archivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Middleware para verificar permisos de administrador
def verificar_admin():
    print(f"Verificando admin - user_id: {session.get('user_id')}, user_rol: {session.get('user_rol')}")
    if 'user_id' not in session:
        print("No hay user_id en session")
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 3:
        print(f"Rol insuficiente: {session.get('user_rol')} - Se requiere rol 3 o superior para administrador")
        return jsonify({'error': 'Acceso no autorizado - rol insuficiente'}), 403
    return None

# Middleware para verificar permisos de recepcionista o superior
def verificar_recepcionista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 1:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de recepcionista o superior'}), 403
    return None

# Middleware para verificar permisos de almacenista o superior
def verificar_almacenista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 2:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
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

# ============ RUTAS PARA GESTIÓN DE IMÁGENES ============

# API para obtener imágenes de una habitación
@admin.route('/api/imagenes-habitacion/<int:idhabitacion>', methods=['GET'])
def obtener_imagenes_habitacion(idhabitacion):
    error = verificar_admin()
    if error:
        return error
    
    try:
        imagenes = ImagenHabitacion.query.filter_by(idhabitacion=idhabitacion).order_by(ImagenHabitacion.orden).all()
        imagenes_list = [imagen.to_dict() for imagen in imagenes]
        return jsonify(imagenes_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API para subir una nueva imagen
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
        
        # Verificar que la habitación existe
        habitacion = Habitacion.query.get_or_404(idhabitacion)
        
        # Crear directorio si no existe
        upload_path = os.path.join('static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        # Generar nombre único para el archivo
        filename = secure_filename(file.filename)
        unique_filename = f"hab_{idhabitacion}_{len(os.listdir(upload_path))}_{filename}"
        file_path = os.path.join(upload_path, unique_filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Crear registro en la base de datos
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

# API para actualizar el orden de una imagen
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

# API para eliminar una imagen
@admin.route('/api/imagenes-habitacion/<int:idimagen>', methods=['DELETE'])
def eliminar_imagen(idimagen):
    error = verificar_admin()
    if error:
        return error
    
    try:
        imagen = ImagenHabitacion.query.get_or_404(idimagen)
        
        # Eliminar archivo físico
        file_path = os.path.join('static', 'uploads', imagen.url)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(imagen)
        db.session.commit()
        
        return jsonify({'message': 'Imagen eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500