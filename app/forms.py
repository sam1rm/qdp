from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, TextAreaField, HiddenField
from wtforms.validators import Required
from flask_security.forms import RegisterForm, ConfirmRegisterForm
# from models import User

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class CustomRegisterForm(RegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class QuestionForm(Form):
    quiz = SelectField('quiz', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')])
    tags = TextField('tags')
    instructions = TextAreaField('instructions', validators = [Required()])
    question = TextAreaField('question', validators = [Required()])
    examples = TextAreaField('examples')
    hints = TextAreaField('hints')
    answer = TextAreaField('answer', validators = [Required()])

class ReviewQuestionForm(Form):
    quiz = HiddenField('quiz')
    tags = HiddenField('tags')
    instructions = HiddenField('instructions')
    question = HiddenField('question')
    examples = HiddenField('examples')
    hints = HiddenField('hints')
    answer = HiddenField('answer')
    tagsComments = TextAreaField('tagComments')
    instructionsComments = TextAreaField('instructionsComments')
    questionComments = TextAreaField('questionComments')
    examplesComments = TextAreaField('examplesComments')
    hintsComments = TextAreaField('hintsComments')
    answerComments = TextAreaField('answerComments')
