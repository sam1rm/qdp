import copy
import doctest

from app import db, login_serializer, g_Oracle
from flask import flash
from flask.ext.security import UserMixin, RoleMixin
from werkzeug import generate_password_hash, check_password_hash

from app.utils import convertToHTML, replaceImageTags, readTempFile, writeTempFile

roles_users = db.Table( 'roles_users',
        db.Column( 'users_id', db.Integer(), db.ForeignKey( 'user.id' ) ),
        db.Column( 'roles_id', db.Integer(), db.ForeignKey( 'role.id' ) ) )

users_questions = db.Table( 'users_questions',
        db.Column( 'users_id', db.Integer(), db.ForeignKey( 'user.id' ) ),
        db.Column( 'questions_id', db.Integer(), db.ForeignKey( 'question.id' ) ) )

# TODO: Implement
questions_histories = db.Table( 'questions_histories',
        db.Column( 'questions_id', db.Integer(), db.ForeignKey( 'question.id' ) ),
        db.Column( 'history_id', db.Integer(), db.ForeignKey( 'history.id' ) ) )

# TODO: Implement
images_questions = db.Table( 'images_questions',
        db.Column( 'images_id', db.Integer(), db.ForeignKey( 'image.id' ) ),
        db.Column( 'questions_id', db.Integer(), db.ForeignKey( 'question.id' ) ) )

class Role( db.Model, RoleMixin ):
    """ Stores the various User's roles (for use in the relational table between Roles and Users)
        (e.g., "User," "Admin,") """
    id = db.Column( db.Integer(), primary_key = True )
    name = db.Column( db.String( 80 ), unique = True )
    description = db.Column( db.String( 255 ) )

    def __repr__( self ):
        return '<Role %r>' % self.id

    def __str__( self ):
        return '<Role %r: %s = %s>' % (self.id,self.name,self.description)

