from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from app import db
from app import models
from app.models import User, Question

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

arie = User.query.filter_by(email = "arie.coach@gmail.com").first()
arie.approved = 2
db.session.merge(arie)
db.session.commit()

print "Arie's now a superuser. Keep an eye on him."