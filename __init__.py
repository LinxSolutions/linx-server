from flask import Flask, render_template, url_for
from blueprints.web import api
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from blueprints.web import g

app = Flask(__name__)
app.register_blueprint(api)
bcrypt = Bcrypt(app)
mongo = PyMongo(app)


@app.before_request
def before_request():
	g.mongo = mongo
	g.bcrypt = bcrypt


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download')
def download():
    return render_template('download.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)