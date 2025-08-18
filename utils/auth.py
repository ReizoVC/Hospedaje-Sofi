from functools import wraps
from flask import session, request, redirect, url_for, jsonify, flash

# Definición de roles
ROL_DESACTIVADO = 0
ROL_CLIENTE = 1
ROL_RECEPCIONISTA = 2
ROL_ALMACENISTA = 3
ROL_ADMIN = 4


def _wants_json_response() -> bool:
    try:
        if request.path.startswith('/api'):
            return True
        accepts = request.accept_mimetypes
        return accepts['application/json'] >= accepts['text/html']
    except Exception:
        return False


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            if _wants_json_response():
                return jsonify({'error': 'No autenticado'}), 401
            flash('Debes iniciar sesión para acceder.', 'error')
            return redirect(url_for('inicio.index'))
        return view(*args, **kwargs)
    return wrapped


def role_required(min_role: int):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                if _wants_json_response():
                    return jsonify({'error': 'No autenticado'}), 401
                flash('Debes iniciar sesión para acceder.', 'error')
                return redirect(url_for('inicio.index'))
            rol = session.get('user_rol', ROL_CLIENTE)
            if rol < min_role:
                if _wants_json_response():
                    return jsonify({'error': 'No autorizado'}), 403
                flash('No tienes permisos para acceder a esta sección.', 'error')
                return redirect(url_for('inicio.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator
