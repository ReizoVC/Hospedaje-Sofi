from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from utils.db import db
from models.usuario import Usuario
from models.reserva import Reserva
import uuid
import hashlib

user = Blueprint('user', __name__, url_prefix='/user')

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('inicio.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@user.route('/profile')
@login_required
def profile():
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('auth.login_page'))
        return render_template('user/profile.html', user=usuario)
    except Exception:
        flash('Error al cargar el perfil', 'error')
        return redirect(url_for('inicio.index'))

@user.route('/reservations')
@login_required
def reservations():
    """Página de reservas del usuario"""
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('auth.login_page'))

        reservas = (
            Reserva.query
            .filter_by(idusuario=usuario.idusuario)
            .order_by(Reserva.fechainicio.desc())
            .all()
        )

        estados_activas = {'pendiente', 'confirmada', 'activa'}
        reservas_activas = [r for r in reservas if r.estado in estados_activas]
        reservas_historial = [r for r in reservas if r.estado not in estados_activas]

        return render_template(
            'user/reservations.html',
            user=usuario,
            reservas_activas=reservas_activas,
            reservas_historial=reservas_historial,
        )
    except Exception:
        flash('Error al cargar las reservas', 'error')
        return redirect(url_for('inicio.index'))

@user.route('/settings')
@login_required
def settings():
    """Página de configuración del usuario"""
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('auth.login_page'))
        return render_template('user/settings.html', user=usuario)
    except Exception:
        flash('Error al cargar la configuración', 'error')
        return redirect(url_for('inicio.index'))

@user.route('/history')
@login_required
def history():
    """Página de historial de estadías del usuario"""
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('auth.login_page'))
        return render_template('user/history.html', user=usuario)
    except Exception:
        flash('Error al cargar el historial', 'error')
        return redirect(url_for('inicio.index'))

@user.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    """Editar perfil del usuario"""
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        usuario.nombre = request.form.get('nombre', usuario.nombre)
        usuario.apellidos = request.form.get('apellidos', usuario.apellidos)
        usuario.telefono = request.form.get('telefono', usuario.telefono)

        db.session.commit()

        session['user_name'] = f"{usuario.nombre} {usuario.apellidos}"

        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('user.profile'))
    except Exception:
        db.session.rollback()
        flash('Error al actualizar el perfil', 'error')
        return redirect(url_for('user.profile'))

@user.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    try:
        sid = session['user_id']
        uid = uuid.UUID(sid) if isinstance(sid, str) else sid
        usuario = Usuario.query.get(uid)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # hash MD5 
        if usuario.clave != hashlib.md5((current_password or '').encode()).hexdigest():
            flash('Contraseña actual incorrecta', 'error')
            return redirect(url_for('user.settings'))

        if new_password != confirm_password:
            flash('Las contraseñas nuevas no coinciden', 'error')
            return redirect(url_for('user.settings'))

        usuario.clave = hashlib.md5((new_password or '').encode()).hexdigest()
        db.session.commit()

        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('user.settings'))
    except Exception:
        db.session.rollback()
        flash('Error al cambiar la contraseña', 'error')
        return redirect(url_for('user.settings'))