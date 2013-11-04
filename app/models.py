import copy
import doctest

from app import db, login_serializer
from flask import flash
from flask.ext.security import UserMixin, RoleMixin
from werkzeug import generate_password_hash, check_password_hash

from utils import decrypt, encrypt, convertToHTML, replaceImageTags, readTempFile, writeTempFile

roles_users = db.Table( 'roles_users',
        db.Column( 'users_id', db.Integer(), db.ForeignKey( 'user.id' ) ),
        db.Column( 'roles_id', db.Integer(), db.ForeignKey( 'role.id' ) ) )

users_questions = db.Table( 'users_questions',
        db.Column( 'users_id', db.Integer(), db.ForeignKey( 'user.id' ) ),
        db.Column( 'questions_id', db.Integer(), db.ForeignKey( 'question.id' ) ) )

questions_histories = db.Table( 'questions_histories',
        db.Column( 'questions_id', db.Integer(), db.ForeignKey( 'question.id' ) ),
        db.Column( 'history_id', db.Integer(), db.ForeignKey( 'history.id' ) ) )

class Role( db.Model, RoleMixin ):
    id = db.Column( db.Integer(), primary_key = True )
    name = db.Column( db.String( 80 ), unique = True )
    description = db.Column( db.String( 255 ) )

    def __repr__( self ):
        return '<Role %d>' % self.id

class User( db.Model, UserMixin ):
    id = db.Column( db.Integer, primary_key = True )
    email = db.Column( db.String( 255 ), unique = True )
    password = db.Column( db.String( 255 ) )
    fullname = db.Column( db.String( 255 ), index = True, unique = True )
    active = db.Column( db.Boolean() )
    created = db.Column( db.DateTime )
    # Flask-Security Fields
    confirmed_at = db.Column( db.DateTime() )
    last_login_at = db.Column( db.DateTime )
    current_login_at = db.Column( db.DateTime )
    last_login_ip = db.Column( db.String( 100 ) )
    current_login_ip = db.Column( db.String( 100 ) )
    login_count = db.Column( db.Integer )
    # Relationships with other models
    roles = db.relationship( 'Role', secondary = roles_users, backref = db.backref( 'users', lazy = 'dynamic' ) )
    questions = db.relationship( 'Question', secondary = users_questions, backref = db.backref( 'author', lazy = 'dynamic' ) )

    @staticmethod
    def get( uid ):
        return User.query.filter_by( id = uid ).one()

    def get_auth_token( self ):
        """
        Encode a secure token for cookie
        """
        data = [str( self.id ), self.password]
        return login_serializer.dumps( data )

    def is_authenticated( self ):
        return True

    def is_active( self ):
        return True

    def is_anonymous( self ):
        return False

    def get_id( self ):
        return unicode( self.id )

    def is_verified( self ):
        return ( 'user' in self.roles or 'admin' in self.roles )

    def is_admin( self ):
        return ( 'admin' in self.roles )

    def set_password( self, password ):
        self.password = generate_password_hash( password )

    def check_password( self, password ):
        return check_password_hash( self.password, password )

    @staticmethod
    def getAllAdmins():
        admins = None
        for user in User.query.order_by( User.id ):
            if ( user.is_admin() ):
                if admins:
                    admins.append( user )
                else:
                    admins = [user]
        return admins

    @staticmethod
    def hasUnverifiedUsers():
        for user in User.query.order_by( User.id ):
            if ( user.is_verified() == False ):
                return True
        return False

    @staticmethod
    def getAllUnverifiedUsers():
        unverifiedUsers = None
        for user in User.query.order_by( User.id ):
            if ( user.is_verified() == False ):
                if unverifiedUsers:
                    unverifiedUsers.append( user )
                else:
                    unverifiedUsers = [user]
        return unverifiedUsers

    def __repr__( self ):
        return '<User %d>' % self.id

    def __str__( self ):
        return 'User #%d: %s' % ( self.id, self.fullname )

class ClassInfo( db.Model ):
    id = db.Column( db.Integer(), primary_key = True )
    classAbbr = db.Column( db.String( 4 ) )
    longName = db.Column( db.String( 256 ) )
    startingID = db.Column( db.Integer )
    currentID = db.Column( db.Integer )

    @staticmethod
    def get( classAbbr ):
        return ClassInfo.query.filter_by( classAbbr = classAbbr ).one()

    def __repr__( self ):
        return '<ClassInfo %r>' % self.id

    def __str__( self ):
        return 'ClassInfo %s (%s): startingID=%d, currentID=%d' % ( self.classAbbr, self.longName, self.startingID, self.currentID )

