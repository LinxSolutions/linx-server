from flask import Blueprint, render_template, request
import db

web = Blueprint('web', __name__, template_folder='templates')


@web.route('/web/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.signin(username, password)

    else:
        return render_template('login.html')