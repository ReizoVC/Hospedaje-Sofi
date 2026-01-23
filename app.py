from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from utils.db import db

from models.usuario import Usuario
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion
from models.reserva import Reserva
from models.checkinout import CheckInOut
from models.producto import Producto
from models.movimientos import Movimientos
from models.egreso import Egreso
from models.ingreso import Ingreso 
from models.valoracion import Valoracion

from routes.inicio import inicio
from routes.auth import auth
from routes.admin import admin
from routes.recepcionista import recepcionista
from routes.almacenista import almacenista
from routes.trabajadores import trabajadores
from routes.user import user
from routes.reservas import reservas
from routes.valoraciones import valoraciones
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if database_url and 'supabase.' in database_url and 'sslmode=' not in database_url:
    separator = '&' if '?' in database_url else '?'
    database_url = f"{database_url}{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///local.db'


app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta')

db.init_app(app)

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

# Registro de blueprints (auth antes que inicio)
app.register_blueprint(auth)
app.register_blueprint(inicio)
app.register_blueprint(trabajadores, url_prefix='/trabajadores')
app.register_blueprint(admin, url_prefix='/trabajadores')
app.register_blueprint(recepcionista, url_prefix='/trabajadores')
app.register_blueprint(almacenista, url_prefix='/trabajadores')
app.register_blueprint(user)
app.register_blueprint(reservas)
app.register_blueprint(valoraciones)

if os.environ.get('AUTO_CREATE_TABLES') == '1':
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)