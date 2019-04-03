import json, os, random

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')

def load_user_choices(uid):
    json_path = os.path.join(current_app.config['result_path'], '%s.json' % uid)
    with open(json_path, 'r', encoding='utf8') as fop:
        return json.load(fop)

def save_user_choices(uid, user_choices):
    json_path = os.path.join(current_app.config['result_path'], '%s.json' % uid)
    with open(json_path, 'w', encoding='utf8') as fop:
        json.dump(user_choices, fop)

@bp.route('/<int:page>', methods=('GET','POST'))
def index(page):
    error = None
    # sanity check
    total_pages = len(current_app.config['tasks'])
    if (page < 0) or (page >= total_pages):
        return "Evaluation sample is out of range.", 404
    # retrieve  uid
    uid = session.get('uid', None)
    if uid is None:
        return "Could not retrieve UID.", 500
    # load user choices
    user_choices = load_user_choices(uid)
    # process choice submission
    if request.method == 'POST':
        # check if choice was made
        if 'choice' in request.form:
            choice_idx = request.form['choice']
            user_choices[page] = int(choice_idx)
            save_user_choices(uid, user_choices)
            # direct to next page or end
            page += 1
            if page >= total_pages:
                return redirect(url_for('thanks'))
            else:
                return redirect(url_for('evaluation.index', page=page))
        else:
            error = "Don't forget to make a selection!"
    choice_idx = user_choices[page]
    # build evaluation page
    truth_idx = current_app.config['tasks'][page]['truth']
    option_idcs = current_app.config['tasks'][page]['other'] + [truth_idx]
    random.shuffle(option_idcs)
    return render_template('evaluation.html', error=error, truth_idx=truth_idx, option_idcs=option_idcs, choice_idx=choice_idx, page=page, total_pages=total_pages)
