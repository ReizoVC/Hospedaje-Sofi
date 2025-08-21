from utils.db import db
from datetime import date


class Producto(db.Model):
	__tablename__ = 'productos'

	idproducto = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(255), nullable=False, unique=True)
	cantidad = db.Column(db.Integer, nullable=False, default=0)
	umbralminimo = db.Column(db.Integer, nullable=False, default=0)
	# Costo unitario del producto (entero)
	costo = db.Column(db.Integer, nullable=False, default=0)
	# Campo propuesto para caducidad (puede ser NULL si no aplica)
	fecha_vencimiento = db.Column(db.Date, nullable=True)

	def __repr__(self) -> str:
		return f"<Producto {self.idproducto} - {self.nombre}>"

	# Propiedades derivadas útiles para UI/API
	@property
	def agotado(self) -> bool:
		try:
			return int(self.cantidad or 0) <= 0
		except Exception:
			return False

	@property
	def bajo_stock(self) -> bool:
		try:
			return int(self.cantidad or 0) <= int(self.umbralminimo or 0)
		except Exception:
			return False

	@property
	def dias_para_vencer(self):
		if not self.fecha_vencimiento:
			return None
		try:
			return (self.fecha_vencimiento - date.today()).days
		except Exception:
			return None

	def to_dict(self):
		return {
			'idproducto': self.idproducto,
			'nombre': self.nombre,
			'cantidad': int(self.cantidad or 0),
			'umbralminimo': int(self.umbralminimo or 0),
			'costo': int(self.costo or 0),
			'costo_total': int(self.costo or 0) * int(self.cantidad or 0),
			'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
			'agotado': self.agotado,
			'bajo_stock': self.bajo_stock,
			'dias_para_vencer': self.dias_para_vencer,
		}

