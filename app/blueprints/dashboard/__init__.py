from flask import Blueprint, request, redirect, url_for,  render_template
from app.blueprints import g
from sparkpost import SparkPost

dashboard = Blueprint('dashboard', __name__, url_prefix="/me")
sp = SparkPost('1b98111f51fd10764b736f0c9293e2ee6f5cc01f')


@dashboard.route('/')
def index():
    if g.is_logged_in() is not True:
        return redirect(url_for('login'))
    if 'language_id' in g.session['user']:
        pass
        # language = g.mongo.linx.languages.find_one({'language_id': g.session['user']['language_id']})
    return render_template('template.html', page='dashboard.html')