class Question( db.Model ):
    id = db.Column( db.Integer, primary_key = True )
    classID = db.Column( db.Integer )
    created = db.Column( db.DateTime )
    modified = db.Column( db.DateTime )
    classAbbr = db.Column( db.String( 4 ) )
    quiz = db.Column( db.Integer )
    tags = db.Column( db.String( 256 ) )
    tagsIV = db.Column( db.String( 16 ) )
    tagsComments = db.Column( db.Text )
    tagsCommentsIV = db.Column( db.String( 16 ) )
    instructions = db.Column( db.Text )
    instructionsIV = db.Column( db.String( 16 ) )
    instructionsComments = db.Column( db.Text )
    instructionsCommentsIV = db.Column( db.String( 16 ) )
    question = db.Column( db.Text )
    questionIV = db.Column( db.String( 16 ) )
    questionComments = db.Column( db.Text )
    questionCommentsIV = db.Column( db.String( 16 ) )
    examples = db.Column( db.Text )
    examplesIV = db.Column( db.String( 16 ) )
    examplesComments = db.Column( db.Text )
    examplesCommentsIV = db.Column( db.String( 16 ) )
    hints = db.Column( db.Text )
    hintsIV = db.Column( db.String( 16 ) )
    hintsComments = db.Column( db.Text )
    hintsCommentsIV = db.Column( db.String( 16 ) )
    answer = db.Column( db.Text )
    answerIV = db.Column( db.String( 16 ) )
    answerComments = db.Column( db.Text )
    answerCommentsIV = db.Column( db.String( 16 ) )
    user_id = db.Column( db.Integer, db.ForeignKey( 'user.id' ) )
    # Relationships with other models
    reviewers = db.relationship( 'User', secondary = users_questions, backref = db.backref( 'reviewers', lazy = 'dynamic' ) )
    isOKFlags = db.Column( db.Integer )
    tagTextIsEncrypted = True
    questionTextIsEncrypted = True
    commentTextIsEncrypted = True

    @staticmethod
    def get( id ):
        """ Retrieve a question from the database by raw id. Also flag the question text as being initially encrypted. """
        questions = None
        questions = Question.query.filter_by( id = id )
        if ( ( questions == None ) or ( questions.count() == 0 ) ):
            flash( "Couldn't find any questions in the database with (raw) ID: %d" % id )
            return None
        if ( questions.count() > 1 ):
            flash( "Found more than one question (%d) in the database with (raw) ID: %d" % ( questions.count(), id ) )
        question = questions.one()
        return question

    @staticmethod
    def getUsingClassID( classID ):
        """ Retrieve a question from the database by the id offset by the class id. This is to have questions numbered
            within a class's category - used to generate the id to retrieve a previously generated quiz/exam.
            Also flag the question text as being initially encrypted. """
        questions = None
        questions = Question.query.filter_by( classID = classID )
        if ( ( questions == None ) or ( questions.count() == 0 ) ):
            flash( "Couldn't find any questions in the database with (class) ID: %d" % classID )
            return None
        if ( questions.count() > 1 ):
            flash( "Found more than one question (%d) in the database with (class) ID: %d" % ( questions.count(), classID ) )
        question = questions.one()
        return questions.one()

    def tagsAsSet( self ):
        if self.tags:
            self.decryptTagText()
            result = set()
            if self.tags:
                for tag in self.tags.split( "," ):
                    result.add( tag.strip() )
            return result
        else:
            return "?? NO TAGS ??"

    def shortenedQuestionWithMarkup( self ):
        """ Returned a short..ed version of the (unencrypted) question text with HTML markup """
        if self.question:
            self.decryptQuestionText()
            if ( len( self.question ) < 60 ):
                return convertToHTML( self.question )
            else:
                return convertToHTML( self.question[0:28].strip() ) + "..." + convertToHTML( self.question[-28:].strip() )
        else:
            return "?? NO QUESTION TEXT ??"

    def shortenedDecryptedTags( self ):
        """ Returned a short..ed version of the (unencrypted) tags """
        if self.tags:
            self.decryptTagText()
            if ( len( self.tags ) < 80 ):
                return self.tags
            else:
                return self.tags[0:38].strip() + "..." + self.tags[-38:].strip()
        else:
            return "?? NO TAGS ??"

    def offsetNumberFromClass( self, classInfo ):
        """ Returns the id offset by a class's category (see getUsingClassID above) """
        assert ( type( self.classID ) == type( 1 ) ), "self.classID (%r) != int??" % self.classID
        assert ( type( classInfo.startingID ) == type( 1 ) ), "classInfo.startingID (%r) != int??" % classInfo.startingID
        offsetNumber = ( self.classID - classInfo.startingID )
        assert ( type( offsetNumber ) == type( 1 ) ), "offsetNumber (%r) != int??" % offsetNumber
        return offsetNumber

    def findSimilarQuestions( self ):
        """ Find questions "similar" to this one. Uses quiz # and tags.
            TODO: Union questions with the same tag(s) - right now it's looking for equal tags. """
        existing = []
        tags = self.tagsAsSet()
        instances = Question.query.filter( Question.classAbbr == self.classAbbr, Question.id != self.id, Question.quiz == self.quiz ).order_by( Question.id ).all()
        for instance in instances:
            instanceTags = instance.tagsAsSet()
            if ( len( instanceTags.intersection( tags ) ) > 0 ):
                existing.append( instance )
        return existing
    
    def addReviewer( self, user, isOKFlag, maxReviewers ):
        """ Add a user to a question's "reviewers" as well as set the "is this question OK" flag.
            maxReviewers is necessary to shift out old reviewers and keep the most recent ones. """ 
        if ( self.isOKFlags == None ):  # Initialize flags if none have been set
            self.isOKFlags = 0
        try:
            userIndex = self.reviewers.index( user )
        except ValueError as ex:
            if ( len( self.reviewers ) == maxReviewers ):  # Shift out earliest reviewer and
                discardedUser = self.reviewers[0]
                self.reviewers = self.reviewers[1:]
                print "DISCARDED (overflow) REVIEWER: %s" % discardedUser
                self.isOKFlags = self.isOKFlags >> 1
                userIndex = 2
            else:
                userIndex = len( self.reviewers )
        self.isOKFlags = self.isOKFlags & ~( 1 << userIndex ) | isOKFlag << userIndex  # Set (or clear) the corresponding isOKFlag
        if ( userIndex >= len( self.reviewers ) ):
            self.reviewers.append( user )
        else:
            self.reviewers[userIndex] = user

    @staticmethod
    def addMarkupToQuestionText( question, decryptTags = False, decryptQuestion = False, decryptComments = False ):
        """ Add HTML markup to all of the question text, including tags and comments.
            This is mostly used for: \n -> <br /> as well as replacing the [[image]] tags. """
        convertedQuestion = copy.copy( question )
        overallImagesToCache = set( [] )
        if decryptTags:
            if convertedQuestion.tags:
                convertedQuestion.tags, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.tags ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
        if decryptQuestion:
            if convertedQuestion.instructions:
                convertedQuestion.instructions, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.instructions ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.question:
                convertedQuestion.question, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.question ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.examples:
                convertedQuestion.examples, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.examples ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.hints:
                convertedQuestion.hints, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.hints ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.answer:
                convertedQuestion.answer, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.answer ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
        if decryptComments:
            if convertedQuestion.instructionsComments:
                convertedQuestion.instructionsComments, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.instructionsComments ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.questionComments:
                convertedQuestion.questionComments, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.questionComments ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.examplesComments:
                convertedQuestion.examplesComments, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.examplesComments ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.hintsComments:
                convertedQuestion.hintsComments, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.hintsComments ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
            if convertedQuestion.answerComments:
                convertedQuestion.answerComments, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.answerComments ) )
                overallImagesToCache = overallImagesToCache.union( imagesToCache )
        for filename in overallImagesToCache:
            _, _ = Image.getAndCacheByName( filename )
        return convertedQuestion

    # Encryption and decryption

    @staticmethod
    def copyAndDecryptText( question, decryptTags = True, decryptQuestion = True, decryptComments = True ):
        """ Decrypt all of the question text, including tags and comments. """
        convertedQuestion = copy.copy( question )
        convertedQuestion.decryptText(decryptTags, decryptQuestion, decryptComments )
        return convertedQuestion

    def decryptText( self, decryptTags = True, decryptQuestion = True, decryptComments = True ):
        """ Decrypt all of the question text, including tags and comments. """
        if decryptTags:
            self.decryptTagText()
        if decryptQuestion:
            self.decryptQuestionText()
        if decryptComments:
            self.decryptCommentText()
    
    def decryptTagText(self):
        """ Decrypt a question's tags (if they exist) if they aren't already decrypted. """
        if self.tags:
            if self.tagTextIsEncrypted:
                self.tags = decrypt( self.tags, self.tagsIV )
                self.tagTextIsEncrypted = False
            
    def decryptQuestionText(self):
        """ Decrypt a question's text parts (if they exist) if they aren't already decrypted. """
        if self.questionTextIsEncrypted:
            if self.instructions:
                self.instructions = decrypt( self.instructions, self.instructionsIV )
            if self.question:
                self.question = decrypt( self.question, self.questionIV )
            if self.examples:
                self.examples = decrypt( self.examples, self.examplesIV )
            if self.hints:
                self.hints = decrypt( self.hints, self.hintsIV )
            if self.answer:
                self.answer = decrypt( self.answer, self.answerIV )
            self.questionTextIsEncrypted = False

    def decryptCommentText(self):
        """ Decrypt a question's comments (if they exist) if they aren't already decrypted. """
        if self.commentTextIsEncrypted:
            if self.tagsComments:
                self.tagsComments = decrypt( self.tagsComments, self.tagsCommentsIV )
            if self.instructionsComments:
                self.instructionsComments = decrypt( self.instructionsComments, self.instructionsCommentsIV )
            if self.questionComments:
                self.questionComments = decrypt( self.questionComments, self.questionCommentsIV )
            if self.examplesComments:
                self.examplesComments = decrypt( self.examplesComments, self.examplesIV )
            if self.hintsComments:
                self.hintsComments = decrypt( self.hintsComments, self.hintsCommentsIV )
            if self.answerComments:
                self.answerComments = decrypt( self.answerComments, self.answerCommentsIV )
            self.commentTextIsEncrypted = False

    def encryptText( self, encryptTags = True, encryptQuestion = True, encryptComments = True ):
        """ Encrypt all of the question text, including tags and comments. """
        if ((encryptTags) and (self.tagTextIsEncrypted == False)):
            self.tags, self.tagsIV = encrypt( self.tags )
            self.tagTextIsEncrypted = True
        if ((encryptQuestion) and (self.questionTextIsEncrypted == False)):
            self.tags, self.tagsIV = encrypt( self.tags )
            self.instructions, self.instructionsIV = encrypt( self.instructions )
            self.question, self.questionIV = encrypt( self.question )
            self.examples, self.examplesIV = encrypt( self.examples )
            self.hints, self.hintsIV = encrypt( self.hints )
            self.answer, self.answerIV = encrypt( self.answer )
            self.questionTextIsEncrypted = True
        if ((encryptComments) and (self.commentTextIsEncrypted == False)):
            self.tagsComments, self.tagsCommentsIV = encrypt( self.tagsComments )
            self.instructionsComments, self.instructionsCommentsIV = encrypt( self.instructionsComments )
            self.questionComments, self.questionCommentsIV = encrypt( self.questionComments )
            self.examplesComments, self.examplesCommentsIV = encrypt( self.examplesComments )
            self.hintsComments, self.hintsCommentsIV = encrypt( self.hintsComments )
            self.answerComments, self.answerCommentsIV = encrypt( self.answerComments )
            self.commentTextIsEncrypted = True

    # Generate Quizzes and Exams
    
    @staticmethod
    def generateQuiz( classInfo, quizNumber, cachedQuestions, maxNumberOfQuestions ):
        """ Generate quiz # for a class, using previously cached questions (caller is responsible for these).
            TODO: Find questions with: most reviews, then different tags
            TODO: Modify maxNumberOfQuestions by length of question / time to answer. """
        quizQuestions = []
        # questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            if ( question.quiz == quizNumber ):
                markedUpQuestion = Question.addMarkupToQuestionText( Question.copyAndDecryptText( question, decryptComments = False ) )
                quizQuestions.append( markedUpQuestion )
                if ( len( quizQuestions ) > maxNumberOfQuestions ):
                    break
        return quizQuestions, Question.generateIDFromQuestions( classInfo, quizQuestions )

    @staticmethod
    def generateFinalExam( classInfo, cachedQuestions ):
        """ Generate final exam # for a class, using previously cached questions (caller is responsible for these)
            TODO: Find questions with: most reviews, then different tags
            TODO: Modify maxNumberOfQuestions by length of question / time to answer. """
        examQuestions = []
        # questions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
        for question in cachedQuestions:
            markedUpQuestion = Question.addMarkupToQuestionText( Question.copyAndDecryptText( question, decryptComments = False ) )
            examQuestions.append( markedUpQuestion )
            if ( len( examQuestions ) > 5 ):
                break
        return examQuestions, Question.generateIDFromQuestions( classInfo, examQuestions )

    @staticmethod
    def generateIDFromQuestions( classInfo, questions ):
        """ Generate an ID from quiz question ids.
            1024 questions per quiz possible. Question IDs in the database
            are offsets from the ClassInfo starting IDs. """
        validIDSymbols = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len( validIDSymbols )
        idSymbols = classInfo.classAbbr
        for question in questions:
            idSymbols += '.'
            qid = ( question.classID - classInfo.startingID )
            if ( qid > numIDSymbols ):
                idSymbols += validIDSymbols[id / numIDSymbols]
            idSymbols += validIDSymbols[qid % numIDSymbols]
        return idSymbols

    @staticmethod
    def getQuestionsFromID( idSymbols, addMarkupToQuestionTextToo ):
        """ Retrieve quiz question from an ID. Question IDs in the database
            are offsets from the ClassInfo starting IDs. """
        validIDSymbols = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len( validIDSymbols )
        questions = []
        questionNumbers = idSymbols.split( '.' )
        if ( len( questionNumbers ) < 2 ):
            flash( "ID (%s) doesn't have any question IDs??" % idSymbols, category = "error" )
        else:
            for index in range( 0, len( questionNumbers ) ):
                if ( index == 0 ):
                    try:
                        classInfo = ClassInfo.get( questionNumbers[index] )
                    except Exception as ex:
                        flash ( "idSymbol (%s) isn't a valid class abbreviation." % questionNumbers[index], category = "error" )
                        break
                else:
                    symbol = questionNumbers[index][0]
                    if symbol in validIDSymbols:
                        questionNumber = validIDSymbols.find( symbol )
                        if ( len( questionNumbers[index] ) > 1 ):
                            symbol = questionNumbers[index][1]
                            if symbol in validIDSymbols:
                                questionNumber = questionNumber * numIDSymbols + validIDSymbols.find( symbol )
                            else:
                                flash( "ID '%s' is invalid in code: %s" % ( questionNumbers[index], idSymbols ), category = "warning" )
                                continue
                    else:
                        flash( "ID '%s' is invalid in code: %s" % ( questionNumbers[index], idSymbols ), category = "warning" )
                        continue
                    questionClassID = classInfo.startingID + questionNumber
                    try:
                        question = Question.getUsingClassID( questionClassID )
                        decryptedQuestion = Question.copyAndDecryptText( question, decryptComments = False )
                        if addMarkupToQuestionTextToo:
                            decryptedQuestion = Question.addMarkupToQuestionText( decryptedQuestion, questionOnly = True )
                        questions.append( decryptedQuestion )
                    except Exception as ex:
                        flash ( "ID '%s' isn't a valid question [class] id (%d) for class: %s in code: %s" % ( questionNumbers[index], questionClassID, questionNumbers[index], idSymbols ), category = "warning" )
                        continue
        return questions

    def __repr__( self ):
        return '<Question %r>' % ( self.id )

    def __str__( self ):
        return "Question #%d (classID: %d): %s" % ( self.id, self.classID, self.decryptAndShortenQuestion() )

