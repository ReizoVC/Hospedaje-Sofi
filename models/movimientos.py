from utils.db import db
from sqlalchemy import event, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class Movimientos(db.Model):
    __tablename__ = 'movimientos'

    idmovimiento = db.Column(db.Integer, primary_key=True)
    idproducto = db.Column(db.Integer, db.ForeignKey('productos.idproducto'), nullable=True)
    idlote = db.Column(db.Integer, db.ForeignKey('lotes.idlote'), nullable=True)
    idusuario = db.Column(UUID(as_uuid=True), db.ForeignKey('usuarios.idusuario'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    costototal = db.Column(db.Integer, nullable=False, default=0)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    producto = db.relationship('Producto', backref='movimientos')
    lote = db.relationship('Lote', backref='movimientos')

    def __repr__(self) -> str:
        return (
            f"<MovInv {self.idmovimiento} prod={self.idproducto} tipo={self.tipo} "
            f"cant={self.cantidad} costototal={self.costototal}>"
        )

    def to_dict(self):
        return {
            'idmovimiento': self.idmovimiento,
            'idproducto': self.idproducto,
            'idlote': self.idlote,
            'idusuario': str(self.idusuario) if self.idusuario else None,
            'tipo': self.tipo,
            'cantidad': int(self.cantidad or 0),
            'costototal': int(self.costototal or 0),
            'fecha': self.fecha.isoformat() if self.fecha else None,
        }


@event.listens_for(Movimientos, 'before_insert')
def _mov_before_insert(mapper, connection, target: Movimientos):
    try:
        if (target.tipo or '').lower() == 'servicios':
            if not target.cantidad or int(target.cantidad) <= 0:
                target.cantidad = 1
            if target.costototal is None:
                target.costototal = 0
            return
        if target.costototal not in (None, 0):
            return
        cantidad = int(target.cantidad or 0)
        costo_unit = 0
        try:
            if target.idlote is not None:
                res = connection.execute(
                    text('SELECT costo_unitario FROM lotes WHERE idlote = :id'),
                    {'id': target.idlote}
                )
                row = res.first()
                if row:
                    costo_unit = int(row[0] or 0)
        except Exception:
            costo_unit = 0
        target.costototal = cantidad * costo_unit
    except Exception:
        if target.costototal is None:
            target.costototal = 0


@event.listens_for(Movimientos, 'before_update')
def _mov_before_update(mapper, connection, target: Movimientos):
    try:
        if (target.tipo or '').lower() == 'servicios':
            if not target.cantidad or int(target.cantidad) <= 0:
                target.cantidad = 1
            if target.costototal is None:
                target.costototal = 0
            return
        if target.costototal not in (None, 0):
            return
        cantidad = int(target.cantidad or 0)
        costo_unit = 0
        try:
            if target.idlote is not None:
                res = connection.execute(
                    text('SELECT costo_unitario FROM lotes WHERE idlote = :id'),
                    {'id': target.idlote}
                )
                row = res.first()
                if row:
                    costo_unit = int(row[0] or 0)
        except Exception:
            costo_unit = 0
        target.costototal = cantidad * costo_unit
    except Exception:
        if target.costototal is None:
            target.costototal = 0

MovimientoInventario = Movimientos
Movimiento = Movimientos
