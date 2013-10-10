import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from config import basedir
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'security.login'
lm.session_protection = "strong"

#Login_serializer used to encryt and decrypt the cookie token for the remember
#me option of flask-login
login_serializer = URLSafeTimedSerializer(app.secret_key)

from app import models

# Setup Flask-Security
from models import User, Role
from forms import ExtendedConfirmRegisterForm, CustomRegisterForm
#app.logger.debug("Setup Flask-Security")
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, \
                    confirm_register_form=CustomRegisterForm)#, login_form=ExtendedLoginForm)

# Setup Flask-Security Mail
from flask_mail import Mail
mail = Mail(app)
