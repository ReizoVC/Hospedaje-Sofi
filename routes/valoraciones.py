import uuid

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from utils.db import db
from models.habitaciones import Habitacion
from models.valoracion import Valoracion


valoraciones = Blueprint('valoraciones', __name__)


def _require_login():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    return None


@valoraciones.route('/api/habitaciones/<int:idhabitacion>/valoraciones', methods=['GET'])
def listar_valoraciones(idhabitacion):
    Habitacion.query.get_or_404(idhabitacion)

    items = (
        Valoracion.query
        .options(joinedload(Valoracion.usuario))
        .filter_by(idhabitacion=idhabitacion)
        .order_by(Valoracion.fecha_creacion.desc())
        .all()
    )

    promedio = (
        db.session.query(func.avg(Valoracion.puntuacion))
        .filter(Valoracion.idhabitacion == idhabitacion)
        .scalar()
    ) or 0

    return jsonify({
        'promedio': float(promedio),
        'total': len(items),
        'valoraciones': [v.to_dict() for v in items],
    })


@valoraciones.route('/api/habitaciones/<int:idhabitacion>/valoraciones', methods=['POST'])
def crear_o_actualizar_valoracion(idhabitacion):
    error = _require_login()
    if error:
        return error

    Habitacion.query.get_or_404(idhabitacion)

    data = request.get_json(silent=True) or {}

    try:
        puntuacion = int(data.get('puntuacion', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Puntuación inválida'}), 400

    comentario = (data.get('comentario') or '').strip()

    if puntuacion < 1 or puntuacion > 5:
        return jsonify({'error': 'La puntuación debe estar entre 1 y 5'}), 400

    try:
        user_uuid = uuid.UUID(str(session['user_id']))
    except Exception:
        return jsonify({'error': 'Sesión inválida (user_id)'}), 400

    try:
        existente = Valoracion.query.filter_by(idhabitacion=idhabitacion, idusuario=user_uuid).first()

        if existente:
            existente.puntuacion = puntuacion
            existente.comentario = comentario
            db.session.commit()
            return jsonify({'message': 'Valoración actualizada', 'valoracion': existente.to_dict()}), 200

        nueva = Valoracion(
            idhabitacion=idhabitacion,
            idusuario=user_uuid,
            puntuacion=puntuacion,
            comentario=comentario,
        )
        db.session.add(nueva)
        db.session.commit()
        return jsonify({'message': 'Valoración creada', 'valoracion': nueva.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar valoración: {str(e)}'}), 500
