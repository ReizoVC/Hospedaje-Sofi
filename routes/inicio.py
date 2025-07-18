from flask import Blueprint, render_template

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