from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore

from app import db
from app import models
from app.models import User, Question, Role

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

arie = User.query.filter_by(email = "arie.coach@gmail.com").first()
default_role = user_datastore.find_or_create_role('user')
user_datastore.add_role_to_user(arie, default_role)
db.session.merge(arie)
db.session.commit()

print "Arie's now a superuser. Keep an eye on him."