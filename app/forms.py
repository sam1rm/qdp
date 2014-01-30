# File: forms.py
# Author: Glenn Sugden
# Date: 2013.09.01
# Description: These are (the models for) the forms shown by the Flask framework via the WTForms module.
# Caution: VERY SENSITIVE - DO NOT DISTRIBUTE OUTSIDE OF THE SELF-PACED CENTER AT UC:BERKELEY! 

from flask.ext.wtf import Form
from wtforms import TextField, SelectField, TextAreaField, HiddenField
from wtforms.validators import Required
from flask_security.forms import RegisterForm, ConfirmRegisterForm

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    """ An attempt to add an additional field to the confirm registration form (requesting the full name)
        TODO: Get this to work correctly!""" 
    fullname = TextField('Full Name', validators = [Required()])
   
class CustomRegisterForm(RegisterForm):
    """ An attempt to add an additional field to the register (login) form (requesting the full name)
    TODO: Get this to work correctly!""" 
    fullname = TextField('Full Name', validators = [Required()])
   
class QuestionForm(Form):
    """ The form for the individual  questions. Some of the fields are optional (no validator)"""
    quiz = SelectField('quiz', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], validators = [Required()])
    tags = TextField('tags', validators = [Required()])
    instructions = TextAreaField('instructions')
    question = TextAreaField('question', validators = [Required()])
    examples = TextAreaField('examples')
    hints = TextAreaField('hints')
    answer = TextAreaField('answer', validators = [Required()])

class ReviewQuestionForm(Form):
    """ The form for reviewing the question, which contains the original question in hidden fields,
    then the comment fields for each of the fields in the Question form (above). All of them
    are optional (not "validated")"""
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
    """ A simple form for reporting a bug. """
    what = SelectField('what', choices=[('bug',"Bug"),('feature',"Suggest a Feature")], validators = [Required()])
    who = TextField('who')
    where = TextField('where')
    when = TextField('when')
    report = TextAreaField('report')