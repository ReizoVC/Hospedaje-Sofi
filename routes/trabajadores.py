from flask import Blueprint, render_template

trabajadores = Blueprint('trabajadores', __name__)


@trabajadores.route('/', strict_slashes=False)
def inicio_trabajadores():
    return render_template('staff/landing.html')
