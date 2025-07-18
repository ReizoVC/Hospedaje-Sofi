from utils.db import db

class Habitacion(db.Model):
    __tablename__ = 'habitaciones'

    idhabitacion = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    capacidad = db.Column(db.Integer)
    precio_noche = db.Column(db.Numeric(7, 2))
    tamano_m2 = db.Column(db.Integer)
    camas = db.Column(db.String(100))
    servicios = db.Column(db.ARRAY(db.Text))

    def __repr__(self):
        return f"<Habitacion {self.numero} - {self.nombre}>"
