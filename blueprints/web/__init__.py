from flask import Blueprint, request
import json
import string
import random


api = Blueprint('api', __name__, url_prefix="/api")


BASE_URL = 'https://linxsolutions.net'


def generate_random():
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

def send_confirmation_email(fname, email, confirmation_key):
	confirmation_url = BASE_URL+'/api/confirm/'+confirmation_key
	body = '''
		Hi '''+fname+''',<br><br>
		You've just created an account on <a href="'''+BASE_URL+'''">Linx</a> but there's still one more step before you can start
		learning a new language!<br><br>
		Please confirm your email address by following this link:<br>
		<a href="'''+confirmation_url+'''">'''+confirmation_url+'''</a>
		<br><br>
		Thanks,
		Linx Team
		<br><br>
		<small>P.S. If you did not make an account, please disregard this email.</small>
	'''
	send_email(email, body)


def send_email(email, body):
	pass


def error_msg(msg):
	return '{"status": "error", "message": "'+msg+'"}'


def success_msg(response):
	return '{"status": "success", "response": '+json.dumps(response)+'}'


def get_user(user):
	return {
		"fname": user['fname'],
		"lname": user['lname'],
		"username": user['username'],
		"email": user['email'],
		"language_id": user['language_id'],
		"plan_id": user['plan_id'],
		"confirmation_key", user['confirmation_key']
		"is_confirmed": user['is_confirmed'],
		"is_suspended": user['is_suspended']
	}


# @api.route('/lesson/<username>/<confirmation_key>')
# def lesson(username, confirmation_key):
# 	user = g.mongo.db.linx.users.find_one({"username": username, "confirmation_key": confirmation_key})
	


@api.route('/confirm/<username>/<confirmation_key>')
def confirm(username, confirmation_key):
	user = g.mongo.db.linx.users.find_one({"username": username, "confirmation_key": confirmation_key})
	if user is not None:
		g.mongo.db.linx.users.update_one({"username": username}, {"$set": {"is_confirmed": True}})
		return success_msg(get_user(user))
	return error_msg('the user does not exist')


@api.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user = g.mongo.db.linx.users.find_one({"username": username})
		if user is not None:
			if g.bcrypt.check_password_hash(user["password"], password):
				if user['is_confirmed']:
					if user['is_suspended'] is False:
						return success_msg(get_user(user))
					return error_msg('your account has been suspended')
				return error_msg('a confirmation email has been sent to '+user['email'])
		return error_msg('username or password incorrect')
	return error_msg('invalid request method')


@api.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		fname = request.form['fname']
		lname = request.form['lname']
		username = request.form['username']
		email = request.form['email']
		password = request.form['password']
		confirm = request.form['confirm']
		
		language_id = request.form['language_id']
		plan_id = request.form['plan_id']

		if password == confirm:

			user = g.mongo.db.linx.users.find_one({"username": username})

			if user is None:

				password = g.bcrypt.generate_password_hash(password)

				confirmation_key = generate_random()

				user_id = g.mongo.db.linx.users.insert_one({
					"fname": fname,
					"lname": lname,
					"username": username,
					"email": email,
					"password": password,
					"language_id": [language_id],
					"plan_id": plan_id,
					"confirmation_key": confirmation_key,
					"is_confirmed": False,
					"is_suspended": False
					}).inserted_id

				
				if user_id is not None:
					print user_id
					send_confirmation_email(fname, email, confirmation_key)
					return success_msg({"email": email})
				return error_msg('failed to create user')
			return error_msg('username is unavailable')
		return error_msg('passwords do not match')
	return error_msg('invalid request method')




class g:
	def __init__(self):
		g.mongo = None
		g.bcrypt = None