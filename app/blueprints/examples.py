from flask import Blueprint, render_template, current_app

bp = Blueprint('examples', __name__, url_prefix='/examples')

@bp.route('/')
def render_examples():
    train_idcs = current_app.config['examples']
    return render_template('examples.html', example_idcs=train_idcs)