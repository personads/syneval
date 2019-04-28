import json, os

from collections import OrderedDict

from flask import Flask, render_template, send_from_directory, session

from blueprints import auth, examples, evaluation

def create_app():
    app = Flask('syneval', instance_relative_config=True)

    # load configuration
    with open('config.json', 'r', encoding='utf8') as fop:
        config = json.load(fop, object_pairs_hook=OrderedDict)
    app.config.update(config)

    # add data path
    @app.route('/data/<path:file>')
    def data(file):
        return send_from_directory(app.config['data_path'], file)

    # add obscured eval data path
    @app.route('/data/truth/<int:task_id>')
    def eval_audio(task_id):
        audio_path = '%d_audio.wav' % app.config['tasks'][task_id]['truth']
        return send_from_directory(app.config['data_path'], audio_path)

    # add landing page
    @app.route('/')
    def index():
        return render_template('intro.html', eval_name=app.config['name'])

    # add landing page
    @app.route('/thanks')
    def thanks():
        # retrieve  uid
        uid = session.get('uid', None)
        if uid is None:
            return "Could not retrieve UID.", 500
        # calculate accuracy
        results = evaluation.load_user_choices(uid)
        # check for completion
        if None in results:
            accuracy = None
        else:
            truths = [task['truth'] for task in app.config['tasks']]
            accuracy = sum([1 for i in range(len(truths)) if truths[i] == results[i]]) / len(truths)
        return render_template('thanks.html', accuracy=accuracy)

    # configure blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(examples.bp)
    app.register_blueprint(evaluation.bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config.get('debug', False))
