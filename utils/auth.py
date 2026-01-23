from functools import wraps
from flask import session, request, redirect, url_for, jsonify, flash

# Definición de roles
ROL_DESACTIVADO = 0
ROL_CLIENTE = 1
ROL_RECEPCIONISTA = 2
ROL_ALMACENISTA = 3
ROL_ADMIN = 4


def staff_dashboard_endpoint(rol: int | None) -> str:
    """Retorna el endpoint del dashboard para trabajadores según su rol."""
    if rol == ROL_RECEPCIONISTA:
        return 'recepcionista.estado_habitaciones'
    if rol == ROL_ALMACENISTA:
        return 'almacenista.inventario'
    if rol is not None and rol >= ROL_ADMIN:
        return 'admin.gestion'
    return 'trabajadores.inicio_trabajadores'


def redirect_staff_to_dashboard():
    """Redirige al dashboard correspondiente si la sesión es de trabajador."""
    rol = session.get('user_rol')
    if rol in (ROL_RECEPCIONISTA, ROL_ALMACENISTA, ROL_ADMIN):
        try:
            return redirect(url_for(staff_dashboard_endpoint(rol)))
        except Exception:
            return redirect('/trabajadores')
    return None


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
