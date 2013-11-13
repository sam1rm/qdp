from datetime import timedelta
import os

basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

CSRF_ENABLED = True
SECRET_KEY = '6FxLM4DBMHbkgqKty2YRCyfS'
PADDING = "0123456789abcdef"

REMEMBER_COOKIE_DURATION = timedelta(days=30)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

SECURITY_CONFIRMABLE = True
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_CHANGEABLE = True
SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
SECURITY_PASSWORD_SALT = 'v1n5= 9f77v]xP+mtw|6tQ15$n.0>%LP|g?DE>9MfdP0&]L*$H(TUrQ_Aw8Wp!mU'

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

