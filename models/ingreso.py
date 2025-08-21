from utils.db import db
from datetime import datetime


class Ingreso(db.Model):
    __tablename__ = 'ingresos'

    idingreso = db.Column(db.Integer, primary_key=True)
    idreserva = db.Column(db.Integer, db.ForeignKey('reserva.idreserva'), nullable=False, index=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    # Algunas instalaciones ya tienen 'concepto' NOT NULL; mantener compatibilidad
    concepto = db.Column(db.String(100), nullable=False, default='reserva')
    descripcion = db.Column(db.String(255), nullable=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relación (opcional) hacia Reserva
    reserva = db.relationship('Reserva', backref='ingresos')

    def __repr__(self) -> str:
        return f"<Ingreso {self.idingreso} reserva={self.idreserva} monto={self.monto}>"

    def to_dict(self):
        return {
            'idingreso': self.idingreso,
            'idreserva': self.idreserva,
            'monto': float(self.monto or 0),
            'concepto': self.concepto,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat() if self.fecha else None,
        }


def registrar_ingreso_por_confirmacion(reserva, habitacion=None, descripcion: str | None = None, concepto: str | None = None):
    """
    Crea (si no existe) un Ingreso para una reserva confirmada.
    - Calcula monto = noches * precio_noche.
    - Evita duplicados por idreserva.
    """
    # Verificar si ya existe un ingreso para esta reserva
    from sqlalchemy import exists
    ya_existe = db.session.query(exists().where(Ingreso.idreserva == reserva.idreserva)).scalar()
    if ya_existe:
        return None

    if habitacion is None:
        # Cargar habitación si no fue proporcionada
        from models.habitaciones import Habitacion
        habitacion = Habitacion.query.get(reserva.idhabitacion)

    noches = max(0, (reserva.fechafin - reserva.fechainicio).days) if reserva.fechainicio and reserva.fechafin else 0
    precio_noche = float(habitacion.precio_noche) if habitacion and habitacion.precio_noche is not None else 0.0
    monto = round(noches * precio_noche, 2)

    if descripcion is None:
        desc_hab = (habitacion.nombre if habitacion else '') or ''
        descripcion = f"Reserva confirmada - {desc_hab} ({noches} noches)"
    if concepto is None:
        # Usar el estado como concepto si es válido; fallback a 'reserva'
        concepto = (reserva.estado or 'reserva') if hasattr(reserva, 'estado') else 'reserva'

    ingreso = Ingreso(
        idreserva=reserva.idreserva,
        monto=monto,
        concepto=str(concepto)[:100] if concepto else 'reserva',
        descripcion=descripcion,
    )
    db.session.add(ingreso)
    return ingreso
