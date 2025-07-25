from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import db
from models.usuario import Usuario

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login_page():
    return render_template('auth/login.html')

@auth.route('/register')
def register_page():
    return render_template('auth/register.html')

@auth.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(correo=data['email']).first():
            return jsonify({'error': 'El correo ya está registrado'}), 400
        
        if Usuario.query.filter_by(dni=data['dni']).first():
            return jsonify({'error': 'El DNI ya está registrado'}), 400
        
        # Crear nuevo usuario
        hashed_password = generate_password_hash(data['password'])
        
        nuevo_usuario = Usuario(
            nombre=data['name'],
            apellidos=data['lastName'],
            dni=data['dni'],
            correo=data['email'],
            telefono=data['phone'],
            clave=hashed_password,
            rol=1  # Usuario normal
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return jsonify({'message': 'Usuario registrado exitosamente'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        usuario = Usuario.query.filter_by(correo=data['email']).first()
        
        if usuario and check_password_hash(usuario.clave, data['password']):
            # Guardar información en la sesión
            session['user_id'] = str(usuario.idusuario)
            session['user_email'] = usuario.correo
            session['user_name'] = usuario.nombre
            session['user_rol'] = usuario.rol
            
            return jsonify({
                'message': 'Sesión iniciada exitosamente',
                'user': {
                    'id': str(usuario.idusuario),
                    'email': usuario.correo,
                    'name': usuario.nombre,
                    'rol': usuario.rol
                }
            }), 200
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200

@auth.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'email': session['user_email'],
                'name': session['user_name'],
                'rol': session['user_rol']
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200