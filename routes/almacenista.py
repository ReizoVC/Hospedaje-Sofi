from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.db import db
from models.producto import Producto
from models.movimientos import Movimientos
from models.lote import Lote
from models.egreso import Egreso
from datetime import datetime, date
from sqlalchemy import func, case, or_, and_
from sqlalchemy.sql import expression
import uuid

almacenista = Blueprint('almacenista', __name__)


def _producto_to_dict(producto: Producto, stock_total=None, costo_total=None, fv=None):
    if stock_total is None or costo_total is None:
        hoy = date.today()
        vigente = or_(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento >= hoy)
        row = (
            db.session.query(
                func.coalesce(func.sum(case((vigente, Lote.cantidad_actual), else_=0)), 0),
                func.coalesce(func.sum(case((vigente, Lote.cantidad_actual * Lote.costo_unitario), else_=0)), 0),
                func.min(case((and_(vigente, Lote.cantidad_actual > 0), Lote.fecha_vencimiento))),
            )
            .filter(Lote.idproducto == producto.idproducto)
            .one()
        )
        stock_total = int(row[0] or 0)
        costo_total = int(row[1] or 0)
        fv = row[2]
    else:
        stock_total = int(stock_total or 0)
        costo_total = int(costo_total or 0)

    costo_unit = int(round(costo_total / stock_total)) if stock_total > 0 else 0
    dias = None
    if fv:
        try:
            dias = (fv - date.today()).days
        except Exception:
            dias = None

    return {
        'idproducto': producto.idproducto,
        'nombre': producto.nombre,
        'cantidad': stock_total,
        'umbralminimo': int(producto.umbralminimo or 0),
        'costo': costo_unit,
        'costo_total': int(costo_total or 0),
        'fecha_vencimiento': fv.isoformat() if fv else None,
        'agotado': stock_total <= 0,
        'bajo_stock': stock_total <= int(producto.umbralminimo or 0),
        'dias_para_vencer': dias,
    }

def verificar_almacenista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 3:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
    return None

@almacenista.before_request
def _proteger_rutas_almacenista():
    is_api = '/api/' in (request.path or '')
    if 'user_id' not in session:
        if is_api:
            return jsonify({'error': 'No autenticado'}), 401
        return redirect(url_for('auth.login_page'))
    if session.get('user_rol', 0) < 3:
        if is_api:
            return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
        return redirect(url_for('auth.login_page'))

@almacenista.route('/inventario')
def inventario():
    error = verificar_almacenista()
    if error:
        return redirect(url_for('auth.login_page'))
    return render_template('almacenista/inventario.html')

@almacenista.route('/reportes-almacen')
def reportes_almacen():
    error = verificar_almacenista()
    if error:
        return redirect(url_for('auth.login_page'))
    return render_template('almacenista/reportes.html')

# Productos
@almacenista.route('/api/productos', methods=['GET'])
def listar_productos():
    error = verificar_almacenista()
    if error:
        return error
    try:
        nombre = request.args.get('q')
        bajos = request.args.get('bajos')
        por_vencer_dias = request.args.get('por_vencer_dias')

        hoy = date.today()
        vigente = or_(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento >= hoy)
        lotes_subq = (
            db.session.query(
                Lote.idproducto.label('idproducto'),
                func.coalesce(func.sum(case((vigente, Lote.cantidad_actual), else_=0)), 0).label('stock_total'),
                func.coalesce(func.sum(case((vigente, Lote.cantidad_actual * Lote.costo_unitario), else_=0)), 0).label('costo_total'),
                func.min(case((and_(vigente, Lote.cantidad_actual > 0), Lote.fecha_vencimiento))).label('fecha_vencimiento'),
            )
            .group_by(Lote.idproducto)
            .subquery()
        )

        q = db.session.query(
            Producto,
            lotes_subq.c.stock_total,
            lotes_subq.c.costo_total,
            lotes_subq.c.fecha_vencimiento,
        ).outerjoin(lotes_subq, Producto.idproducto == lotes_subq.c.idproducto)

        if nombre:
            q = q.filter(Producto.nombre.ilike(f"%{nombre}%"))

        productos = q.all()
        data = [
            _producto_to_dict(p, stock_total, costo_total, fv)
            for (p, stock_total, costo_total, fv) in productos
        ]
        if bajos == '1':
            data = [d for d in data if d['bajo_stock']]
        if por_vencer_dias and por_vencer_dias.isdigit():
            dias = int(por_vencer_dias)
            data = [d for d in data if d['dias_para_vencer'] is not None and d['dias_para_vencer'] <= dias]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Error al listar productos: {str(e)}'}), 500

