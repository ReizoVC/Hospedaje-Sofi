from utils.db import db
from datetime import datetime
import string
import random
from sqlalchemy.dialects.postgresql import UUID

class Reserva(db.Model):
    __tablename__ = 'reserva'
    
    idreserva = db.Column(db.Integer, primary_key=True)
    idusuario = db.Column(UUID(as_uuid=True), db.ForeignKey('usuarios.idusuario'), nullable=False)
    idhabitacion = db.Column(db.Integer, db.ForeignKey('habitaciones.idhabitacion'), nullable=False)
    fechainicio = db.Column(db.Date, nullable=False)
    fechafin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    # Estados posibles:
    # - 'pendiente': Reserva creada, esperando confirmación
    # - 'confirmada': Reserva confirmada, esperando check-in
    # - 'activa': Check-in realizado, huésped en la habitación
    # - 'completada': Check-out realizado, reserva finalizada
    # - 'cancelada': Reserva cancelada
    codigoreserva = db.Column(db.String(20), nullable=False, unique=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='reservas')
    habitacion = db.relationship('Habitacion', backref='reservas')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.codigoreserva:
            self.codigoreserva = self.generar_codigo_reserva()
    
    def generar_codigo_reserva(self):
        """Genera un código único de reserva"""
        letras = string.ascii_uppercase
        numeros = string.digits
        codigo = ''.join(random.choices(letras, k=3)) + ''.join(random.choices(numeros, k=4))
        
        # Verificar que el código no exista
        while Reserva.query.filter_by(codigoreserva=codigo).first():
            codigo = ''.join(random.choices(letras, k=3)) + ''.join(random.choices(numeros, k=4))
        
        return codigo
    
    def to_dict(self):
        return {
            'idreserva': self.idreserva,
            'idusuario': str(self.idusuario) if self.idusuario else None,
            'idhabitacion': self.idhabitacion,
            'fechainicio': self.fechainicio.isoformat() if self.fechainicio else None,
            'fechafin': self.fechafin.isoformat() if self.fechafin else None,
            'estado': self.estado,
            'codigoreserva': self.codigoreserva,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }