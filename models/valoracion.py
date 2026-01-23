import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from utils.db import db


class Valoracion(db.Model):
    __tablename__ = 'valoraciones'

    idvaloracion = db.Column(db.Integer, primary_key=True)

    idhabitacion = db.Column(
        db.Integer,
        db.ForeignKey('habitaciones.idhabitacion', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    idusuario = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('usuarios.idusuario', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    puntuacion = db.Column(db.Integer, nullable=False)  # 1..5
    comentario = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    usuario = db.relationship('Usuario', backref='valoraciones')
    habitacion = db.relationship('Habitacion', backref='valoraciones')

    __table_args__ = (
        CheckConstraint('puntuacion >= 1 AND puntuacion <= 5', name='ck_valoraciones_puntuacion_1_5'),
        UniqueConstraint('idhabitacion', 'idusuario', name='uq_valoraciones_habitacion_usuario'),
    )

    def to_dict(self):
        return {
            'idvaloracion': self.idvaloracion,
            'idhabitacion': self.idhabitacion,
            'idusuario': str(self.idusuario) if self.idusuario else None,
            'puntuacion': self.puntuacion,
            'comentario': self.comentario or '',
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'usuario': {
                'idusuario': str(self.usuario.idusuario),
                'nombre': self.usuario.nombre,
                'apellidos': self.usuario.apellidos,
            } if getattr(self, 'usuario', None) else None,
        }
