from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from utils.db import db

# Importar modelos para que se registren con SQLAlchemy
from models.usuario import Usuario
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
from models.reserva import Reserva
from models.checkinout import CheckInOut
from models.producto import Producto
from models.movimientos import Movimientos
from models.egreso import Egreso
from models.ingreso import Ingreso  # <-- nuevo

from routes.inicio import inicio
from routes.auth import auth
from routes.admin import admin
from routes.recepcionista import recepcionista
from routes.almacenista import almacenista
from routes.user import user
from routes.reservas import reservas
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env para usar Supabase (PostgreSQL)
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos
# Heroku provee DATABASE_URL. Convertimos "postgres://" a "postgresql://" para SQLAlchemy 2.x
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Si es Supabase y no se indicó sslmode, forzamos sslmode=require
if database_url and 'supabase.' in database_url and 'sslmode=' not in database_url:
    separator = '&' if '?' in database_url else '?'
    database_url = f"{database_url}{separator}sslmode=require"

# Permitir fallback local si no hay DATABASE_URL definido
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///local.db'

# Opciones del engine para conexiones más robustas en entornos como Heroku
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta')

# Inicializar extensiones
db.init_app(app)

# Context processor para hacer la información del usuario disponible globalmente
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = {
            'id': session['user_id'],
            'email': session['user_email'],
            'name': session['user_name'],
            'rol': session['user_rol']
        }
    return {'user': user}

# Registrar blueprints
app.register_blueprint(inicio)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(recepcionista)
app.register_blueprint(almacenista)
app.register_blueprint(user)
app.register_blueprint(reservas)

# Crear las tablas si no existen (solo si se habilita explícitamente)
# En producción (Heroku) es preferible correr migraciones/creación vía one-off dyno
if os.environ.get('AUTO_CREATE_TABLES') == '1':
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)