from flask import Blueprint, request, jsonify, session, render_template, flash, redirect, url_for
from utils.auth import redirect_staff_to_dashboard
from models.usuario import Usuario
from utils.db import db
import uuid
import hashlib

auth = Blueprint('auth', __name__)

@auth.route('/login')   
def login_page():
    # Login SOLO para usuarios web (clientes)
    resp = redirect_staff_to_dashboard()
    if resp is not None:
        return resp
    return render_template(
        'auth/login.html',
        is_staff_login=False,
        login_endpoint=url_for('auth.login'),
    )

@auth.route('/login/trabajadores')
def login_trabajadores_page():
    # Login SOLO para trabajadores (personal)
    return render_template(
        'auth/staff_login.html',
        login_endpoint=url_for('auth.staff_login_api'),
    )

@auth.route('/register')
def register_page():
    resp = redirect_staff_to_dashboard()
    if resp is not None:
        return resp
    return render_template('auth/register.html')

@auth.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        required_fields = ['name', 'lastName', 'dni', 'email', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        existing_user = Usuario.query.filter(
            (Usuario.correo == data['email'].lower()) |
            (Usuario.dni == data['dni'])
        ).first()
        if existing_user:
            return jsonify({'error': 'El usuario ya existe con ese email o DNI'}), 400
        hashed_password = hashlib.md5(data['password'].encode()).hexdigest()
        new_user = Usuario(
            nombre=data['name'],
            apellidos=data['lastName'],
            dni=data['dni'],
            correo=data['email'].lower(),
            telefono=data['phone'],
            clave=hashed_password,
            rol=1 
        )
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = str(new_user.idusuario)
        session['user_email'] = new_user.correo
        session['user_name'] = f"{new_user.nombre} {new_user.apellidos}"
        session['user_rol'] = new_user.rol
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'authenticated': True,
            'user': {
                'id': str(new_user.idusuario),
                'nombre': new_user.nombre,
                'apellidos': new_user.apellidos,
                'email': new_user.correo,
                'rol': new_user.rol
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@auth.route('/api/login', methods=['POST'])
def login():
    """Login SOLO para usuarios web (rol=1)."""
    try:
        data = request.get_json() or {}
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400

        user = Usuario.query.filter_by(correo=(data.get('email') or '').lower()).first()
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        provided = data.get('password') or ''
        ok = (user.clave == hashlib.md5(provided.encode()).hexdigest())
        if not ok:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        if user.rol == 0:
            return jsonify({'error': 'Esta cuenta ha sido desactivada. Contacte al administrador.'}), 403

        if user.rol != 1:
            return jsonify({'error': 'Este acceso es solo para clientes. Usa /login/trabajadores.'}), 403

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

@auth.route('/api/staff/login', methods=['POST'])
def staff_login_api():
    """Login SOLO para trabajadores (roles 2/3/4)."""
    try:
        data = request.get_json() or {}
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400

        user = Usuario.query.filter_by(correo=(data.get('email') or '').lower()).first()
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        provided = data.get('password') or ''
        ok = (user.clave == hashlib.md5(provided.encode()).hexdigest())
        if not ok:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        if user.rol == 0:
            return jsonify({'error': 'Esta cuenta ha sido desactivada. Contacte al administrador.'}), 403

        if user.rol not in (2, 3, 4):
            return jsonify({'error': 'Este acceso es solo para trabajadores. Usa /login.'}), 403

        session['user_id'] = str(user.idusuario)
        session['user_email'] = user.correo
        session['user_name'] = f"{user.nombre} {user.apellidos}"
        session['user_rol'] = user.rol

        return jsonify({
            'message': 'Sesión de trabajador iniciada exitosamente',
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
