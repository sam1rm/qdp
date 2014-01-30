

from datetime import timedelta
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Debugging (must be off for deployment!)

DEBUG = True

# Stop the debugging toolbar (flask-debugtoolbar) from stopping redirects (initiated by the app)

DEBUG_TB_INTERCEPT_REDIRECTS = False

# For the "Oracle" for checking that form submissions came from the app, and not somewhere else.

CSRF_ENABLED = True
SECRET_KEY = '6FxLM4DBMHbkgqKty2YRCyfS'

# "Remember me" login cookie, short settings for security

REMEMBER_COOKIE_DURATION = timedelta(days=1)

# Main database settings (app.db)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Security settings for flask.ext.security

SECURITY_CONFIRMABLE = False
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_CHANGEABLE = True
SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
SECURITY_PASSWORD_SALT = 'v1n5= 9f77v]xP+mtw|6tQ15$n.0>%LP|g?DE>9MfdP0&]L*$H(TUrQ_Aw8Wp!mU'

# Mail server (mainly for bug reports)

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'headcrash@berkeley.edu'
MAIL_PASSWORD = 'DDVhd,(gC^54'

# QDP Specific

REVIEWS_BEFORE_OK_TO_USE = 3
MAX_NUMBER_OF_QUESTIONS = 5

# File uploads

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

