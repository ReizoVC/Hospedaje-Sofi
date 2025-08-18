from utils.db import db
from datetime import datetime


class CheckInOut(db.Model):
    __tablename__ = 'checkinout'

    idcheck = db.Column(db.Integer, primary_key=True)
    idreserva = db.Column(db.Integer, db.ForeignKey('reserva.idreserva'), nullable=False)
    checkin = db.Column(db.DateTime, nullable=True)
    checkout = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'idcheck': self.idcheck,
            'idreserva': self.idreserva,
            'checkin': self.checkin.isoformat() if self.checkin else None,
            'checkout': self.checkout.isoformat() if self.checkout else None,
        }