class User( db.Model, UserMixin ):
    """ Stores user information, including the password in encrypted form. Also handles session cookies
        for the 'remember me' option. Also keeps track of the Role of the user (e.g. 'Admin') as well as the
        questions that the user has written. """
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
        users = User.query.filter_by( id = uid )
        if ( ( users == None ) or ( users.count() == 0 ) ):
            flash( "Couldn't find any users in the database with (raw) ID: %d" % uid )
            return None
        elif ( users.count() != 1 ):
            flash( "Found more than one user with (raw) ID: %d!" % uid )
        return users.one()

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
        return '<User %r>' % self.id

    def __str__( self ):
        return 'User #%r: %s' % ( self.id, self.fullname )

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
    tagsComments = db.Column( db.Text )
    instructions = db.Column( db.Text )
    instructionsComments = db.Column( db.Text )
    question = db.Column( db.Text )
    questionComments = db.Column( db.Text )
    examples = db.Column( db.Text )
    examplesComments = db.Column( db.Text )
    hints = db.Column( db.Text )
    hintsComments = db.Column( db.Text )
    answer = db.Column( db.Text )
    answerComments = db.Column( db.Text )
    tagsIV = db.Column( db.String( 16 ) )
    questionIV = db.Column( db.String( 16 ) )
    commentsIV = db.Column( db.String( 16 ) )
    user_id = db.Column( db.Integer, db.ForeignKey( 'user.id' ) )
    # Relationships with other models
    reviewers = db.relationship( 'User', secondary = users_questions, backref = db.backref( 'reviewers', lazy = 'dynamic' ) )
    isOKFlags = db.Column( db.Integer )

    @staticmethod
    def get( id ):
        """ Retrieve a question from the database by raw id. """
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
        result = set()
        if self.tags:
            self.decryptTagText()
            if self.tags:
                for tag in self.tags.split( "," ):
                    result.add( tag.lower().strip() )                    
        else:
            result.add( "?? MISSING TAGS ??")
        return result

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

    def retrieveAndDecryptSimilarQuestions( self ):
        """ Find questions "similar" to this one. Uses quiz # and tags.
            TODO: Union questions with the same tag(s) - right now it's looking for equal tags. """
        existing = []
        if self.tags:
            tags = self.tagsAsSet()
            instances = Question.query.filter( Question.classAbbr == self.classAbbr, Question.id != self.id, Question.quiz == self.quiz ).order_by( Question.id ).all()
            for instance in instances:
                instanceTags = instance.tagsAsSet()
                if ( len( instanceTags.intersection( tags ) ) > 0 ):
                    # TODO: FIX!
                    existing.append( instance.makeDecryptedTextVersion() )
        return existing
    
    def calculateRows(self):
        rowCounts={}
        if self.tagsComments:
            rowCounts['tagsComments']=max(2,self.tagsComments.count("\n")+1)
        else:
            rowCounts['tagsComments']=2
        if self.instructions:
            rowCounts['instructions']=max(4,self.instructions.count("\n")+1)
        else:
            rowCounts['instructions']=4
        if self.instructionsComments:
            rowCounts['instructionsComments']=max(4,self.instructionsComments.count("\n")+1)
        else:
            rowCounts['instructionsComments']=4
        if self.question:
            rowCounts['question']=max(4,self.question.count("\n")+1)
        else:
            rowCounts['question']=4
        if self.questionComments:
            rowCounts['questionComments']=max(4,self.questionComments.count("\n")+1)
        else:
            rowCounts['questionComments']=4
        if self.examples:
            rowCounts['examples']=max(4,self.examples.count("\n")+1)
        else:
            rowCounts['examples']=4
        if self.examplesComments:
            rowCounts['examplesComments']=max(4,self.examplesComments.count("\n")+1)
        else:
            rowCounts['examplesComments']=4
        if self.hints:
            rowCounts['hints']=max(4,self.hints.count("\n")+1)
        else:
            rowCounts['hints']=4
        if self.hintsComments:
            rowCounts['hintsComments']=max(4,self.hintsComments.count("\n")+1)
        else:
            rowCounts['hintsComments']=4
        if self.answer:
            rowCounts['answer']=max(4,self.answer.count("\n")+1)
        else:
            rowCounts['answer']=4
        if self.answerComments:
            rowCounts['answerComments']=max(4,self.answerComments.count("\n")+1)
        else:
            rowCounts['answerComments']=4
        return rowCounts
    
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

    def makeMarkedUpVersion( self ):
        """ Add HTML markup to all of the question text, including tags and comments.
            This is mostly used for: \n -> <br /> as well as replacing the [[image]] tags. """
        convertedQuestion = self.makeDecryptedTextVersion()
        overallImagesToCache = set( [] )
        if convertedQuestion.tags:
            convertedQuestion.tags, imagesToCache = replaceImageTags( convertToHTML( convertedQuestion.tags ) )
            overallImagesToCache = overallImagesToCache.union( imagesToCache )
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
            _ = Image.getAndCacheByName( filename )
        return convertedQuestion

    # Encryption and decryption

    def makeDecryptedTextVersion(self, decryptTags = True, decryptQuestion = True, decryptComments = True ):
        """ Decrypt all of the question text, including tags and comments. """
        convertedQuestion = copy.copy( self )
        convertedQuestion.decryptText( decryptTags, decryptQuestion, decryptComments )
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
            if g_Oracle.isEncrypted(self.tags):
                self.tags = g_Oracle.decrypt( self.tags, self.tagsIV )
            
    def decryptQuestionText(self):
        """ Decrypt a question's text parts (if they exist) if they aren't already decrypted. """
        if g_Oracle.isEncrypted(self.question):
            if self.instructions:
                self.instructions = g_Oracle.decrypt( self.instructions, self.questionIV )
            if self.question:
                self.question = g_Oracle.decrypt( self.question, self.questionIV )
            if self.examples:
                self.examples = g_Oracle.decrypt( self.examples, self.questionIV )
            if self.hints:
                self.hints = g_Oracle.decrypt( self.hints, self.questionIV )
            if self.answer:
                self.answer = g_Oracle.decrypt( self.answer, self.questionIV )
            self.questionTextIsEncrypted = False

    def decryptCommentText(self):
        """ Decrypt a question's comments (if they exist) if they aren't already decrypted. """
        if g_Oracle.isEncrypted(self.questionComments):
            if self.tagsComments:
                self.tagsComments = g_Oracle.decrypt( self.tagsComments, self.commentsIV )
            if self.instructionsComments:
                self.instructionsComments = g_Oracle.decrypt( self.instructionsComments, self.commentsIV )
            if self.questionComments:
                self.questionComments = g_Oracle.decrypt( self.questionComments, self.commentsIV )
            if self.examplesComments:
                self.examplesComments = g_Oracle.decrypt( self.examplesComments, self.commentsIV )
            if self.hintsComments:
                self.hintsComments = g_Oracle.decrypt( self.hintsComments, self.commentsIV )
            if self.answerComments:
                self.answerComments = g_Oracle.decrypt( self.answerComments, self.commentsIV )
            self.commentTextIsEncrypted = False

    def encryptText( self, encryptTags = True, encryptQuestion = True, encryptComments = True ):
        """ Encrypt all of the question text, including tags and comments. """
        if ((encryptTags) and (g_Oracle.isEncrypted(self.tags) == False)):
            iv, self.tagsIV = g_Oracle.generateIV()
            self.tags = g_Oracle.encrypt( self.tags, iv )
            self.tagTextIsEncrypted = True
        if ((encryptQuestion) and (g_Oracle.isEncrypted(self.question) == False)):
            iv, self.questionIV = g_Oracle.generateIV()
            self.instructions = g_Oracle.encrypt( self.instructions, iv )
            self.question = g_Oracle.encrypt( self.question, iv )
            self.examples = g_Oracle.encrypt( self.examples, iv )
            self.hints = g_Oracle.encrypt( self.hints, iv )
            self.answer = g_Oracle.encrypt( self.answer, iv )
            self.questionTextIsEncrypted = True
        if ((encryptComments) and (g_Oracle.isEncrypted(self.questionComments) == False)):
            iv, self.commentsIV = g_Oracle.generateIV()
            self.tagsComments = g_Oracle.encrypt( self.tagsComments, iv )
            self.instructionsComments = g_Oracle.encrypt( self.instructionsComments, iv )
            self.questionComments = g_Oracle.encrypt( self.questionComments, iv )
            self.examplesComments = g_Oracle.encrypt( self.examplesComments, iv )
            self.hintsComments = g_Oracle.encrypt( self.hintsComments, iv )
            self.answerComments = g_Oracle.encrypt( self.answerComments, iv )
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
                markedUpQuestion = question.makeMarkedUpVersion()
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
            markedUpQuestion = question.makeMarkedUpVersion()
            examQuestions.append( markedUpQuestion )
            if ( len( examQuestions ) > 5 ):
                break
        return examQuestions, Question.generateIDFromQuestions( classInfo, examQuestions )

    @staticmethod
    def generateIDFromQuestions( classInfo, questions ):
        """ Generate an ID from quiz question ids.
            1024 questions per quiz possible. Question IDs in the database
            are offsets from the ClassInfo starting IDs. 
            TODO: Turn this into a History instead. """
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
    def getQuestionsFromID( idSymbols ):
        """ Retrieve quiz question from an ID. Question IDs in the database
            are offsets from the ClassInfo starting IDs.
            TODO: Turn this into a History instead. """
        validIDSymbols = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        numIDSymbols = len( validIDSymbols )
        questions = []
        classInfo = None
        questionNumbers = idSymbols.split( '.' )
        if ( len( questionNumbers ) < 2 ):
            flash( "ID (%s) doesn't have any question IDs??" % idSymbols, category = "error" )
        else:
            classAbbr = questionNumbers[0].upper()
            del questionNumbers[0]
            try:
                classInfo = ClassInfo.get( classAbbr )
            except Exception as _:
                flash ( "idSymbol (%s) isn't a valid class abbreviation." % classAbbr, category = "error" )
                return None, None
            for index in range( 0, len( questionNumbers ) ):
                questionNumber = 0
                while (len(questionNumbers[index])>0):
                    symbol = questionNumbers[index][0].upper()
                    if symbol in validIDSymbols:
                        questionNumber = questionNumber * numIDSymbols + validIDSymbols.find( symbol )
                    else:
                        flash( "Invalid code '%s' in: %s" % ( questionNumbers[index][0], idSymbols ), category = "warning" )
                        break
                    questionNumbers[index] = questionNumbers[index][1:]
                questionClassID = classInfo.startingID + questionNumber
                try:
                    question = Question.getUsingClassID( questionClassID )
                except Exception as ex:
                    flash ( "ID '%s' isn't a valid question [class] id (%d) for class: %s in code: %s" % ( questionNumbers[index], questionClassID, questionNumbers[index], idSymbols ), category = "warning" )
                    continue
                decryptedQuestion = question.makeMarkedUpVersion()
                questions.append( decryptedQuestion )
        return questions, classInfo

    def __repr__( self ):
        return '<Question %r>' % ( self.id )

    def __str__( self ):
        return "Question #%d (classID: %d): %s" % ( self.id, self.classID, self.decryptAndShortenQuestion() )

