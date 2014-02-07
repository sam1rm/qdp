from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer

#=== Main Flask entry point ===

app = Flask(__name__)

app.config.from_object('config')

#=== Database ===

db = SQLAlchemy(app)

#=== Flask-Login setup ===

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'security.login'
lm.session_protection = "strong"

#Login_serializer used to encryt and decrypt the cookie token for the remember
#me option of flask-login
login_serializer = URLSafeTimedSerializer(app.secret_key)

#=== Security "Oracle" ===

import oracle

oracle.init(app.config['SECRET_KEY'], encryptedPrefixFlag='QDP');

from app import models

#=== Flask-Security setup ===

from app.models import User, Role
from app.forms import ExtendedConfirmRegisterForm, CustomRegisterForm
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, \
                    confirm_register_form=CustomRegisterForm)#, login_form=ExtendedLoginForm)

#=== Flask-Mail setup ===

from flask_mail import Mail
mail = Mail(app)

from app import views
