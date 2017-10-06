from flask import Blueprint, request, Response, redirect, url_for
from sparkpost import SparkPost
import json
import string
import random


api = Blueprint('api', __name__, url_prefix="/api")


BASE_URL = 'https://linxsolutions.net'

#with open('../../../sparkpost.txt', 'r') as api_key:
sp = SparkPost('1b98111f51fd10764b736f0c9293e2ee6f5cc01f')


def generate_random():
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

def send_confirmation_email(fname, email, username, confirmation_key):
	confirmation_url = BASE_URL+'/api/confirm/'+username+'/'+confirmation_key
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

		language = g.mongo.db.linx.languages.find_one({})

		try:
			user_lessons = g.mongo.db.linx.users.find_one({"username": username})['languages'][language_id-1]['lessons']


			for lesson in language['lessons']:
				for user_lesson in user_lessons:
					if lesson['lesson_id'] == user_lesson['lesson_id']:
						for question in lesson['questions']:
							for user_question in user_lesson['questions']:
								if question['question_id'] == user_question['question_id']:
									question['results'] = user_question

			return success_msg(language['lessons'])
		except:
			return error_msg('Failed')
	else:
		return error_msg('Failed')


		

@api.route('/lesson', methods=['POST'])
def lesson():
	if request.method == 'POST':
		title = request.form['title']
		subtitle = request.form['subtitle']
		language_id = int(request.form['language_id'])

		language = g.mongo.db.linx.languages.find_one({})

		questions = []

		for lesson in language['lessons']:
			for media in lesson['media']:
				if media['title'] == title:
					for i in range(0, len(lesson['questions'])):
						lesson['questions'][i]['lesson_id'] = lesson['lesson_id']
					questions.extend(lesson['questions'])
					break

		final = []

		l = []

		captions = g.mongo.db.linx.captions.find_one({'title': title, 'subtitle': subtitle})['captions']
		for caption in captions:
			words = caption['text'].lower().split()
			for word in words:
				for question in questions:
					# if question['translation'] == '' or question['transliteration'] == '':
					if word == question['word']:
						if len(word) > 4:
							if word not in l:
								#print word
								final.append(question)
								l.append(word)

		return success_msg(final)
	else:
		return error_msg('Failed')





@api.route('/progress', methods=['POST'])
def progress():
	if request.method == 'POST':
		username = request.form['username']
		language_id = str(int(request.form['language_id'])-1)
		lesson_id = str(int(request.form['lesson_id'])-1)
		question_id = str(int(request.form['question_id'])-1)
		mark = request.form['mark']

		resp = g.mongo.db.linx.users.update(
			{ 
				"username" : username
			},
			{ '$inc': { "languages."+language_id+".lessons."+lesson_id+".questions."+question_id+"."+mark : 1 } }
		)

		resp['_id']= ''

		return success_msg(resp)
	return error_msg('Failed')






@api.route('/scrap', methods=['GET', 'POST'])
def scrap():
	c = request.form['captions']
	c = json.loads(c)

	inserted = None
	media = g.mongo.db.linx.captions.find_one({'title': c['title']})	

	if media is None:
			 
		inserted = g.mongo.db.linx.captions.insert_one({
			"title": c['title'],
			"episodes": [
				{
					"title": c['subtitle'],
					"url": c['url'],
					"captions": c['captions']
				}
			]
		})
	
	else:
		if 'episodes' in media:
			exists = False
			for episode in media['episodes']:
				if c['subtitle'] == episode['title']:
					exists = True
					if len(c['captions']) > len(episode['captions']):
						inserted = g.mongo.db.linx.captions.update_one({
							'title': c['title'],
							'episodes.$.title': c['subtitle']
						}, {'$set': {'captions': c['captions']}})
					break
			if exists is not True:
				inserted = g.mongo.db.linx.captions.update({
					'title': c['title']
				}, {'$push': {'episodes': {
					'title': c['subtitle'],
					'url': c['url'],
					'captions': c['captions']
				}}})
	
	if inserted is not None:
		# send to queue
		return success_msg({'inserted': True})
	else:
		return error_msg('Failed to insert captions')









@api.route('/confirm/<username>/<confirmation_key>')
def confirm(username, confirmation_key):
	user = g.mongo.db.linx.users.find_one({"username": username, "confirmation_key": confirmation_key})
	if user is not None:
		g.mongo.db.linx.users.update_one({"username": username}, {"$set": {"isConfirmed": True}})
		return redirect(url_for('success'))
	return error_msg('the user does not exist')


















@api.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user = g.mongo.db.linx.users.find_one({"username": username})
		
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

					language = g.mongo.db.linx.languages.find_one({})
					lessons = []

					for i in range(0, len(language['lessons'])):
						l = {"lesson_id": i+1, "questions": []}
						count = 1
						for question in language['lessons'][i]['questions']:
							l['questions'].append({"question_id": count, "correct": 0, "incorrect": 0})
							count += 1
						lessons.append(l)
					
					u['password'] = password
					u['confirmation_key'] = confirmation_key
					u['plan_id'] = 0
					u['languages'] = [
						{
							"language_id": 1,
							"name": "Japanese",
							"lessons": lessons
						}
					]



					user_id = g.mongo.db.linx.users.insert_one(u)

					if user_id is not None:
						send_confirmation_email(u['fname'], u['email'], u['username'], u['confirmation_key'])
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
