import json, os, random, string

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

def gen_uid():
    chars = string.ascii_letters + string.digits
    uid = ''.join(random.choice(chars) for _ in range(16))
    # intialise results as list of Nones
    json_path = os.path.join(current_app.config['result_path'], '%s.json' % uid)
    with open(json_path, 'w', encoding='utf8') as fop:
        json.dump([None for _ in range(len(current_app.config['tasks']))], fop)
    return uid

def is_valid_uid(uid):
    if not isinstance(uid, str):
        return False
    return os.path.isfile(os.path.join(current_app.config['result_path'], '%s.json' % uid))

@bp.route('/login', methods=('GET', 'POST'))
def login():
    # check if already logged in
    uid = session.get('uid', None)
    if is_valid_uid(uid):
        return redirect(url_for('index'))
    # check for code submission 
    error = False
    if request.method == 'POST':
        code = request.form['code']
        # if code matches, init session
        if code.lower() == current_app.config['code'].lower():
            session.clear()
            session['uid'] = gen_uid()
            return redirect(url_for('index'))
        else:
            error = True
    # render if not logged in or on error
    return render_template('auth.html', error=error)

@bp.before_app_request
def check_auth():
    if request.endpoint not in ['auth.login', 'static']:
        uid = session.get('uid', None)
        if not is_valid_uid(uid):
            return redirect(url_for('auth.login'))
