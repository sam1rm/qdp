import base64
import copy

from app import db, login_serializer
from flask import flash
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from werkzeug import generate_password_hash, check_password_hash
  
roles_users = db.Table('roles_users',
        db.Column('users_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('roles_id', db.Integer(), db.ForeignKey('role.id')))

users_questions = db.Table('users_questions',
        db.Column('users_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('questions_id', db.Integer(), db.ForeignKey('question.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), unique = True)
    password = db.Column(db.String(255))
    fullname = db.Column(db.String(255), index = True, unique = True)
    active = db.Column(db.Boolean())
    created = db.Column(db.DateTime)
    # Flask-Security Fields
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    # Relationships with other models
    roles = db.relationship('Role', secondary = roles_users, backref = db.backref('users', lazy='dynamic'))
    questions = db.relationship('Question', secondary = users_questions, backref = db.backref('author', lazy = 'dynamic'))

    @staticmethod
    def get(id):
        return User.query.filter_by(id=id).one()

    def __repr__(self):
        return '<User #%d: %r>' % (self.id, self.email)

    def get_auth_token(self):
        """
        Encode a secure token for cookie
        """
        data = [str(self.id), self.password]
        return login_serializer.dumps(data)
     
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.id)
    
    def is_verified(self):
        from app import app
        return ('user' in self.roles or 'admin' in self.roles)
    
    def is_admin(self):
        from app import app
        return ('admin' in self.roles)
 
    def set_password(self, password):
        self.password = generate_password_hash(password)
   
    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def getAllAdmins():
        admins = None
        for user in User.query.order_by(User.id):
            if (user.is_admin()):
                if admins:
                    admins.append(user)
                else:
                    admins=[user]
        return admins
    
    @staticmethod
    def getAllUnverified():
        unverifiedUsers = None
        for user in User.query.order_by(User.id):
            if (user.is_verified() == False):
                if unverifiedUsers:
                    unverifiedUsers.append(user)
                else:
                    unverifiedUsers=[user]
        return unverifiedUsers
 
class ClassInfo(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    classAbbr = db.Column(db.String(4))
    longName = db.Column(db.String(256))
    startingID = db.Column(db.Integer)
    currentID = db.Column(db.Integer)

    @staticmethod
    def get(classAbbr):
        return ClassInfo.query.filter_by(classAbbr=classAbbr).one()

    def __repr__(self):
        return '<ClassInfo %r>' % self.id

    def __str__(self):
        return 'ClassInfo %s: %s, startingID=%d, currentID=%d' % (self.classAbbr, self.longName, self.startingID, self.currentID)
 
class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    classID = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    classAbbr = db.Column(db.String(4))
    quiz = db.Column(db.Integer)
    tags = db.Column(db.String(256))
    tagsComments = db.Column(db.Text)
    instructions = db.Column(db.Text)
    instructionsComments = db.Column(db.Text)
    question = db.Column(db.Text)
    questionComments = db.Column(db.Text)
    examples = db.Column(db.Text)
    examplesComments = db.Column(db.Text)
    hints = db.Column(db.Text)
    hintsComments = db.Column(db.Text)
    answer = db.Column(db.Text)
    answerComments = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Relationships with other models
    reviewers = db.relationship('User', secondary = users_questions, backref = db.backref('reviewers', lazy = 'dynamic'))

    @staticmethod
    def get(classID):
        return Question.query.filter_by(classID=classID).one()

    def __repr__(self):
        return '<Question %r>' % (self.id)

    def __str__(self):
        return "Question #%d: %s" % (self.id, self.decryptAndShortenQuestion())
    
    def tagsAsSet(self):
        result=set()
        if self.tags:
            for tag in self.tags.split(","):
                result.add(tag.strip())
        return result
    
    def shortenedDecryptedQuestionWithMarkup(self):
        ''' Returned a short..ed version of the (unencrypted) question text with HTML markup '''
        encryptedQuestion = self.question
        if encryptedQuestion:
            question = decrypt(encryptedQuestion).strip()
            if (len(question)<80):
                return convertToHTML(question)
            else:
                return convertToHTML(question[0:38].strip())+"..."+convertToHTML(question[-38:].strip())
        else:
            return "?? NO QUESTION TEXT ??"

    def shortenedDecryptedTags(self):
        ''' Returned a short..ed version of the (unencrypted) tags '''
        encryptedTags = self.tags
        if encryptedTags:
            tags = decrypt(encryptedTags).strip()
            if (len(tags)<80):
                return tags
            else:
                return tags[0:38].strip()+"..."+tags[-38:].strip()
        else:
            return "?? NO TAGS ??"
        
    def number(self,classInfo):
        return ( self.classID - classInfo.startingID )
    
    @staticmethod
    def idFromNumber(number,classInfo):
        return ( classInfo.startingID + number )
    
    def getAllReviewers(self):
        return self.reviewers

    def getSimilarQuestions(self):
        ''' Find questions "similar" to this one. Uses quiz # and tags.
            TODO: Union questions with the same tag(s) - right now it's looking for equal tags. '''
        existing=[]
        tags = self.tagsAsSet()
        instances = Question.query.filter(Question.id != self.id, Question.quiz == self.quiz).order_by(Question.id).all()
        for instance in instances:
            instanceTags = instance.tagsAsSet()
            if (len(instanceTags.intersection(tags))>0):
                existing.append(instance) 
        return existing
  
    def decryptQuestionText(self, questionOnly = False, commentsOnly = False):
        if ((commentsOnly == None) or (commentsOnly == False)):
            if self.tags:
                self.tags = decrypt(self.tags)
            if self.instructions:
                self.instructions = decrypt(self.instructions)
            if self.question:
                self.question = decrypt(self.question)
            if self.examples:
                self.examples = decrypt(self.examples)
            if self.hints:
                self.hints = decrypt(self.hints)
            if self.answer:
                self.answer = decrypt(self.answer)
        if ((questionOnly == None) or (questionOnly == False)):
            if self.tagsComments:
                self.tagsComments = decrypt(self.tagsComments)
            if self.instructionsComments:
                self.instructionsComments = decrypt(self.instructionsComments)
            if self.questionComments:
                self.questionComments = decrypt(self.questionComments)
            if self.examplesComments:
                self.examplesComments = decrypt(self.examplesComments)
            if self.hintsComments:
                self.hintsComments = decrypt(self.hintsComments)
            if self.answerComments:
                self.answerComments = decrypt(self.answerComments)
                
    @staticmethod
    def detachAndDecryptQuestionText(question, questionOnly = False, commentsOnly = False):
        ''' Decrypt all of the question text, including tags and comments. '''
        convertedQuestion = copy.copy(question)
        convertedQuestion.decryptQuestionText(questionOnly, commentsOnly)
        return convertedQuestion

    @staticmethod
    def addMarkupToQuestionText(question, questionOnly = False, commentsOnly = False):
        ''' Add HTML markup to all of the question text, including tags and comments. This is mostly used for \n -> <br /> '''
        convertedQuestion = copy.copy(question)
        if ((commentsOnly == None) or (commentsOnly == False)):
            if convertedQuestion.tags:
                convertedQuestion.tags = convertToHTML(convertedQuestion.tags)
            if convertedQuestion.instructions:
                convertedQuestion.instructions = convertToHTML(convertedQuestion.instructions)
            if convertedQuestion.question:
                convertedQuestion.question = convertToHTML(convertedQuestion.question)
            if convertedQuestion.examples:
                convertedQuestion.examples = convertToHTML(convertedQuestion.examples)
            if convertedQuestion.hints:
                convertedQuestion.hints = convertToHTML(convertedQuestion.hints)
            if convertedQuestion.answer:
                convertedQuestion.answer = convertToHTML(convertedQuestion.answer)
        if ((questionOnly == None) or (questionOnly == False)):
            if convertedQuestion.instructionsComments:
                convertedQuestion.instructionsComments = convertToHTML(convertedQuestion.instructionsComments)
            if convertedQuestion.questionComments:
                convertedQuestion.questionComments = convertToHTML(convertedQuestion.questionComments)
            if convertedQuestion.examplesComments:
                convertedQuestion.examplesComments = convertToHTML(convertedQuestion.examplesComments)
            if convertedQuestion.hintsComments:
                convertedQuestion.hintsComments = convertToHTML(convertedQuestion.hintsComments)
            if convertedQuestion.answerComments:
                convertedQuestion.answerComments = convertToHTML(convertedQuestion.answerComments)
        return convertedQuestion
 
    def encryptQuestionText(self, questionOnly = False, commentsOnly = False):
        ''' Encrypt all of the question text, including tags and comments. '''
        if ((commentsOnly == None) or (commentsOnly == False)):
            self.tags = encrypt(self.tags)
            self.instructions = encrypt(self.instructions)
            self.question = encrypt(self.question)
            self.examples = encrypt(self.examples)
            self.hints = encrypt(self.hints)
            self.answer = encrypt(self.answer)
        if ((questionOnly == None) or (questionOnly == False)):
            self.tagsComments = encrypt(self.tagsComments)
            self.instructionsComments = encrypt(self.instructionsComments)
            self.questionComments = encrypt(self.questionComments)
            self.examplesComments = encrypt(self.examplesComments)
            self.hintsComments = encrypt(self.hintsComments)
            self.answerComments = encrypt(self.answerComments)
               
#     @staticmethod 
#     def convertFromHTML(text):
#         import flask
#         result = ""
#         if text:
#             for line in text.split('<br />'):
#                 line = flask.Markup(line)
#                 result += line.unescape() + '\n'
#             result = result[:-1]
#         return result
    
    @staticmethod
    def generateQuiz(classAbbr, classInfo, quizNumber, cachedQuestions):
        ''' Generate quiz # for a class, using previously cached questions (caller is responsible for these). 
            TODO: Find questions with: most reviews, then different tags'''
        quizQuestions = []
        #questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            if (question.quiz == quizNumber):
                markedUpQuestion = Question.addMarkupToQuestionText(Question.detachAndDecryptQuestionText(question,questionOnly=True))
                quizQuestions.append(markedUpQuestion)
                if (len(quizQuestions)>5):
                    break
        return quizQuestions, Question.IDFromQuestions(classInfo, quizQuestions)
    
    @staticmethod
    def generateFinalExam(classAbbr, classInfo, cachedQuestions):
        ''' Generate final exam # for a class, using previously cached questions (caller is responsible for these) 
            TODO: Find questions with: most reviews, then different tags'''
        examQuestions = []
        #questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            markedUpQuestion = Question.addMarkupToQuestionText(Question.detachAndDecryptQuestionText(question,questionOnly=True))
            examQuestions.append(markedUpQuestion)
            if (len(examQuestions)>5):
                break
        return examQuestions, Question.IDFromQuestions(classInfo, examQuestions)
    
    @staticmethod
    def IDFromQuestions(classInfo, questions):
        ''' Generate an ID from quiz question ids.
            1024 questions per quiz possible '''
        validIDSymbols="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len(validIDSymbols)
        idSymbols = classInfo.classAbbr
        for question in questions:
            idSymbols += '.'
            id = question.number(classInfo)
            if (id > numIDSymbols):
                idSymbols += validIDSymbols[id/numIDSymbols]
            idSymbols += validIDSymbols[id%numIDSymbols]
        return idSymbols

    @staticmethod
    def questionsFromID(idSymbols):
        ''' Retrieve quiz question from an ID.'''
        validIDSymbols="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len(validIDSymbols)
        questions = []
        questionNumbers = idSymbols.split('.')
        if (len(questionNumbers)<2):
            flash("ID (%s) doesn't have any question IDs??" % idSymbols, category="error")
        else:
            for index in range(0,len(questionNumbers)):
                if (index == 0):
                    try:
                        classInfo = ClassInfo.get(questionNumbers[index])
                    except Exception as ex:
                        flash ("idSymbol (%s) isn't a valid class abbreviation." % questionNumbers[index], category="error")
                        break
                else:
                    symbol = questionNumbers[index][0]
                    if symbol in validIDSymbols:
                        rawClassNumber = validIDSymbols.find(symbol)
                        if (len(questionNumbers[index])>1):
                            symbol = questionNumbers[index][1]
                            if symbol in validIDSymbols:
                                rawClassNumber = rawClassNumber * numIDSymbols + validIDSymbols.find(symbol)
                            else:
                                flash("ID '%s' is invalid in code: %s"%(questionNumbers[index],idSymbols), category="warning")
                                continue
                    else:
                        flash("ID '%s' is invalid in code: %s"%(questionNumbers[index],idSymbols), category="warning")
                        continue
                    questionID = Question.idFromNumber(rawClassNumber, classInfo)
                    try:
                        question = Question.get(questionID)
                        questions.append(Question.detachAndDecryptQuestionText(question,questionOnly=True))
                    except Exception as ex:
                        flash ("ID '%s' isn't a valid question [class] id (%d) for class: %s in code: %s" % (questionNumbers[index], questionID, questionNumbers[index], idSymbols), category="warning")
                        continue
        return questions

def convertToHTML(text):
    import flask
    result = ""
    if text:
        for line in text.split('\n'):
            result += flask.Markup.escape(line) + flask.Markup('<br />')
        result = result[:-6]
    return result

import config
from Crypto.Cipher import AES

def encrypt(message):
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, config.IV)
    numToPad = 16 - ( len(message) + 4 ) % 16
    paddedMessage = "%04d%s%s" % (len(message),message,config.PADDING[:numToPad])
    encryptedMessage = OBJ.encrypt(paddedMessage)
    b64Message = base64.b64encode(encryptedMessage)
    return(b64Message)

def decrypt(b64Message):
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, config.IV)
    message = base64.b64decode(b64Message)
    paddedMessage = OBJ.decrypt(message)
    messageLen = int(paddedMessage[:4])
    numToPad = 16 - ( messageLen + 4 ) % 16
    message = paddedMessage[4:messageLen+4]
    if (paddedMessage[messageLen+4:] != config.PADDING[:numToPad]):
        return "INVALID PADDING"
    return(message)
