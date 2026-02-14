from utils.db import db
from datetime import date
from sqlalchemy import func, case, or_, and_


class Producto(db.Model):
	__tablename__ = 'productos'

	idproducto = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(255), nullable=False, unique=True)
	umbralminimo = db.Column(db.Integer, nullable=False, default=0)

	def _get_stock_snapshot(self):
		from models.lote import Lote
		hoy = date.today()
		vigente = or_(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento >= hoy)
		row = (
			db.session.query(
				func.coalesce(func.sum(case((vigente, Lote.cantidad_actual), else_=0)), 0),
				func.coalesce(func.sum(case((vigente, Lote.cantidad_actual * Lote.costo_unitario), else_=0)), 0),
				func.min(case((and_(vigente, Lote.cantidad_actual > 0), Lote.fecha_vencimiento))),
			)
			.filter(Lote.idproducto == self.idproducto)
			.one()
		)
		stock_total = int(row[0] or 0)
		costo_total = int(row[1] or 0)
		fv = row[2]
		return stock_total, costo_total, fv

	def __repr__(self) -> str:
		return f"<Producto {self.idproducto} - {self.nombre}>"

	# Propiedades derivadas útiles para UI/API
	@property
	def agotado(self) -> bool:
		try:
			stock_total, _, _ = self._get_stock_snapshot()
			return stock_total <= 0
		except Exception:
			return False

	@property
	def bajo_stock(self) -> bool:
		try:
			stock_total, _, _ = self._get_stock_snapshot()
			return stock_total <= int(self.umbralminimo or 0)
		except Exception:
			return False

	@property
	def dias_para_vencer(self):
		try:
			_, _, fv = self._get_stock_snapshot()
			if not fv:
				return None
			return (fv - date.today()).days
		except Exception:
			return None

	def to_dict(self):
		stock_total, costo_total, fv = self._get_stock_snapshot()
		costo_unit = int(round(costo_total / stock_total)) if stock_total > 0 else 0
		dias = None
		if fv:
			try:
				dias = (fv - date.today()).days
			except Exception:
				dias = None
		return {
			'idproducto': self.idproducto,
			'nombre': self.nombre,
			'cantidad': int(stock_total or 0),
			'umbralminimo': int(self.umbralminimo or 0),
			'costo': int(costo_unit or 0),
			'costo_total': int(costo_total or 0),
			'fecha_vencimiento': fv.isoformat() if fv else None,
			'agotado': stock_total <= 0,
			'bajo_stock': stock_total <= int(self.umbralminimo or 0),
			'dias_para_vencer': dias,
		}

