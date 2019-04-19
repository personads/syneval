from flask import Blueprint, render_template, current_app

bp = Blueprint('examples', __name__, url_prefix='/examples')

@bp.route('/')
def index():
    train_idcs = current_app.config['examples']
    num_classes = len(current_app.config['tasks'][0]['other']) + 1
    return render_template('examples.html', example_idcs=train_idcs, num_classes=num_classes)
