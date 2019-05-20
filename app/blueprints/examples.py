from flask import Blueprint, render_template, current_app

bp = Blueprint('examples', __name__, url_prefix='/examples')

@bp.route('/')
def index():
    example_idcs = current_app.config['examples']
    classes = current_app.config['classes']
    return render_template('examples.html', classes=classes, example_idcs=example_idcs)
