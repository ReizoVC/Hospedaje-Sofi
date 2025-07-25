from utils.db import db
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

class Habitacion(db.Model):
    __tablename__ = 'habitaciones'

    idhabitacion = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False, unique=True)
    estado = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    capacidad = db.Column(db.Integer)
    precio_noche = db.Column(db.Numeric(10, 2))
    tamano_m2 = db.Column(db.Integer)
    camas = db.Column(db.String(100))
    servicios = db.Column(ARRAY(db.Text))

    # Relación con imágenes
    imagenes = relationship("ImagenHabitacion", back_populates="habitacion", cascade="all, delete-orphan", order_by="ImagenHabitacion.orden")

    def __repr__(self):
        return f"<Habitacion {self.numero} - {self.nombre}>"
    
    def to_dict(self):
        return {
            'idhabitacion': self.idhabitacion,
            'numero': self.numero,
            'estado': self.estado,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'capacidad': self.capacidad,
            'precio_noche': float(self.precio_noche) if self.precio_noche else 0.0,
            'tamano_m2': self.tamano_m2,
            'camas': self.camas,
            'servicios': self.servicios or []
        }