class Image( db.Model ):
    """ Class to encapsulate the storage and retrieval of images from the database. 
        TODO: Categorize (for speed) by classAbbr.
        TODO: Handle PNGs """
    id = db.Column( db.Integer(), primary_key = True )
    name = db.Column( db.String( 80 ), unique = True )
    classAbbr = db.Column( db.String( 4 ) )
    data = db.Column( db.LargeBinary( 4096 ), unique = True )
    dataIV = db.Column( db.String( 16 ) )
    cachePath = None

    @staticmethod
    def get( uid ):
        image = Image.query.filter_by( id = uid )
        if ( ( image == None ) or ( image.count() == 0 ) ):
            flash( "Couldn't find any image in the database with (raw) ID: %d" % uid )
            return None
        elif ( image.count() != 1 ):
            flash( "Found more than one user with (raw) ID: %d!" % uid )
        return image.one()
    
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
        """ Get image from cache if it exists, if not, get it from the database and cache it (to a temporary file). """
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
                    image.cacheByName()
        return data
    
    @staticmethod
    def imageFromUploadedFile(file, filepath, humanReadableName, classAbbr):
        file.save(filepath)
        fref = open(filepath,"rb")
        data = fref.read()
        fref.close()
        dataIV,dataIV64 = g_Oracle.generateIV();
        image = Image(name=humanReadableName, classAbbr=classAbbr, data=g_Oracle.encrypt(data,dataIV), dataIV=dataIV64)
        return image

    def cacheByName( self ):
        """ Write data to /path/to/tmp/filename (and store the generated path) """
        self.cachePath = writeTempFile( self.name, self.data )

    def __repr__( self ):
        return '<Image %r>' % ( self.id )

    def __str__( self ):
        return "Image #%d: %s (cachePath=%s) (size=%d)" % ( self.id, self.name, self.cachePath, len( self.data ) )
    
class History( db.Model ):
    """ A general way to store previously generated data, which, for now, is a workaround for long, 
        clunky IDs to retrieve previously generated quizzes and exams. Class abbreviation (e.g., 9F) and
        quiz number are to aid in retrieval and display.
        TODO: Implement """
    id = db.Column( db.Integer(), primary_key = True )
    classAbbr = db.Column( db.String( 4 ) )
    quiz = db.Column( db.Integer )   
    questions = db.relationship( 'Question', secondary = questions_histories, backref = db.backref( 'histories', lazy = 'dynamic' ) )
  
    def __repr__( self ):
        return '<History %r>' % ( self.id )

    def __str__( self ):
        return "History #%d: %r" % ( self.id, questions )
