from flask.ext.wtf import Form
from wtforms import TextField, SelectField, TextAreaField, HiddenField
from wtforms.validators import Required
from flask_security.forms import RegisterForm, ConfirmRegisterForm
# from models import User

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class CustomRegisterForm(RegisterForm):
    fullname = TextField('Full Name', validators = [Required()])
   
class QuestionForm(Form):
    quiz = SelectField('quiz', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], validators = [Required()])
    tags = TextField('tags', validators = [Required()])
    instructions = TextAreaField('instructions')
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
    
class ReportForm(Form):
    what = SelectField('what', choices=[('bug',"Bug"),('feature',"Suggest a Feature")], validators = [Required()])
    who = TextField('who')
    where = TextField('where')
    when = TextField('when')
    report = TextAreaField('report')
    
# class UploadImageForm(Form):
#     name = TextAreaField('name')
