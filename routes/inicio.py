from flask import Blueprint, render_template
from utils.db import db

inicio = Blueprint('inicio', __name__)

@inicio.route('/')
def index():
    return render_template('pages/index.html')

@inicio.route('/habitaciones')
def habitaciones():
    return render_template('pages/habitaciones.html')

@inicio.route('/nosotros')
def nosotros():
    return render_template('pages/nosotros.html')

@inicio.route('/login')
def login():
    return render_template('auth/login.html')

@inicio.route('/register')
def register():
    return render_template('auth/register.html')