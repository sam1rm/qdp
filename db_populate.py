#!/usr/bin/python

import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password

from app import db
from app import models
from app.models import User, Role, Question

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

db.create_all()

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

with app.app_context():
    password = encrypt_password('password')
    print password

default_role = user_datastore.create_role(name='user', description='Generic user role')

admin_role = user_datastore.create_role(name='admin', description='Generic administrator role')

user = user_datastore.create_user(password=password, email = "headcrash@berkeley.edu", fullname = "Glenn Sugden", confirmed_at=datetime.datetime.now())

user_datastore.add_role_to_user(user, admin_role)

user = user_datastore.create_user(password=password, email = "carolm@EECS.berkeley.edu", confirmed_at=datetime.datetime.now(), fullname = "Carol Marshall")

user_datastore.add_role_to_user(user, admin_role)

user = user_datastore.create_user(password=password, email = "user@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Joe User")

user_datastore.add_role_to_user(user, default_role)

user = user_datastore.create_user(password=password, email = "unverified@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Unverified User")

user = user_datastore.create_user(password=password, email = "hack666@gmail.com", fullname = "Joe Hacker")

question = Question(created = datetime.datetime.now(), for_class = "9F", quiz = 1, section="Operator expressions",  \
    instructions="Circle the correct expression. Assume default meanings for each operator.",                       \
    question = "cin >> x or cin << x\ncout << \"value for n?\" or cout << \'value for n?\'",                        \
    examples = None, hints = None, answer = "cin >> x\ncout << \"value for n?\"", num_reviews = 0, user_id = 1 )

db.session.add(question)

db.session.commit()
