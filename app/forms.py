from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, TextAreaField
from wtforms.validators import Required

class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
    
class QuestionForm(Form):
    quiz = SelectField('quiz', choices=[('q1', '1'), ('q2', '2'), ('q3', '3'), ('q4', '4'), ('q5', '5'), ('q6', '6')])
    section = TextField('section', validators = [Required()])
    instructions = TextAreaField('instructions', validators = [Required()])
    question = TextAreaField('question', validators = [Required()])
    examples = TextAreaField('examples')
    hints = TextAreaField('hints')
    answer = TextAreaField('answer', validators = [Required()])
    
#     def _value(self):
#         if self.data:
#             return u', '.join(self.data)
#         else:
#             return u''
#     
#     def process_formdata(self, valuelist):
#         if valuelist:
#             self.data = [x.strip() for x in valuelist[0].split(',')]
#         else:
#             self.data = []
            
    from app import app