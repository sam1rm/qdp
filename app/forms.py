from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, TextAreaField
from wtforms.validators import Required
from flask_security.forms import RegisterForm, ConfirmRegisterForm
# from models import User

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class CustomRegisterForm(RegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class QuestionForm(Form):
    quiz = SelectField('quiz', choices=[('q1', '1'), ('q2', '2'), ('q3', '3'), ('q4', '4'), ('q5', '5'), ('q6', '6')])
    section = TextField('section', validators = [Required()])
    instructions = TextAreaField('instructions', validators = [Required()])
    question = TextAreaField('question', validators = [Required()])
    examples = TextAreaField('examples')
    hints = TextAreaField('hints')
    answer = TextAreaField('answer', validators = [Required()])
