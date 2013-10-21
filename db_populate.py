#!/usr/bin/python

import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password

from app import db
from app.models import User, Role, Question, ClassInfo, encrypt

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

with app.app_context():
    password = encrypt_password('shouldnotbepassword')
    #print password

default_role = user_datastore.create_role(name='user', description='Generic user role')

admin_role = user_datastore.create_role(name='admin', description='Generic administrator role')

user = user_datastore.create_user(password=password, email = "headcrash@berkeley.edu", fullname = "Glenn Sugden", confirmed_at=datetime.datetime.now())

user_datastore.add_role_to_user(user, default_role)
user_datastore.add_role_to_user(user, admin_role)

user = user_datastore.create_user(password=password, email = "carolm@EECS.berkeley.edu", confirmed_at=datetime.datetime.now(), fullname = "Carol Marshall")

user_datastore.add_role_to_user(user, default_role)
user_datastore.add_role_to_user(user, admin_role)

user = user_datastore.create_user(password=password, email = "user@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Joe User")

user_datastore.add_role_to_user(user, default_role)

user = user_datastore.create_user(password=password, email = "arie.coach@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Arie Meir")

user_datastore.add_role_to_user(user, default_role)

user = user_datastore.create_user(password=password, email = "unverified@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Unverified User")

user = user_datastore.create_user(password=password, email = "hack666@gmail.com", fullname = "Joe Hacker")
    
classInfo = ClassInfo( classAbbr = "9A", longName="Matlab", startingID = 0, currentID = 0 )
db.session.add(classInfo)
classInfo = ClassInfo( classAbbr = "9C", longName="C", startingID = 10000, currentID = 10000 )
db.session.add(classInfo)
classInfo = ClassInfo( classAbbr = "9E", longName="Unix", startingID = 20000, currentID = 20000 )
db.session.add(classInfo)
classInfo = ClassInfo( classAbbr = "9F", longName="C++", startingID = 30000, currentID = 30000 )
db.session.add(classInfo)
classInfo = ClassInfo( classAbbr = "9G", longName="Java", startingID = 40000, currentID = 40000 )
db.session.add(classInfo)
classInfo = ClassInfo( classAbbr = "9H", longName="Python", startingID = 50000, currentID = 50000 )
db.session.add(classInfo)

encryptedTags = encrypt("Operators,Expressions")
encryptedInstructions = encrypt("Circle the correct expression. Assume default meanings for each operator.")
encryptedQuestion = encrypt("cin >> x or cin << x\ncout << \"value for n?\" or cout << \'value for n?\'")
encryptedAnswer = encrypt("cin >> x\ncout << \"value for n?\"")

question = Question(classID = 30000, created = datetime.datetime.now(), classAbbr = "9F", quiz = 1, tags=encryptedTags,  \
    instructions=encryptedInstructions, question = encryptedQuestion, answer = encryptedAnswer, user_id = 1 )

db.session.add(question)

db.session.commit()
