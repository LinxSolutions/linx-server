from flask import Flask, render_template, url_for, request, redirect, session
from blueprints.web import api
from blueprints.dashboard import dashboard
# from blueprints.admin import admin
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from app.blueprints import g
import os

app = Flask(__name__)
app.secret_key = 'linx'
app.register_blueprint(api)
app.register_blueprint(dashboard)
# app.register_blueprint(admin)
bcrypt = Bcrypt(app)
mongo = PyMongo(app)


@app.before_request
def before_request():
    g.mongo = mongo
    g.bcrypt = bcrypt
    g.session = session


@app.route('/')
def index():
    # return render_template('template.html', page='index.html')
    return redirect('anime')


@app.route('/signup')
def signup():
    return render_template('template.html', page='signup.html')


@app.route('/login')
def login():
    return render_template('template.html', page='login.html')


@app.route('/anime')
def anime():
    return render_template('template.html', page='anime.html')


@app.route('/success')
def success():
    return render_template('template.html', page='success.html')


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
