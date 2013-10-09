#!/usr/bin/python

import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from app import db
from app import models
from app.models import User, Question

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

user = User(created = datetime.datetime.now(), last_access = datetime.datetime.now(),       \
                    nickname = 'hEADcRASH', email = "headcrash13@gmail.com",                \
                    fullname = "Glenn Sugden", approved=2)

db.session.add(user)

user = User(created = datetime.datetime.now(), last_access = datetime.datetime.now(),       \
                    nickname = 'Self-Paced Lady', email = "carolm@EECS.Berkeley.edu",       \
                    fullname = "Carol Marshall", approved=2)

db.session.add(user)

user = User(created = datetime.datetime.now(), last_access = datetime.datetime.now(),      \
                    nickname = '1337hacker', email = "hack666@gmail.com",                  \
                    fullname = "Joe Hacker", approved=0)

db.session.add(user)

question = Question(created = datetime.datetime.now(), for_class = "9F", quiz = 1, section="Operator expressions",  \
    instructions="Circle the correct expression. Assume default meanings for each operator.",                       \
    question = "cin >> x or cin << x\ncout << \"value for n?\" or cout << \'value for n?\'",                        \
    examples = None, hints = None, answer = "cin >> x\ncout << \"value for n?\"", num_reviews = 0, user_id = 1 )

db.session.add(question)

db.session.commit()
