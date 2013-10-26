import copy

from app import db, login_serializer
from flask import flash
from flask.ext.security import UserMixin, RoleMixin
from werkzeug import generate_password_hash, check_password_hash

from utils import decrypt, encrypt, convertToHTML
  
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
    
    def __repr__(self):
        return '<Role %d>' % self.id

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
    def get(uid):
        return User.query.filter_by(id=uid).one()

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
        return ('user' in self.roles or 'admin' in self.roles)
    
    def is_admin(self):
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
    def hasUnverifiedUsers():
        for user in User.query.order_by(User.id):
            if (user.is_verified() == False):
                return True
        return False

    @staticmethod
    def getAllUnverifiedUsers():
        unverifiedUsers = None
        for user in User.query.order_by(User.id):
            if (user.is_verified() == False):
                if unverifiedUsers:
                    unverifiedUsers.append(user)
                else:
                    unverifiedUsers=[user]
        return unverifiedUsers

    def __repr__(self):
        return '<User %d>' % self.id

    def __str__(self):
        return 'User #%d: %s' % (self.id, self.fullname)
 
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
        return 'ClassInfo %s (%s): startingID=%d, currentID=%d' % (self.classAbbr, self.longName, self.startingID, self.currentID)
 
class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    classID = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    classAbbr = db.Column(db.String(4))
    quiz = db.Column(db.Integer)
    tags = db.Column(db.String(256))
    tagsIV=db.Column(db.String(16))
    tagsComments = db.Column(db.Text)
    tagsCommentsIV=db.Column(db.String(16))
    instructions = db.Column(db.Text)
    instructionsIV=db.Column(db.String(16))
    instructionsComments = db.Column(db.Text)
    instructionsCommentsIV=db.Column(db.String(16))
    question = db.Column(db.Text)
    questionIV=db.Column(db.String(16))
    questionComments = db.Column(db.Text)
    questionCommentsIV=db.Column(db.String(16))
    examples = db.Column(db.Text)
    examplesIV=db.Column(db.String(16))
    examplesComments = db.Column(db.Text)
    examplesCommentsIV=db.Column(db.String(16))
    hints = db.Column(db.Text)
    hintsIV=db.Column(db.String(16))
    hintsComments = db.Column(db.Text)
    hintsCommentsIV=db.Column(db.String(16))
    answer = db.Column(db.Text)
    answerIV=db.Column(db.String(16))
    answerComments = db.Column(db.Text)
    answerCommentsIV=db.Column(db.String(16))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Relationships with other models
    reviewers = db.relationship('User', secondary = users_questions, backref = db.backref('reviewers', lazy = 'dynamic'))
    
    @staticmethod
    def get(id):
        questions = None
        questions = Question.query.filter_by(id=id)
        if ((questions == None) or (questions.count()==0)):
            flash("Couldn't find any questions in the database with (raw) ID: %d" % id)
            return None
        if (questions.count()>1):
            flash("Found more than one question (%d) in the database with (raw) ID: %d" % (questions.count(),id))
        return questions.one()    

    @staticmethod
    def getUsingClassID(classID):
        questions = None
        questions = Question.query.filter_by(classID=classID)
        if ((questions == None) or (questions.count()==0)):
            flash("Couldn't find any questions in the database with (class) ID: %d" % classID)
            return None
        if (questions.count()>1):
            flash("Found more than one question (%d) in the database with (class) ID: %d" % (questions.count(),classID))
        return questions.one()    
    
    def tagsAsSet(self):
        result=set()
        if self.tags:
            for tag in self.tags.split(","):
                result.add(tag.strip())
        return result
    
    def shortenedDecryptedQuestionWithMarkup(self):
        """ Returned a short..ed version of the (unencrypted) question text with HTML markup """
        encryptedQuestion = self.question
        if encryptedQuestion:
            encryptedQuesionIV = self.questionIV 
            question = decrypt(encryptedQuestion,encryptedQuesionIV).strip()
            if (len(question)<80):
                return convertToHTML(question)
            else:
                return convertToHTML(question[0:38].strip())+"..."+convertToHTML(question[-38:].strip())
        else:
            return "?? NO QUESTION TEXT ??"

    def shortenedDecryptedTags(self):
        """ Returned a short..ed version of the (unencrypted) tags """
        encryptedTags = self.tags
        if encryptedTags:
            encryptedTagsIV = self.tagsIV 
            tags = decrypt(encryptedTags,encryptedTagsIV).strip()
            if (len(tags)<80):
                return tags
            else:
                return tags[0:38].strip()+"..."+tags[-38:].strip()
        else:
            return "?? NO TAGS ??"
        
    def offsetNumberFromClass(self, classInfo):
        assert (type(self.classID)==type(1)), "self.classID (%r) != int??" % self.classID
        assert (type(classInfo.startingID)==type(1)), "classInfo.startingID (%r) != int??" % classInfo.startingID
        offsetNumber = ( self.classID - classInfo.startingID )
        assert (type(offsetNumber)==type(1)), "offsetNumber (%r) != int??" % offsetNumber
        return offsetNumber
    
    def findSimilarQuestions(self):
        """ Find questions "similar" to this one. Uses quiz # and tags.
            TODO: Union questions with the same tag(s) - right now it's looking for equal tags. """
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
                self.tags = decrypt(self.tags,self.tagsIV)
            if self.instructions:
                self.instructions = decrypt(self.instructions,self.instructionsIV)
            if self.question:
                self.question = decrypt(self.question,self.questionIV)
            if self.examples:
                self.examples = decrypt(self.examples,self.examplesIV)
            if self.hints:
                self.hints = decrypt(self.hints,self.hintsIV)
            if self.answer:
                self.answer = decrypt(self.answer,self.answerIV)
        if ((questionOnly == None) or (questionOnly == False)):
            if self.tagsComments:
                self.tagsComments = decrypt(self.tagsComments,self.tagsCommentsIV)
            if self.instructionsComments:
                self.instructionsComments = decrypt(self.instructionsComments,self.instructionsCommentsIV)
            if self.questionComments:
                self.questionComments = decrypt(self.questionComments,self.questionCommentsIV)
            if self.examplesComments:
                self.examplesComments = decrypt(self.examplesComments,self.examplesIV)
            if self.hintsComments:
                self.hintsComments = decrypt(self.hintsComments,self.hintsCommentsIV)
            if self.answerComments:
                self.answerComments = decrypt(self.answerComments,self.answerCommentsIV)
                
    @staticmethod
    def detachAndDecryptQuestionText(question, questionOnly = False, commentsOnly = False):
        """ Decrypt all of the question text, including tags and comments. """
        convertedQuestion = copy.copy(question)
        convertedQuestion.decryptQuestionText(questionOnly, commentsOnly)
        return convertedQuestion

    @staticmethod
    def addMarkupToQuestionText(question, questionOnly = False, commentsOnly = False):
        """ Add HTML markup to all of the question text, including tags and comments. This is mostly used for \n -> <br /> """
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
        """ Encrypt all of the question text, including tags and comments. """
        if ((commentsOnly == None) or (commentsOnly == False)):
            self.tags, self.tagsIV = encrypt(self.tags)
            self.instructions, self.instructionsIV = encrypt(self.instructions)
            self.question, self.questionIV = encrypt(self.question)
            self.examples, self.examplesIV = encrypt(self.examples)
            self.hints, self.hintsIV = encrypt(self.hints)
            self.answer, self.answerIV = encrypt(self.answer)
        if ((questionOnly == None) or (questionOnly == False)):
            self.tagsComments, self.tagsCommentsIV = encrypt(self.tagsComments)
            self.instructionsComments, self.instructionsCommentsIV = encrypt(self.instructionsComments)
            self.questionComments,self.questionCommentsIV = encrypt(self.questionComments)
            self.examplesComments,self.examplesCommentsIV = encrypt(self.examplesComments)
            self.hintsComments,self.hintsCommentsIV = encrypt(self.hintsComments)
            self.answerComments,self.answerCommentsIV = encrypt(self.answerComments)
                  
    @staticmethod
    def generateQuiz(classInfo, quizNumber, cachedQuestions):
        """ Generate quiz # for a class, using previously cached questions (caller is responsible for these). 
            TODO: Find questions with: most reviews, then different tags"""
        quizQuestions = []
        #questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            if (question.quiz == quizNumber):
                markedUpQuestion = Question.addMarkupToQuestionText(Question.detachAndDecryptQuestionText(question,questionOnly=True))
                quizQuestions.append(markedUpQuestion)
                if (len(quizQuestions)>5):
                    break
        return quizQuestions, Question.generateIDFromQuestions(classInfo, quizQuestions)
    
    @staticmethod
    def generateFinalExam(classInfo, cachedQuestions):
        """ Generate final exam # for a class, using previously cached questions (caller is responsible for these) 
            TODO: Find questions with: most reviews, then different tags"""
        examQuestions = []
        #questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            markedUpQuestion = Question.addMarkupToQuestionText(Question.detachAndDecryptQuestionText(question,questionOnly=True))
            examQuestions.append(markedUpQuestion)
            if (len(examQuestions)>5):
                break
        return examQuestions, Question.generateIDFromQuestions(classInfo, examQuestions)
    
    @staticmethod
    def generateIDFromQuestions(classInfo, questions):
        """ Generate an ID from quiz question ids.
            1024 questions per quiz possible. Question IDs in the database
            are offsets from the ClassInfo starting IDs. """
        validIDSymbols="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len(validIDSymbols)
        idSymbols = classInfo.classAbbr
        for question in questions:
            idSymbols += '.'
            qid = ( question.classID - classInfo.startingID )
            if (qid > numIDSymbols):
                idSymbols += validIDSymbols[id/numIDSymbols]
            idSymbols += validIDSymbols[qid%numIDSymbols]
        return idSymbols

    @staticmethod
    def getQuestionsFromID(idSymbols, addMarkupToQuestionTextToo):
        """ Retrieve quiz question from an ID. Question IDs in the database
            are offsets from the ClassInfo starting IDs. """
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
                        questionNumber = validIDSymbols.find(symbol)
                        if (len(questionNumbers[index])>1):
                            symbol = questionNumbers[index][1]
                            if symbol in validIDSymbols:
                                questionNumber = questionNumber * numIDSymbols + validIDSymbols.find(symbol)
                            else:
                                flash("ID '%s' is invalid in code: %s"%(questionNumbers[index],idSymbols), category="warning")
                                continue
                    else:
                        flash("ID '%s' is invalid in code: %s"%(questionNumbers[index],idSymbols), category="warning")
                        continue
                    questionClassID = classInfo.startingID + questionNumber
                    try:
                        question = Question.getUsingClassID(questionClassID)
                        decryptedQuestion = Question.detachAndDecryptQuestionText(question, questionOnly=True)
                        if addMarkupToQuestionTextToo:
                            decryptedQuestion = Question.addMarkupToQuestionText(decryptedQuestion, questionOnly=True)
                        questions.append(decryptedQuestion)
                    except Exception as ex:
                        flash ("ID '%s' isn't a valid question [class] id (%d) for class: %s in code: %s" % (questionNumbers[index], questionClassID, questionNumbers[index], idSymbols), category="warning")
                        continue
        return questions

    def __repr__(self):
        return '<Question %r>' % (self.id)

    def __str__(self):
        return "Question #%d (classID: %d): %s" % (self.id, self.classID, self.decryptAndShortenQuestion())
    
class Image(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    data = db.Column(db.LargeBinary(4096), unique=True)
    
    @staticmethod
    def getByName(filename):
        images = None
        images = Image.query.filter_by(name=filename)
        if ((images == None) or (images.count()==0)):
            flash("Couldn't find any images in the database with filename: %s" % filename)
            return None
        if (images.count()>1):
            flash("Found more than one image (%d) in the database with filename: %s" % filename)
        return images.one()    
  
    def __repr__(self):
        return '<Image %r>' % (self.id)

    def __str__(self):
        return "Image #%d (size=%d): %s" % (self.id, len(self.data), self.name)
