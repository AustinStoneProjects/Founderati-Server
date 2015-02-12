from functools import wraps
from flask.ext.login import LoginManager, AnonymousUserMixin, login_user, logout_user, current_user
from flask import jsonify
from flask.ext.bcrypt import Bcrypt
from flask.ext.api.status import HTTP_401_UNAUTHORIZED
from project.services.database import Database
from bson.objectid import ObjectId
from functools import wraps

class Auth:
    GHOST = 1
    USER = 2

    class Anonymous(AnonymousUserMixin):
        def __init__(self):
            self._id = None
    
        def get_id(self):
            return unicode('')

    def __init__(self):
        self.__login_manager = LoginManager()
        self.config = {}

    def init_app(self, app, config):
        print 'Attaching LoginManager to app.'
        self.__login_manager.init_app(app)
        self.__login_manager.anonymous_user = Auth.Anonymous
        self.config = config

        def load_user(user_id):
            if user_id == '':
                return None

            Users = Database['Users']

            return Users.User.find_one({'_id': ObjectId(user_id)})

        def unauthorized():
            return jsonify(error='Unauthorized'), HTTP_401_UNAUTHORIZED

        self.__login_manager.user_loader(load_user)
        self.__login_manager.unauthorized_handler(unauthorized)

        self.__bcrypt = Bcrypt(app)

    def login_manager(self):
        return self.__login_manager

    def require(self, user_level):
        def login_required(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if current_user.is_authenticated() and current_user.get_access_level() >= user_level:
                    return f(*args, **kwargs)
                return self.__login_manager.unauthorized()
            return decorated_function
        return login_required

    def login(self, user_object, password_hash):
        if user_object is not None:
            if self.__bcrypt.check_password_hash(user_object['password'], password_hash):
                login_user(user_object)            
            else:
                return 'Invalid password'
        else:
            return 'Invalid email'
        return None

    def logout(self):
        logout_user()

    def hash_password(self, password):
        return self.__bcrypt.generate_password_hash(password)

    # decorator that protects other users from PUT/POST/DELETE on you stuff
    # user_id _must_ be passed in as 'user_id'
    def only_me(self, function):
        @wraps(function)
        def inner(*args, **kwargs):
            if kwargs['user_id'] != 'me':
                return '{}', HTTP_401_UNAUTHORIZED
            return function(*args, **kwargs)
        return inner

# singleton (soft enforcement)
Auth = Auth()
