#!/usr/bin/python

import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password

from app import db
from app.models import User, Role, Question, ClassInfo, Image, encrypt

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

# Setup Flask-Security

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

#########
# ROLES #
#########

default_role = user_datastore.create_role(name='user', description='Generic user role')

admin_role = user_datastore.create_role(name='admin', description='Generic administrator role')

#########
# USERS #
#########

with app.app_context():
    password = encrypt_password('shouldnotbepassword')
    #print password

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

##############
# CLASS INFO #
##############
    
classInfo9A = ClassInfo( classAbbr = "9A", longName="Matlab", startingID = 0, currentID = 0 )
db.session.add(classInfo9A)
classInfo9C = ClassInfo( classAbbr = "9C", longName="C", startingID = 10000, currentID = 10000 )
db.session.add(classInfo9C)
classInfo9E = ClassInfo( classAbbr = "9E", longName="Unix", startingID = 20000, currentID = 20000 )
db.session.add(classInfo9E)
classInfo9F = ClassInfo( classAbbr = "9F", longName="C++", startingID = 30000, currentID = 30000 )
db.session.add(classInfo9F)
classInfo9G = ClassInfo( classAbbr = "9G", longName="Java", startingID = 40000, currentID = 40000 )
db.session.add(classInfo9G)
classInfo9H = ClassInfo( classAbbr = "9H", longName="Python", startingID = 50000, currentID = 50000 )
db.session.add(classInfo9H)

#############
# QUESTIONS #
#############

##########
# IMAGES #
##########

path = "db_populate_images/"
filename = "9c.3.1.gif"
imageDataFileRef = open(path+filename)
assert imageDataFileRef,"Can't find %s??"%path+filename
imageData = imageDataFileRef.read()
assert imageData,"Image (%s) is empty??"%path+filename
imageDataFileRef.close()
image = Image( name=filename, data=imageData )
db.session.add(image)

##########
# 9C : C #
##########

encryptedTags, encryptedTagsIV = encrypt(u"Data Structures,Pointers")
encryptedInstructions, encryptedInstructionsIV = encrypt(u"class ListNode {\npublic:\n    ListNode (const int k);\n    ListNode (const int k, const ListNode* ptr);\n    ...\nprivate:\n    int value;\n    ListNode *next;\n};\n\nSuppose that p, list1, and list2 are variables of type ListNode *, and that list1 and list2 point to the following structures.\n\t((list1 diagram))\n\t((list2 diagram))")
encryptedQuestion, encryptedQuestionIV = encrypt(u"Draw the diagram that results from executing the following code segment.\n\tp = list1->next;\n\tlist1->next->next = list2;\n\tp->next->next = list1;\n\tlist2->next->value = 5;")
encryptedExample, encryptedExampleIV = encrypt(u"[[9c.3.1.gif]]")
encryptedAnswer, encryptedAnswerIV = encrypt(u"[[9c.3.1.answer.gif]]")

question = Question(classID = classInfo9C.startingID, created = datetime.datetime.now(), classAbbr = classInfo9C.classAbbr, quiz = 3,   \
    tags=encryptedTags, instructions=encryptedInstructions, question = encryptedQuestion, answer = encryptedAnswer,                     \
    tagsIV=encryptedTagsIV, instructionsIV=encryptedInstructionsIV, questionIV=encryptedQuestionIV, answerIV = encryptedAnswerIV,       \
    user_id = 1  )

db.session.add(question)

#####+######
# 9F : C++ #
############

encryptedTags, encryptedTagsIV = encrypt("uOperators,Expressions")
encryptedInstructions, encryptedInstructionsIV = encrypt(u"Circle the correct expression. Assume default meanings for each operator.")
encryptedQuestion, encryptedQuestionIV = encrypt(u"cin >> x or cin << x\ncout << \"value for n?\" or cout << \'value for n?\'")
encryptedAnswer, encryptedAnswerIV = encrypt(u"cin >> x\ncout << \"value for n?\"")

question = Question(classID = classInfo9F.startingID, created = datetime.datetime.now(), classAbbr = classInfo9F.classAbbr, quiz = 1,   \
    tags=encryptedTags, instructions=encryptedInstructions, question = encryptedQuestion, answer = encryptedAnswer,                     \
    tagsIV=encryptedTagsIV, instructionsIV=encryptedInstructionsIV, questionIV=encryptedQuestionIV, answerIV = encryptedAnswerIV,       \
    user_id = 1 )

db.session.add(question)

db.session.commit()
