from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.db import db
from models.producto import Producto
from models.movimientos import Movimientos
from models.egreso import Egreso
from datetime import datetime, date
import uuid

almacenista = Blueprint('almacenista', __name__)

def verificar_almacenista():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    if session.get('user_rol', 0) < 3:
        return jsonify({'error': 'Acceso no autorizado - se requiere rol de almacenista o superior'}), 403
    return None

@almacenista.before_request
def _proteger_rutas_almacenista():
    # Con prefijo /trabajadores, las APIs quedan como /trabajadores/api/...
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
        q = Producto.query
        nombre = request.args.get('q')
        bajos = request.args.get('bajos')
        por_vencer_dias = request.args.get('por_vencer_dias')
        if nombre:
            q = q.filter(Producto.nombre.ilike(f"%{nombre}%"))
        productos = q.all()
        data = [p.to_dict() for p in productos]
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
        fv = data.get('fecha_vencimiento')
        fv_date = datetime.strptime(fv, '%Y-%m-%d').date() if fv else None
        p = Producto(nombre=nombre, cantidad=cantidad, umbralminimo=umbral, costo=costo, fecha_vencimiento=fv_date)
        db.session.add(p)
        db.session.flush()
        if cantidad and cantidad > 0:
            sid = session.get('user_id')
            user_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid
            mov = Movimientos(
                idproducto=p.idproducto,
                idusuario=user_uuid,
                tipo='entrada',
                cantidad=cantidad,
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
        return jsonify({'message': 'Producto creado', 'producto': p.to_dict()}), 201
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
        if 'fecha_vencimiento' in data:
            fv = data.get('fecha_vencimiento')
            p.fecha_vencimiento = datetime.strptime(fv, '%Y-%m-%d').date() if fv else None
        if 'costo' in data:
            try:
                p.costo = int(data.get('costo') or 0)
            except Exception:
                return jsonify({'error': 'Costo inválido'}), 400
        db.session.commit()
        return jsonify({'message': 'Producto actualizado', 'producto': p.to_dict()})
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


def _aplicar_movimiento_stock(producto: Producto, tipo: str, cantidad: int):
    if cantidad <= 0:
        raise ValueError('La cantidad debe ser mayor a 0')
    if tipo == 'entrada':
        producto.cantidad = int(producto.cantidad or 0) + cantidad
    elif tipo == 'salida':
        disponible = int(producto.cantidad or 0)
        if cantidad > disponible:
            raise ValueError('Stock insuficiente')
        producto.cantidad = disponible - cantidad
    elif tipo == 'ajuste':
        producto.cantidad = int(producto.cantidad or 0) + cantidad
    else:
        raise ValueError('Tipo de movimiento no válido')

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
        _aplicar_movimiento_stock(producto, tipo, cantidad)
        sid = session.get('user_id')
        user_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid
        mov = Movimientos(
            idproducto=producto.idproducto,
            idusuario=user_uuid,
            tipo=tipo,
            cantidad=cantidad,
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
        return jsonify({'message': 'Movimiento registrado', 'producto': producto.to_dict(), 'movimiento': mov.to_dict()}), 201
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear movimiento: {str(e)}'}), 500