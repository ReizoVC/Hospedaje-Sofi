import uuid
from utils.db import db
from sqlalchemy.dialects.postgresql import UUID

class Usuario(db.Model):
    __tablename__ = "usuarios"

    idusuario = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    nombre = db.Column(db.String(255), nullable=False)
    apellidos = db.Column(db.String(255), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    clave = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Integer, nullable=False, default=1)  # Rol 1 = Usuario normal, Rol 0 = Cuenta eliminada

    def __repr__(self) -> str:
        return f"<Usuario {self.idusuario} - {self.correo}>"

    def to_dict(self):
        return {
            'idusuario': str(self.idusuario),
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'dni': self.dni,
            'correo': self.correo,
            'telefono': self.telefono,
            'rol': self.rol
        }

