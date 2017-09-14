from flask import Blueprint, request, Response, redirect
from sparkpost import SparkPost
import json
import string
import random


api = Blueprint('api', __name__, url_prefix="/api")


BASE_URL = 'https://linxsolutions.net'

with open('/var/www/linx/sparkpost.txt', 'r') as api_key:
	sp = SparkPost(api_key.read())


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
	send_email(email, 'Welcome to Linx!', body)


def send_email(email, subject, body):
	response = sp.transmissions.send(
	    use_sandbox=False,
	    recipients=[email],
	    html=body,
	    from_email='welcome@linxsolutions.net',
	    subject=subject
	)

	print response


def error_msg(msg):
	return build_response('{"status": "error", "message": "'+msg+'"}')


def success_msg(response):
	return build_response('{"status": "success", "response": '+json.dumps(response)+'}')


def get_user(user):
	return {
		"fname": user['fname'],
		"lname": user['lname'],
		"username": user['username'],
		"email": user['email'],
		"languages": user['languages'],
		"plan_id": user['plan_id'],
		"confirmation_key": user['confirmation_key'],
		"isConfirmed": user['isConfirmed'],
		"isSuspended": user['isSuspended']
	}


def build_response(response):
	resp = Response(response)
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp


@api.route('/lessons', methods=['POST'])
def lessons():
	if request.method == 'POST':
		username = request.form['username']
		language_id = int(request.form['language_id'])

		language = g.mongo.db.linx.languages.find_one({})[str(language_id-1)]

		user_lessons = g.mongo.db.linx.users.find_one({"username": username})['languages'][language_id-1]['lessons']


		for lesson in language['lessons']:
			for user_lesson in user_lessons:
				if lesson['lesson_id'] == user_lesson['lesson_id']:
					for question in lesson['questions']:
						for user_question in user_lesson['questions']:
							if question['question_id'] == user_question['question_id']:
								question['results'] = user_question

		return success_msg(language['lessons'])

	else:
		return error_msg('Failed')


		

@api.route('/lesson', methods=['POST'])
def lesson():
	if request.method == 'POST':
		title = request.form['title']
		subtitle = request.form['subtitle']
		language_id = int(request.form['language_id'])

		language = g.mongo.db.linx.languages.find_one({})[str(language_id-1)]

		questions = []

		for lesson in language['lessons']:
			for media in lesson['media']:
				if media['title'] == title:
					for q in lesson['questions']:
						q['lesson_id'] = lesson['lesson_id']
					questions.extend(lesson['questions'])
					break

		final = []

		l = []

		captions = g.mongo.db.linx.captions.find_one({'title': title, 'subtitle': subtitle})['captions']
		for caption in captions:
			words = caption['text'].lower().split()
			for word in words:
				for question in questions:
					if question['translation'] == '' or question['transliteration'] == '':
						if word == question['word']:
							if len(word) > 4:
								if word not in l:
									print word
									final.append(question)
									l.append(word)

		return success_msg(final)
	else:
		return error_msg('Failed')





@api.route('/progress', methods=['POST'])
def progress():
	if request.method == 'POST':
		username = request.form['username']
		language_id = request.form['language_id']
		lesson_id = request.form['lesson_id']
		question_id = request.form['question_id']
		mark = request.form['mark']

		user_lessons = g.mongo.db.linx.users.find_one({"username": username})['languages'][language_id-1]['lessons']

		exists = False

		for lesson in user_lessons:
			if lesson_id == lesson['lesson_id']:
				for question in lesson['question']:
					if question_id in question['question_id']:
						
						user_lessons.update(
						  { 
						    "username" : username, 
						    "languages.language_id" : language_id, 
						    "languages.lessons.lesson_id" : lesson_id,
						    "languages.lessons.questions.question_id": question_id
						  },
						  { 
							'$set': { "languages.lessons.questions.$."+mark : question[mark]+1 } 
						  },
						  false,
						  true
						)
						exists = True
						break


		if exists is not True:
			correct = 0
			incorrect = 0

			if mark == 'correct':
				correct = 1
			else:
				incorrect = 1

			user_lessons.update(
				{
					"username" : username, 
				    "languages.language_id" : language_id, 
				    "languages.lessons.lesson_id" : lesson_id
				}, 
				{
					'$push': {
						'questions': {
							'question_id': question_id,
							'correct': correct,
							'incorrect': incorrect
						}
					}
				}
			)

		return success_msg(lessons)
	return error_msg('Failed')






@api.route('/scrap', methods=['GET', 'POST'])
def scrap():
	c = request.form['captions']
	c = json.loads(c)
	
	exists = g.mongo.db.linx.captions.find_one({'title': c['title'], 'subtitle': c['subtitle']})

	if exists is None:

		inserted = g.mongo.db.linx.captions.insert_one(c)

		if inserted is not None:
			return success_msg({'inserted': True})
		else:
			return error_msg('Failed to insert captions')

	else:
		return error_msg('Failed to insert captions')


@api.route('/confirm/<username>/<confirmation_key>')
def confirm(username, confirmation_key):
	user = g.mongo.db.linx.users.find_one({"username": username, "confirmation_key": confirmation_key})
	if user is not None:
		g.mongo.db.linx.users.update_one({"username": username}, {"$set": {"isConfirmed": True}})
		return success_msg(get_user(user))
	return error_msg('the user does not exist')


@api.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user = g.mongo.db.linx.users.find_one({"username": username})
		print user
		if user is not None:
			if g.bcrypt.check_password_hash(user["password"], password):
				if user['isConfirmed']:
					if user['isSuspended'] is False:
						return success_msg(get_user(user))
					return error_msg('Your account has been suspended.')
				return error_msg('A confirmation email has been sent to '+user['email']+'.')
		return error_msg('Username or Password Incorrect')
	return error_msg('Something weird just happened at our end.')


@api.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		u = request.get_json()
		u['isConfirmed'] = False
		u['isSuspended'] = False
		
		if u['password'] == u['confirm']:
			u.pop('confirm', None)
			username_exist = g.mongo.db.linx.users.find_one({"username": u['username']})
			email_exist = g.mongo.db.linx.users.find_one({"email": u['email']})

			if email_exist is None:
				if username_exist is None:
					password = g.bcrypt.generate_password_hash(u['password'])
					confirmation_key = generate_random()
					
					u['password'] = password
					u['confirmation_key'] = confirmation_key
					u['plan_id'] = 0
					u['language_id'] = [1]

					user_id = g.mongo.db.linx.users.insert_one(u)

					if user_id is not None:
						send_confirmation_email(u['fname'], u['email'], u['confirmation_key'])
						return success_msg({'email': u['email']})
					else:
						return error_msg('An unexpected error has occured.')
				else:
					return error_msg('Username is unavailable.')
			else:
				return error_msg('An account is already registed with this email.')
		else:
			return error_msg('Passwords do not match.')
	else:
		return error_msg('Something went wrong.')




class g:
	def __init__(self):
		g.mongo = None
		g.bcrypt = None