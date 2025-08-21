from utils.db import db
from datetime import date


class Egreso(db.Model):
    __tablename__ = 'egresos'

    idegreso = db.Column(db.Integer, primary_key=True)
    idmovimiento = db.Column(
        db.Integer,
        db.ForeignKey('movimientos.idmovimiento'),
        nullable=False,
        index=True,
    )
    descripcion = db.Column(db.String(255), nullable=True)
    # La BD tiene float4; aquí usamos Float. Si migras a dinero exacto, cambia a Numeric(12, 2).
    monto = db.Column(db.Float, nullable=False, default=0.0)
    fechaegreso = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # Relación hacia movimiento (permite movimiento.egresos)
    movimiento = db.relationship('Movimientos', backref='egresos')

    def __repr__(self) -> str:
        return f"<Egreso {self.idegreso} mov={self.idmovimiento} monto={self.monto}>"

    def to_dict(self):
        return {
            'idegreso': self.idegreso,
            'idmovimiento': self.idmovimiento,
            'descripcion': self.descripcion,
            'monto': float(self.monto or 0.0),
            'fechaegreso': self.fechaegreso.isoformat() if self.fechaegreso else None,
        }