class Image( db.Model ):
    """ Class to encapsulate the storage and retrieval of images from the database. """
    id = db.Column( db.Integer(), primary_key = True )
    name = db.Column( db.String( 80 ), unique = True )
    data = db.Column( db.LargeBinary( 4096 ), unique = True )

    @staticmethod
    def getByName( filename ):
        images = None
        images = Image.query.filter_by( name = filename )
        if ( ( images == None ) or ( images.count() == 0 ) ):
            flash( "Couldn't find any images in the database with filename: %s" % filename )
            return None
        if ( images.count() > 1 ):
            flash( "Found more than one image (%d) in the database with filename: %s" % filename )
        return images.one()

    @staticmethod
    def getAndCacheByName( filename ):
        path = None
        try:
            data, path = readTempFile( filename )
        except IOError as ex:
            data = None
        if ( data == None ):
            image = Image.getByName( filename )
            if image:
                data = image.data
                if data:
                    path = writeTempFile( filename, data )
        return data, path

    def __repr__( self ):
        return '<Image %r>' % ( self.id )

    def __str__( self ):
        return "Image #%d (size=%d): %s" % ( self.id, len( self.data ), self.name )
    
class History( db.Model ):
    """ A general way to store previously generated data, which, for now, is a workaround for long, 
        clunky IDs to retrieve previously generated quizzes and exams. Class abbreviation (e.g., 9F) and
        quiz number are to aid in retrieval and display. """
 
    id = db.Column( db.Integer(), primary_key = True )
    classAbbr = db.Column( db.String( 4 ) )
    quiz = db.Column( db.Integer )   
    questions = db.relationship( 'Question', secondary = questions_histories, backref = db.backref( 'histories', lazy = 'dynamic' ) )
  
    def __repr__( self ):
        return '<History %r>' % ( self.id )

    def __str__( self ):
        return "History #%d: %r" % ( self.id, questions )
