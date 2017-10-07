import string
import random
import json


class g:

    def __init__(self):
        self.mongo = None
        self.bcrypt = None
        self.session = None
        self.current_user = None

    @staticmethod
    def error_msg(msg):
        return '{"status": "error", "message": "' + msg + '"}'

    @staticmethod
    def generate_random(n=8):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

    @staticmethod
    def success_msg(response):
        return '{"status": "success", "response": ' + json.dumps(response) + '}'

    @staticmethod
    def is_logged_in():
        g.session_counter()
        return 'user' in g.session

    @staticmethod
    def session_counter():
        try:
            g.session['counter'] += 1
        except KeyError:
            g.session['counter'] = 1