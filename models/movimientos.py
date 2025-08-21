from utils.db import db
from sqlalchemy import event, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class Movimientos(db.Model):
    __tablename__ = 'movimientos'

    idmovimiento = db.Column(db.Integer, primary_key=True)
    # Ahora opcional: puede ser NULL cuando el tipo sea 'servicios'
    idproducto = db.Column(db.Integer, db.ForeignKey('productos.idproducto'), nullable=True)
    idusuario = db.Column(UUID(as_uuid=True), db.ForeignKey('usuarios.idusuario'), nullable=False)
    # Tipos permitidos: 'entrada', 'salida', 'ajuste', 'servicios'
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    # Costo total del movimiento (entero). Ej: cantidad * costo unitario del producto.
    costototal = db.Column(db.Integer, nullable=False, default=0)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones simples (opcionales para navegación)
    producto = db.relationship('Producto', backref='movimientos')

    def __repr__(self) -> str:
        return (
            f"<MovInv {self.idmovimiento} prod={self.idproducto} tipo={self.tipo} "
            f"cant={self.cantidad} costototal={self.costototal}>"
        )

    def to_dict(self):
        return {
            'idmovimiento': self.idmovimiento,
            'idproducto': self.idproducto,
            'idusuario': str(self.idusuario) if self.idusuario else None,
            'tipo': self.tipo,
            'cantidad': int(self.cantidad or 0),
            'costototal': int(self.costototal or 0),
            'fecha': self.fecha.isoformat() if self.fecha else None,
        }


# Listeners para calcular costototal automáticamente si no se proporciona
@event.listens_for(Movimientos, 'before_insert')
def _mov_before_insert(mapper, connection, target: Movimientos):
    try:
        # Si es servicio: forzar cantidad mínima 1, no calcular desde producto
        if (target.tipo or '').lower() == 'servicios':
            if not target.cantidad or int(target.cantidad) <= 0:
                target.cantidad = 1
            # Se espera que costototal sea provisto por quien crea el movimiento (admin)
            if target.costototal is None:
                target.costototal = 0
            return

        # Inventario: si ya viene costototal, respetar y no recalcular
        if target.costototal not in (None, 0):
            return
        cantidad = int(target.cantidad or 0)
        # Intentar tomar costo del producto asociado
        costo_unit = 0
        try:
            if getattr(target, 'producto', None) is not None and target.producto.costo is not None:
                costo_unit = int(target.producto.costo or 0)
            elif target.idproducto is not None:
                # Consultar directo para evitar dependencia de sesión
                res = connection.execute(
                    text('SELECT costo FROM productos WHERE idproducto = :id'),
                    {'id': target.idproducto}
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
        # Servicios: no recalcular costototal automáticamente
        if (target.tipo or '').lower() == 'servicios':
            if not target.cantidad or int(target.cantidad) <= 0:
                target.cantidad = 1
            if target.costototal is None:
                target.costototal = 0
            return

        # Solo recalcula si costototal viene vacío y hay cantidad
        if target.costototal not in (None, 0):
            return
        cantidad = int(target.cantidad or 0)
        costo_unit = 0
        try:
            if getattr(target, 'producto', None) is not None and target.producto.costo is not None:
                costo_unit = int(target.producto.costo or 0)
            elif target.idproducto is not None:
                res = connection.execute(
                    text('SELECT costo FROM productos WHERE idproducto = :id'),
                    {'id': target.idproducto}
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

# Alias de compatibilidad y naming conciso
MovimientoInventario = Movimientos
Movimiento = Movimientos
