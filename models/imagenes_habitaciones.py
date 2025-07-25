from utils.db import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class ImagenHabitacion(db.Model):
    __tablename__ = 'imagenes_habitaciones'

    idimagen = db.Column(db.Integer, primary_key=True)
    idhabitacion = db.Column(db.Integer, ForeignKey('habitaciones.idhabitacion'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)

    # Relación con la tabla habitaciones
    habitacion = relationship("Habitacion", back_populates="imagenes")

    def __repr__(self):
        return f"<ImagenHabitacion {self.idimagen} - Habitación {self.idhabitacion}>"
    
    def to_dict(self):
        return {
            'idimagen': self.idimagen,
            'idhabitacion': self.idhabitacion,
            'url': self.url,
            'orden': self.orden
        }