@almacenista.route('/api/productos', methods=['POST'])
def crear_producto():
    error = verificar_almacenista()
    if error:
        return error
    try:
        data = request.get_json() or {}
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400
        if Producto.query.filter(Producto.nombre.ilike(nombre)).first():
            return jsonify({'error': 'Ya existe un producto con ese nombre'}), 400
        cantidad = int(data.get('cantidad') or 0)
        umbral = int(data.get('umbralminimo') or 0)
        costo = int(data.get('costo') or 0)
        if costo < 10:
            return jsonify({'error': 'El costo unitario no puede ser menor a 10'}), 400
        fv = data.get('fecha_vencimiento')
        fv_date = datetime.strptime(fv, '%Y-%m-%d').date() if fv else None
        p = Producto(nombre=nombre, umbralminimo=umbral)
        db.session.add(p)
        db.session.flush()
        if cantidad and cantidad > 0:
            lote = Lote(
                idproducto=p.idproducto,
                cantidad_actual=cantidad,
                cantidad_inicial=cantidad,
                fecha_vencimiento=fv_date,
                costo_unitario=costo,
            )
            db.session.add(lote)
            db.session.flush()
            sid = session.get('user_id')
            user_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid
            mov = Movimientos(
                idproducto=p.idproducto,
                idlote=lote.idlote,
                idusuario=user_uuid,
                tipo='entrada',
                cantidad=cantidad,
                costototal=int(cantidad) * int(costo or 0),
                fecha=datetime.utcnow(),
            )
            db.session.add(mov)
            db.session.flush()
            if (mov.costototal or 0) > 0:
                eg = Egreso(
                    idmovimiento=mov.idmovimiento,
                    descripcion=f"Entrada inicial de producto {p.nombre}",
                    monto=float(mov.costototal or 0),
                    fechaegreso=mov.fecha.date() if hasattr(mov.fecha, 'date') else date.today(),
                )
                db.session.add(eg)
        db.session.commit()
        return jsonify({'message': 'Producto creado', 'producto': _producto_to_dict(p)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear producto: {str(e)}'}), 500

@almacenista.route('/api/productos/<int:idproducto>', methods=['PUT'])
def actualizar_producto(idproducto):
    error = verificar_almacenista()
    if error:
        return error
    try:
        p = Producto.query.get_or_404(idproducto)
        data = request.get_json() or {}
        if 'nombre' in data and data['nombre']:
            nombre = data['nombre'].strip()
            if nombre != p.nombre and Producto.query.filter(Producto.nombre.ilike(nombre)).first():
                return jsonify({'error': 'Ya existe un producto con ese nombre'}), 400
            p.nombre = nombre
        if 'umbralminimo' in data:
            p.umbralminimo = int(data['umbralminimo'] or 0)
        if 'fecha_vencimiento' in data or 'costo' in data:
            pass
        db.session.commit()
        return jsonify({'message': 'Producto actualizado', 'producto': _producto_to_dict(p)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar producto: {str(e)}'}), 500

@almacenista.route('/api/productos/<int:idproducto>', methods=['DELETE'])
def eliminar_producto(idproducto):
    error = verificar_almacenista()
    if error:
        return error
    try:
        p = Producto.query.get_or_404(idproducto)
        if p.movimientos and len(p.movimientos) > 0:
            return jsonify({'error': 'No se puede eliminar un producto con movimientos registrados'}), 400
        db.session.delete(p)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar producto: {str(e)}'}), 500

# Movimientos
@almacenista.route('/api/movimientos', methods=['GET'])
def listar_movimientos():
    error = verificar_almacenista()
    if error:
        return error
    try:
        q = Movimientos.query
        idproducto = request.args.get('idproducto')
        tipo = request.args.get('tipo')
        if idproducto and idproducto.isdigit():
            q = q.filter(Movimientos.idproducto == int(idproducto))
        if tipo in ('entrada', 'salida', 'ajuste'):
            q = q.filter(Movimientos.tipo == tipo)
        movimientos = q.order_by(Movimientos.fecha.desc()).limit(200).all()
        return jsonify([m.to_dict() for m in movimientos])
    except Exception as e:
        return jsonify({'error': f'Error al listar movimientos: {str(e)}'}), 500


@almacenista.route('/api/lotes/vencidos', methods=['GET'])
def listar_lotes_vencidos():
    error = verificar_almacenista()
    if error:
        return error
    try:
        hoy = date.today()
        q = (
            db.session.query(Lote, Producto.nombre.label('producto_nombre'))
            .join(Producto, Producto.idproducto == Lote.idproducto)
            .filter(Lote.fecha_vencimiento.isnot(None), Lote.fecha_vencimiento < hoy)
            .order_by(Lote.fecha_vencimiento.asc())
        )
        items = []
        for lote, producto_nombre in q.all():
            items.append({
                'idlote': lote.idlote,
                'idproducto': lote.idproducto,
                'producto': producto_nombre,
                'cantidad_actual': int(lote.cantidad_actual or 0),
                'cantidad_inicial': int(lote.cantidad_inicial or 0),
                'fecha_vencimiento': lote.fecha_vencimiento.isoformat() if lote.fecha_vencimiento else None,
                'costo_unitario': int(lote.costo_unitario or 0),
                'fecha_ingreso': lote.fecha_ingreso.isoformat() if lote.fecha_ingreso else None,
            })
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': f'Error al listar lotes vencidos: {str(e)}'}), 500


@almacenista.route('/api/lotes/producto/<int:idproducto>', methods=['GET'])
def listar_lotes_por_producto(idproducto):
    """Obtiene todos los lotes de un producto específico"""
    error = verificar_almacenista()
    if error:
        return error
    try:
        Producto.query.get_or_404(idproducto)
        lotes = (
            Lote.query
            .filter(Lote.idproducto == idproducto)
            .order_by(Lote.fecha_ingreso.desc())
            .all()
        )
        items = []
        hoy = date.today()
        for lote in lotes:
            vencido = lote.fecha_vencimiento is not None and lote.fecha_vencimiento < hoy
            items.append({
                'idlote': lote.idlote,
                'cantidad_actual': int(lote.cantidad_actual or 0),
                'cantidad_inicial': int(lote.cantidad_inicial or 0),
                'fecha_vencimiento': lote.fecha_vencimiento.isoformat() if lote.fecha_vencimiento else None,
                'costo_unitario': int(lote.costo_unitario or 0),
                'fecha_ingreso': lote.fecha_ingreso.isoformat() if lote.fecha_ingreso else None,
                'vencido': vencido,
                'dias_para_vencer': (lote.fecha_vencimiento - hoy).days if lote.fecha_vencimiento else None,
            })
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': f'Error al listar lotes: {str(e)}'}), 500


@almacenista.route('/api/movimientos', methods=['POST'])
def crear_movimiento():
    error = verificar_almacenista()
    if error:
        return error
    try:
        data = request.get_json() or {}
        idproducto = data.get('idproducto')
        tipo = data.get('tipo')
        cantidad = int(data.get('cantidad') or 0)
        if not idproducto or not tipo or cantidad <= 0:
            return jsonify({'error': 'Datos incompletos: idproducto, tipo y cantidad > 0 son requeridos'}), 400
        if tipo not in ('entrada', 'salida', 'ajuste'):
            return jsonify({'error': 'Tipo inválido'}), 400
        producto = Producto.query.get_or_404(idproducto)
        sid = session.get('user_id')
        user_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid

        if tipo in ('entrada', 'ajuste'):
            costo_unitario = data.get('costo_unitario')
            try:
                costo_unitario = int(costo_unitario)
            except Exception:
                return jsonify({'error': 'Costo unitario inválido'}), 400
            if costo_unitario < 10:
                return jsonify({'error': 'El costo unitario no puede ser menor a 10'}), 400

            fv = data.get('fecha_vencimiento')
            fv_date = None
            if fv:
                try:
                    fv_date = datetime.strptime(fv, '%Y-%m-%d').date()
                except Exception:
                    return jsonify({'error': 'Fecha de vencimiento inválida'}), 400

            lote = Lote(
                idproducto=producto.idproducto,
                cantidad_actual=cantidad,
                cantidad_inicial=cantidad,
                fecha_vencimiento=fv_date,
                costo_unitario=costo_unitario,
            )
            db.session.add(lote)
            db.session.flush()

            mov = Movimientos(
                idproducto=producto.idproducto,
                idlote=lote.idlote,
                idusuario=user_uuid,
                tipo=tipo,
                cantidad=cantidad,
                costototal=int(cantidad) * int(costo_unitario or 0),
                fecha=datetime.utcnow(),
            )
            db.session.add(mov)
            db.session.flush()

            if tipo == 'entrada' and (mov.costototal or 0) > 0:
                eg = Egreso(
                    idmovimiento=mov.idmovimiento,
                    descripcion=f"Entrada de stock producto {producto.nombre}",
                    monto=float(mov.costototal or 0),
                    fechaegreso=mov.fecha.date() if hasattr(mov.fecha, 'date') else date.today(),
                )
                db.session.add(eg)

            db.session.commit()
            return jsonify({
                'message': 'Movimiento registrado',
                'producto': _producto_to_dict(producto),
                'movimiento': mov.to_dict(),
            }), 201

        # Filtrar solo lotes vigentes (no vencidos)
        hoy = date.today()
        lotes_vigentes = or_(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento >= hoy)
        
        lotes = (
            Lote.query
            .filter(
                Lote.idproducto == producto.idproducto,
                Lote.cantidad_actual > 0,
                lotes_vigentes  # Solo lotes no vencidos
            )
            .order_by(
                expression.nulls_last(Lote.fecha_vencimiento.asc()),
                Lote.fecha_ingreso.asc(),
            )
            .all()
        )
        restante = cantidad
        movimientos_creados = []

        for lote in lotes:
            if restante <= 0:
                break
            disponible = int(lote.cantidad_actual or 0)
            if disponible <= 0:
                continue
            tomar = disponible if disponible < restante else restante
            lote.cantidad_actual = disponible - tomar
            mov = Movimientos(
                idproducto=producto.idproducto,
                idlote=lote.idlote,
                idusuario=user_uuid,
                tipo='salida',
                cantidad=tomar,
                costototal=int(tomar) * int(lote.costo_unitario or 0),
                fecha=datetime.utcnow(),
            )
            db.session.add(mov)
            movimientos_creados.append(mov)
            restante -= tomar

        if restante > 0:
            db.session.rollback()
            return jsonify({'error': 'Stock insuficiente - no hay suficiente stock en lotes vigentes'}), 400

        db.session.commit()
        return jsonify({
            'message': 'Movimiento registrado',
            'producto': _producto_to_dict(producto),
            'movimientos': [m.to_dict() for m in movimientos_creados],
        }), 201
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear movimiento: {str(e)}'}), 500


@almacenista.route('/api/lotes/<int:idlote>/descartar-vencido', methods=['POST'])
def descartar_lote_vencido(idlote):
    """Descarta un lote vencido y registra el movimiento como salida/descarte"""
    error = verificar_almacenista()
    if error:
        return error
    try:
        lote = Lote.query.get_or_404(idlote)
        hoy = date.today()
        
        # Verificar que esté vencido
        if lote.fecha_vencimiento is None or lote.fecha_vencimiento >= hoy:
            return jsonify({'error': 'El lote no está vencido'}), 400
        
        # Verificar que tenga cantidad
        if lote.cantidad_actual <= 0:
            return jsonify({'error': 'El lote ya está vacío'}), 400
        
        cantidad_descartada = int(lote.cantidad_actual or 0)
        producto = Producto.query.get_or_404(lote.idproducto)
        sid = session.get('user_id')
        user_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid
        
        # Crear movimiento de salida/descarte
        mov = Movimientos(
            idproducto=lote.idproducto,
            idlote=lote.idlote,
            idusuario=user_uuid,
            tipo='salida',
            cantidad=cantidad_descartada,
            costototal=int(cantidad_descartada) * int(lote.costo_unitario or 0),
            fecha=datetime.utcnow(),
        )
        db.session.add(mov)
        
        # Marcar lote como agotado
        lote.cantidad_actual = 0
        
        db.session.commit()
        return jsonify({
            'message': f'Lote vencido descartado (cantidad: {cantidad_descartada} unidades)',
            'producto': _producto_to_dict(producto),
            'movimiento': mov.to_dict(),
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al descartar lote: {str(e)}'}), 500


@almacenista.route('/api/lotes/<int:idlote>', methods=['DELETE'])
def eliminar_lote(idlote):
    """Elimina un lote específico"""
    error = verificar_almacenista()
    if error:
        return error
    try:
        lote = Lote.query.get_or_404(idlote)
        idproducto = lote.idproducto
        
        # Verificar que el lote no tenga movimientos asociados
        if lote.movimientos and len(lote.movimientos) > 0:
            return jsonify({'error': 'No se puede eliminar un lote con movimientos registrados'}), 400
        
        db.session.delete(lote)
        db.session.commit()
        
        producto = Producto.query.get_or_404(idproducto)
        return jsonify({
            'message': f'Lote #{idlote} eliminado correctamente',
            'producto': _producto_to_dict(producto),
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar lote: {str(e)}'}), 500


@almacenista.route('/api/lotes/<int:idlote>', methods=['PUT'])
def editar_lote(idlote):
    """Edita los datos de un lote específico (cantidad actual, fecha vencimiento, costo)"""
    error = verificar_almacenista()
    if error:
        return error
    try:
        lote = Lote.query.get_or_404(idlote)
        data = request.get_json() or {}
        
        # Editar cantidad actual
        if 'cantidad_actual' in data:
            nueva_cantidad = int(data['cantidad_actual'] or 0)
            if nueva_cantidad < 0:
                return jsonify({'error': 'La cantidad no puede ser negativa'}), 400
            lote.cantidad_actual = nueva_cantidad
        
        # Editar costo unitario
        if 'costo_unitario' in data:
            nuevo_costo = int(data['costo_unitario'] or 0)
            if nuevo_costo < 10:
                return jsonify({'error': 'El costo unitario no puede ser menor a 10'}), 400
            lote.costo_unitario = nuevo_costo
        
        # Editar fecha de vencimiento
        if 'fecha_vencimiento' in data:
            if data['fecha_vencimiento'] is None:
                lote.fecha_vencimiento = None
            else:
                try:
                    lote.fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d').date()
                except Exception:
                    return jsonify({'error': 'Fecha de vencimiento inválida'}), 400
        
        db.session.commit()
        producto = Producto.query.get_or_404(lote.idproducto)
        return jsonify({
            'message': 'Lote actualizado correctamente',
            'producto': _producto_to_dict(producto),
            'lote': {
                'idlote': lote.idlote,
                'cantidad_actual': int(lote.cantidad_actual or 0),
                'cantidad_inicial': int(lote.cantidad_inicial or 0),
                'fecha_vencimiento': lote.fecha_vencimiento.isoformat() if lote.fecha_vencimiento else None,
                'costo_unitario': int(lote.costo_unitario or 0),
                'fecha_ingreso': lote.fecha_ingreso.isoformat() if lote.fecha_ingreso else None,
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al editar lote: {str(e)}'}), 500