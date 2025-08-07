from flask import Blueprint, request, jsonify, session, render_template, flash, redirect, url_for
from werkzeug.security import check_password_hash
from models.usuario import Usuario, db
import uuid
import hashlib

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
        
        # Validar datos requeridos
        required_fields = ['name', 'lastName', 'dni', 'email', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        # Verificar si el usuario ya existe
        existing_user = Usuario.query.filter(
            (Usuario.correo == data['email']) | 
            (Usuario.dni == data['dni'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'El usuario ya existe con ese email o DNI'}), 400
        
        # Crear nuevo usuario con hash MD5 (32 caracteres)
        hashed_password = hashlib.md5(data['password'].encode()).hexdigest()
        new_user = Usuario(
            nombre=data['name'],
            apellidos=data['lastName'],
            dni=data['dni'],
            correo=data['email'],
            telefono=data['phone'],
            clave=hashed_password,
            rol=0
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': str(new_user.idusuario),
                'nombre': new_user.nombre,
                'apellidos': new_user.apellidos,
                'email': new_user.correo
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@auth.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        # Buscar usuario por email
        user = Usuario.query.filter_by(correo=data['email']).first()
        
        # Verificar contraseña con hash MD5
        input_password_hash = hashlib.md5(data['password'].encode()).hexdigest()
        
        if not user or user.clave != input_password_hash:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Crear sesión
        session['user_id'] = str(user.idusuario)
        session['user_email'] = user.correo
        session['user_name'] = f"{user.nombre} {user.apellidos}"
        session['user_rol'] = user.rol
        
        return jsonify({
            'message': 'Sesión iniciada exitosamente',
            'user': {
                'id': str(user.idusuario),
                'nombre': user.nombre,
                'apellidos': user.apellidos,
                'email': user.correo,
                'telefono': user.telefono,
                'rol': user.rol
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@auth.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Sesión cerrada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@auth.route('/logout', methods=['GET', 'POST'])
def logout_user():
    """Cerrar sesión del usuario"""
    session.clear()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('inicio.index'))

@auth.route('/api/check-auth', methods=['GET'])
def check_auth():
    try:
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
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

# VERSIÓN TEMPORAL SIN HASH (NO USAR EN PRODUCCIÓN)
# Solo descomenta esto si necesitas una solución rápida para desarrollo

# @auth.route('/api/register-temp', methods=['POST'])
# def register_temp():
#     try:
#         data = request.get_json()
#         
#         # Validar datos requeridos
#         required_fields = ['name', 'lastName', 'dni', 'email', 'phone', 'password']
#         for field in required_fields:
#             if not data.get(field):
#                 return jsonify({'error': f'El campo {field} es requerido'}), 400
#         
#         # Verificar si el usuario ya existe
#         existing_user = Usuario.query.filter(
#             (Usuario.correo == data['email']) | 
#             (Usuario.dni == data['dni'])
#         ).first()
#         
#         if existing_user:
#             return jsonify({'error': 'El usuario ya existe con ese email o DNI'}), 400
#         
#         # Crear nuevo usuario SIN HASH (TEMPORAL)
#         new_user = Usuario(
#             nombre=data['name'],
#             apellidos=data['lastName'],
#             dni=data['dni'],
#             correo=data['email'],
#             telefono=data['phone'],
#             clave=data['password'],  # SIN HASH
#             rol=0
#         )
#         
#         db.session.add(new_user)
#         db.session.commit()
#         
#         return jsonify({
#             'message': 'Usuario registrado exitosamente',
#             'user': {
#                 'id': str(new_user.idusuario),
#                 'nombre': new_user.nombre,
#                 'apellidos': new_user.apellidos,
#                 'email': new_user.correo
#             }
#         }), 201
#         
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500