from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from utils.db import db

# Importar modelos para que se registren con SQLAlchemy
from models.usuario import Usuario
from models.habitaciones import Habitacion
from models.imagenes_habitaciones import ImagenHabitacion

from routes.inicio import inicio
from routes.auth import auth
from routes.admin import admin
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env para usar Supabase (PostgreSQL)
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui_muy_segura_123')

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

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)