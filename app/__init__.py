from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)

#app.logger.debug("config")

app.config.from_object('config')

#app.logger.debug("SQLAlchemy")

db = SQLAlchemy(app)

#app.logger.debug("LoginManager")

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'security.login'
lm.session_protection = "strong"

#app.logger.debug("login_serializer")

#Login_serializer used to encryt and decrypt the cookie token for the remember
#me option of flask-login
login_serializer = URLSafeTimedSerializer(app.secret_key)

#app.logger.debug("models")

from app import models

#app.logger.debug("security")

# Setup Flask-Security
from app.models import User, Role
from app.forms import ExtendedConfirmRegisterForm, CustomRegisterForm
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, \
                    confirm_register_form=CustomRegisterForm)#, login_form=ExtendedLoginForm)

#app.logger.debug("flask_mail")

# Setup Flask-Security Mail
from flask_mail import Mail
mail = Mail(app)

#app.logger.debug("views")

from app import views
