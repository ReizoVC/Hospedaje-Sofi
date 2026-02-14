from utils.db import db
from datetime import datetime


class Lote(db.Model):
    __tablename__ = 'lotes'

    idlote = db.Column(db.Integer, primary_key=True)
    idproducto = db.Column(db.Integer, db.ForeignKey('productos.idproducto'), nullable=False, index=True)
    cantidad_actual = db.Column(db.Integer, nullable=False, default=0)
    cantidad_inicial = db.Column(db.Integer, nullable=False, default=0)
    fecha_vencimiento = db.Column(db.Date, nullable=True, index=True)
    costo_unitario = db.Column(db.Integer, nullable=False, default=0)
    fecha_ingreso = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    producto = db.relationship('Producto', backref='lotes')

    def __repr__(self) -> str:
        return (
            f"<Lote {self.idlote} prod={self.idproducto} cant={self.cantidad_actual}/"
            f"{self.cantidad_inicial} costo={self.costo_unitario}>"
        )

    def to_dict(self):
        return {
            'idlote': self.idlote,
            'idproducto': self.idproducto,
            'cantidad_actual': int(self.cantidad_actual or 0),
            'cantidad_inicial': int(self.cantidad_inicial or 0),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'costo_unitario': int(self.costo_unitario or 0),
            'fecha_ingreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
        }
