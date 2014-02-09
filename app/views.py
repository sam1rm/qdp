# === Imports ===

import datetime
import os
import random
import subprocess
from app import app, db, lm, login_serializer, mail
from app.forms import QuestionForm, ReviewQuestionForm, ReportForm
from app.models import User, Role, ClassInfo, Question, Image
from app.utils import makeTempFileResp
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import current_user, login_required
from flask.ext.mail import Message
from flask.ext.principal import Permission, RoleNeed, UserNeed, identity_loaded
from flask.ext.security import SQLAlchemyUserDatastore
from flask.helpers import get_flashed_messages
from werkzeug import secure_filename

# === Globals ===

g_CachedQuestions = []
g_HerokuPushVersion = None

# Create a permission with a single Need, in this case a RoleNeed.
user_permission = Permission( RoleNeed( 'user' ) )
admin_permission = Permission( RoleNeed( 'admin' ) )

# === Constants ===

CLASS_ABBR_KEY = 'classAbbr'

# === View Code ===

@app.route( '/' )
@login_required
def index():
    """ Top level site location. Displays additional buttons for admin: Verify users (if there
        are any), and provide additional administration. """
    #app.logger.debug("user=g.user")
    user = g.user
    #app.logger.debug("user.is_verified()")
    if user.is_verified():
        global g_HerokuPushVersion
        if not g_HerokuPushVersion:
            fref=open("version.txt")
            g_HerokuPushVersion = fref.readline()[:-1]
        # imageFileURL = url_for( 'static', filename = 'img/possibly47abc.png' )
        #app.logger.debug("render_template")
        return render_template( 'index.html',
            user = user,
            isAdmin = user.is_admin(),
            hasUnverifiedUsers = ( user.is_admin() and User.hasUnverifiedUsers() ),  # redundant on purpose
            help = 'helpMain',
            isDebugging = app.config['DEBUG'],
            version = g_HerokuPushVersion )
    else:
        #app.logger.debug("unverifiedUser")
        return redirect( url_for( 'unverifiedUser' ) )

@app.route( '/helpMain' )
@login_required
@user_permission.require()
def helpMain():
    """ Help page associated with the main page.
        TODO: Make help dynamic (e.g. __page__Help.html)"""
    return render_template( 'helpMain.html', title = "SAMPLE HELP PAGE" )

# CHOOSERS

@app.route( '/chooseClass' )
@login_required
@user_permission.require()
def chooseClass():
    """ "Funneling" location to chose a class for a specific mode (write, edit, review) """
    argMode = request.args.get( 'mode' )
    if argMode:
        session['mode'] = argMode
        return render_template( 'chooseClass.html', title = session['mode'] + ": Choose Class" )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )

@app.route( '/chooseQuestionToEdit' )
@login_required
@user_permission.require()
def chooseQuestionToEdit():
    """ Primary point for editing a question which begins with choosing questions that
        exist for a previously chosen class.
        TODO: Allow admins to edit _all_ questions. """
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        user = g.user
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        if (user.is_admin()):
            questions = Question.query.filter( Question.classAbbr == session[CLASS_ABBR_KEY] ).order_by( Question.id ).all()
        else:
            questions = Question.query.filter( Question.user_id == user.id, Question.classAbbr == session[CLASS_ABBR_KEY] ).order_by( Question.id ).all()
        if ( len( questions ) > 0 ):
                # TODO: This is SUCH a hack .. clean up encrypted synchronization!
            return render_template( 'chooseQuestion.html', questions = questions, \
                                   title = "Choose Question to Edit for %s (%s)" % (classInfo.classAbbr, classInfo.longName ))
        else:
            flash( "You (%s) don't have any questions to edit for %s (%s)!" % ( currentUserFirstName(), classInfo.classAbbr,classInfo.longName ) )
            return redirect( url_for( 'chooseClass', mode = session['mode']))
    elif 'mode' in session:
        flash( "Please choose a class first." )
        return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )
    
@app.route( '/chooseQuiz' )
@login_required
@admin_permission.require()
def chooseQuiz():
    """ Choose from existing unique quiz numbers available
        TODO: Super-inefficient, but tries to cache questions for a generated quiz... """
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        global g_CachedQuestions
        quizzesFound = set()
        g_CachedQuestions = Question.query.filter( Question.classAbbr == session[CLASS_ABBR_KEY] ).all()
        for question in g_CachedQuestions:
            quizzesFound.add( question.quiz )
        return render_template( 'chooseQuiz.html', quizzes = quizzesFound, finalExamAvailable = ( len( quizzesFound ) > 0 ), title = "Choose Quiz for " + session[CLASS_ABBR_KEY] + " (" + classInfo.longName + ")" )
    elif 'mode' in session:
        flash( "Please choose a class first." )
        return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )
    
# Media upload
    
@app.route( "/manageMedia" )
@login_required
@user_permission.require()
def manageMedia():
    """ Display uploaded media files, or upload a new one. 
        TODO: Filter (optimization) by classAbbr. """
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        images = []
        instances = Image.query.filter(Image.classAbbr == session[CLASS_ABBR_KEY]).order_by( Image.id ).all()
        for instance in instances:
            try:
                instance.cacheByName()
            except Exception as ex:
                flash(instance.name + ": " +  str(ex))
            images.append( instance )
        if ( len( images ) > 0 ):
            return render_template('manageMedia.html', \
                                   title="Manage Media for " + session[CLASS_ABBR_KEY] + " (" + classInfo.longName + ")", \
                                   imagesToDisplay = images, \
                                   isDebugging = app.config['DEBUG'] )
        else:
            flash( "%s, you don't have any images to edit for %s!" % ( currentUserFirstName(), classInfo ) )
    elif 'mode' in session:
        flash( "Please choose a class first." )
        return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )
    
@app.route( "/uploadMedia", methods=['GET', 'POST'] )
@login_required
@user_permission.require()
def uploadMedia():
    """ Upload a file (image), encrypt it, and store it in the database. """
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        if request.method == 'POST':
                file = request.files['file']
                humanReadableName = request.form['name']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image = Image.imageFromUploadedFile(file, filepath, humanReadableName, classInfo.classAbbr)
                    db.session.add(image)
                    db.session.commit()
                    flash('Saved: ' + filename)
                    return redirect(url_for('manageMedia', filename=filename))
                else:
                    flash( "Invalid upload (file). Only accepting (extensions): "+str(app.config['ALLOWED_EXTENSIONS']))
                    return redirect( url_for( 'manageMedia' ) )
        else:
            return render_template('uploadMedia.html', allowedFileTypes = app.config['ALLOWED_EXTENSIONS'], title="Upload File (Image)")
    elif 'mode' in session:
        flash( "Please choose a class first." )
        return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.')[-1].lower() in app.config['ALLOWED_EXTENSIONS']

# CHOSE-ERS <-- Steps following choosers (above)

@app.route( '/choseClass' )
@login_required
@user_permission.require()
def choseClass():
    """ Once a class is chosen (above), redirect to the mode's page (etc. 'write'->editQuestion()) """
    if 'mode' in session:
        session[CLASS_ABBR_KEY] = request.args.get( CLASS_ABBR_KEY ) # Store the passed arg 'class abbreviate' in the session
        if ( session['mode'] == "Write" ):
            return redirect( url_for( 'writeNewQuestion' ) )
        elif ( session['mode'] == "Edit" ):
            return redirect( url_for( 'chooseQuestionToEdit' ) )
        elif ( session['mode'] == "Review" ):
            return redirect( url_for( 'requestReviewQuestion' ) )
        elif ( session['mode'] == "Generate" ):
            return redirect( url_for( 'chooseQuiz' ) )
        elif ( session['mode'] == "Media" ):
            return redirect( url_for( 'manageMedia' ) )
        else:
            raise Exception( "Unknown mode choice: %s" % ( session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )

@app.route( '/writeNewQuestion' )
@login_required
@user_permission.require()
def writeNewQuestion():
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        question = Question( created = datetime.datetime.now(), classAbbr = session[CLASS_ABBR_KEY], classID = classInfo.currentID )
        db.session.add( question )
        classInfo.currentID = classInfo.currentID + 1
        db.session.merge( classInfo )
        db.session.commit()
        return redirect( url_for( "editQuestion", questionID = question.id ) )
    else:
        flash( "Please choose a class first." )
    return redirect( url_for( "chooseClass", mode = session['mode'] ) )

@app.route( '/editQuestion')
@login_required
@user_permission.require()
def editQuestion():
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        rawQuestionIDAsString = request.args.get( 'questionID' )
        assert rawQuestionIDAsString, "rawQuestionID wasn't passed to editQuestion??"
        question = Question.get( int( rawQuestionIDAsString ) )
        if question:  # Can be None if there was a problem retrieving this question
            question.decryptText()
            rowCounts = question.calculateRows()
            # TODO: Handle bad questions (errors on next line) gracefully!
#            similarQuestions = question.retrieveAndDecryptSimilarQuestions()
            form = QuestionForm( request.form, question )
            return render_template( 'editQuestion.html', form = form, \
#                                    similarQuestionsToDisplay = similarQuestions, \
                                    questionToDisplay = question, \
                                    rowCountsToDisplay = rowCounts, \
                                    title = "%s Question #%d For %s" % \
                                        ( session['mode'], ( question.offsetNumberFromClass( classInfo ) + 1 ), \
                                    classInfo.longName ) )
        else:
            flash("Unable to find Question ID: "+rawQuestionIDAsString)
            return redirect( url_for( 'chooseQuestionToEdit' ) )
    else:
        flash( "Please choose a class first." )
    return redirect( url_for( "chooseClass", mode = session['mode'] ) )

@app.route( '/saveQuestion', methods = ['POST'] )
@login_required
@user_permission.require()
def saveQuestion():
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        assert classInfo, "classInfo wasn't already stored for saveQuestion??"
        rawQuestionIDAsString = request.args.get( 'questionID' )
        assert rawQuestionIDAsString, "rawQuestionID wasn't passed to saveQuestion??"
        question = Question.get( int( rawQuestionIDAsString ) )
        if request.method == 'POST':
            form = QuestionForm( request.form, question )
            if ( request.form['button'] == 'delete' ):
                # TODO: Add confirmation!
                db.session.delete( question )
                if ( ( question.classID + 1 ) == classInfo.currentID ):
                    classInfo.currentID = classInfo.currentID - 1
                    db.session.merge( classInfo )
                db.session.commit()
                flash( 'Question #%d deleted.' % ( question.offsetNumberFromClass( classInfo ) + 1 ) )
                return redirect( url_for( "index" ) )
            elif form.validate():
                form.populate_obj( question )
                assert question.id == int( rawQuestionIDAsString ), "question.id should be the same as int( rawQuestionIDAsString )!"
                question.modified = datetime.datetime.now()
                question.encryptText( encryptComments = False )
                db.session.merge( question )
                db.session.commit()
                flash( 'Question #%d saved.' % ( question.offsetNumberFromClass( classInfo ) + 1 ) )
                session['mode'] = 'Edit'
                return redirect( url_for( "editQuestion", questionID = question.id ) )
            else:
                flash( 'There was a problem handling the form POST (save) for Question ID:%d' % ( question.id ) )
    else:
        flash( 'There was a problem getting the classInfo for the session.' )
    return redirect( url_for( "editQuestion", questionID = question.id ) )

@app.route( '/requestReviewQuestion' )
@login_required
@user_permission.require()
def requestReviewQuestion():
    """ Retrieve a question that's been least reviewed for a chosen class.
        Least reviewed is found by looking for 0, 1, 2, etc. up to 10 prior reviews."""
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        if ( Question.query.filter( Question.classAbbr == session[CLASS_ABBR_KEY] ).count() > 0 ):
            questionsToReview = Question.query.filter( Question.classAbbr == session[CLASS_ABBR_KEY] ).all()
            leastReviewed = app.config["REVIEWS_BEFORE_OK_TO_USE"]
            assert( leastReviewed > -1 )
            for questionToReview in questionsToReview:
                numTimesReviewed = len( questionToReview.reviewers )
                if ( numTimesReviewed < leastReviewed ):
                    leastReviewed = numTimesReviewed
            leastReviewedQuestionsToReview = []
            for questionToReview in questionsToReview:
                numTimesReviewed = len( questionToReview.reviewers )
                if ( numTimesReviewed == leastReviewed ):
                    leastReviewedQuestionsToReview.append( questionToReview )
                # We have a list of least reviewed questions, pick one at random.
            questionToReview = random.choice( leastReviewedQuestionsToReview )
            return redirect( url_for( 'reviewQuestion', questionID = questionToReview.id ) )
        flash( 'There are no questions to review for class: ' + classInfo.longName )
    else:
        flash( "Please choose a class first." )
    return redirect( url_for( 'chooseClass', mode = session['mode'] ) )

@app.route( '/reviewQuestion', methods = ['POST', 'GET'] )
@login_required
@user_permission.require()
def reviewQuestion():
    """ Handler for the "Review question" functionality. Redisplays the original question text as
        uneditable and includes editable comment sections.
        TODO: Show/hide comment sections"""
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        # Handle a question review form
        reviewQuestionIDAsString = request.args.get( 'questionID' )
        assert( reviewQuestionIDAsString ), "reviewQuestionID wasn't passed to reviewQuestion"
        question = Question.get( int( reviewQuestionIDAsString ) )
        if question:
            question.decryptCommentText()
            rowCounts = question.calculateRows()
            #similarQuestions = question.retrieveAndDecryptSimilarQuestions()
            form = ReviewQuestionForm( request.form, question )
            if request.method == 'POST':
                form.populate_obj( question )
                question.modified = datetime.datetime.now()
                question.encryptText( )
                if ( request.form['button'] == 'needswork' ):
                    question.addReviewer( g.user, False, app.config['REVIEWS_BEFORE_OK_TO_USE'] )
                    db.session.commit()
                    return redirect( url_for( "requestReviewQuestion" ) )
                else:
                    question.addReviewer( g.user, True, app.config['REVIEWS_BEFORE_OK_TO_USE'] )
                    if form.validate():
                        db.session.merge( question )
                        db.session.commit()
                        return redirect( url_for( "requestReviewQuestion" ) )
                    else:
                        flash( 'There was a problem handling the form POST for Question ID:%d' % ( question.id ) )
            reviewersSaidOK = [0]  # loop.index starts index at 1
            for n in range( len( question.reviewers ) ):
                reviewersSaidOK.append( question.isOKFlags & 1 << n )
            return render_template( 'reviewQuestion.html', \
                                    form = form, \
                                    #similarQuestionsToDisplay = similarQuestions, \
                                    questionToDisplay = question.makeMarkedUpVersion(), \
                                    rowCountsToDisplay = rowCounts, \
                                    title = "%s Question #%d For %s (%s)" % \
                                        ( session['mode'], ( question.offsetNumberFromClass( classInfo ) + 1 ), session[CLASS_ABBR_KEY], classInfo.longName ), \
                                    reviewersSaidOKToDisplay = reviewersSaidOK )
        else:
            flash( "Couldn't find question ID: %s??" % reviewQuestionIDAsString )
    elif 'mode' in session:
        flash( "Please choose a class first." )
        return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )

@app.route( '/gatherSimilarQuestionsFromTags', methods = ['POST'] )
@login_required
def gatherSimilarQuestionsFromTags():
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        assert(request.form[ 'questionID' ] and request.form[ 'tags' ] and request.form[ 'quiz' ])  # Ensure that this data has been passed by the Javascript
        classAbbr = session[CLASS_ABBR_KEY]
        assert(classAbbr)
        thisQuestionIDAsString = request.form[ 'questionID' ]
        thisQuestionID = int(thisQuestionIDAsString)
        tags=request.form['tags']
        quizAsString=request.form['quiz']
        quiz=int(quizAsString)
        similarQuestions = Question.retrieveAndDecryptSimilarQuestions( thisQuestionID, tags, classAbbr, quiz )
        return render_template( 'similarQuestions.html', similarQuestionsToDisplay=similarQuestions )
    elif 'mode' in session:
            flash( "Please choose a class first." )
            return redirect( url_for( 'chooseClass', mode = session['mode'] ) )
    else:
        flash( "Please choose a task (e.g., 'review') first." )
        return redirect( url_for( 'index' ) )
        
@app.route( '/generateQuiz' )
@login_required
@admin_permission.require()
def generateQuiz():
    """ Generate a printable quiz (see Question.generateQuiz for more information). Utilizes questions
    that were previously cached when choosing which quiz to generate (See chooseQuiz (above) for more 
    information. The quiz itself is rendered on a new page (to ease printing). """ 
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
        if g_CachedQuestions:
            quizNumber = request.args.get( 'quizID' )
            assert quizNumber, "Generate quiz without a quiz number??"
            generatedQuiz, generatedID = Question.generateQuiz( classInfo, int( quizNumber ), g_CachedQuestions, app.config['MAX_NUMBER_OF_QUESTIONS'] )
            return render_template( 'generatedQuizOrExam.html', quizNumberToDisplay = quizNumber, generatedIDToDisplay = generatedID, \
                               generatedQuestionsToDisplay = generatedQuiz, classInfoToDisplay = classInfo )
        else:
            flash( "Please select a quiz first." )
            return redirect( url_for( 'chooseQuiz' ) )
    else:
        flash( "Please choose a class first." )
    return redirect( url_for( 'chooseClass', mode = session['mode'] ) )

@app.route( '/generateExam' )
@login_required
@admin_permission.require()
def generateExam():
    """ Very similar to generateQuiz (above), except uses Question.generateFinalExam """
    if ((CLASS_ABBR_KEY in session) and (session[CLASS_ABBR_KEY])):
        if g_CachedQuestions:
            classInfo = ClassInfo.get( session[CLASS_ABBR_KEY] )
            generatedExam, generatedID = Question.generateFinalExam( classInfo, g_CachedQuestions )
            return render_template( 'generatedQuizOrExam.html', quizNumberToDisplay = 0,\
                                    generatedIDToDisplay = generatedID, \
                                    generatedQuestionsToDisplay = generatedExam, \
                                    classInfoToDisplay = classInfo )
        else:
            flash( "Please select a quiz # or final first." )
            return redirect( url_for( 'chooseQuiz' ) )
    else:
        flash( "Please choose a class first." )
    return redirect( url_for( 'chooseClass', mode = session['mode'] ) )

@app.route( "/retrieveQuizOrExam", methods = ['POST', 'GET'] )
@login_required
@admin_permission.require()
def retrieveQuizOrExam():
    """ Retrieve and render a previous quiz or final exam given a code that is displayed on generated quizzes or finals.
        TODO: Fix "Quiz" or "Final Exam" titles """
    if request.method == 'POST':
        code = request.form['code']
        questions, classInfo = Question.getQuestionsFromID( code  )
        messages = get_flashed_messages()
        if ( len( messages ) == 0 ):
            if ( len( questions ) == 0 ):
                flash ( "No valid questions found for code: %s??" % code )
                return redirect( url_for( 'retrieveQuizOrExam' ) )
            return render_template( 'generatedQuizOrExam.html', generatedIDToDisplay = code, \
                                    generatedQuestionsToDisplay = questions, classInfoToDisplay = classInfo )
#         else: # Re-push the flash messages (get_flashed_messages remove current flashes
#             for message in messages:
#                 flash(message)
    return render_template( 'retrieveQuizOrExam.html' )

@app.route( "/imageStatistics" )
@login_required
@user_permission.require()
def imageStatistics():
    rawImageIDAsString = request.args.get( 'imageID' )
    assert rawImageIDAsString, "rawImageIDAsString wasn't passed to imageStatistics??"
    image = Image.get( int( rawImageIDAsString ) )
    if image:  # Can be None if there was a problem retrieving this image
        return render_template( 'imageStatistics.html', title = "Image Statistics for "+image.name, imageToDisplay = image)
    else:
        flash("Unable to find Image ID: "+rawImageIDAsString)
        return redirect( url_for( 'manageMedia' ) )
    
# ADMIN

@app.route( "/adminDatabaseReset" )
@login_required
@admin_permission.require()
def adminDatabaseReset():
    import db_reset
    messageList = []
#     for entry in Question.query.all():
#         messageList.append( "Deleting Question id: %d (class id: %d) (%s)" % ( entry.id, entry.classID, entry.shortenedDecryptedQuestionWithMarkup() ) )
#         db.session.delete( entry )
#     for entry in User.query.filter( User.fullname != "Glenn Sugden" ).all():
#         messageList.append( "Deleting User id: %d (%s)" % ( entry.id, entry.fullname ) )
#         db.session.delete( entry )
#     for entry in ClassInfo.query.all():
#         messageList.append( "Resetting class ids for: %s (id: %d)" % ( entry.longName, entry.id ) )
#         entry.currentID = entry.startingID
#     db.session.commit()
    db_reset.resetDatabase(db)
    messageList.append( "...done!" )
    return render_template( 'adminOutput.html', title = "Admin. - Database Reset", messagesToDisplay = messageList )

@app.route( "/adminTesting" )
@login_required
@admin_permission.require()
def adminTesting():
    messages = []
    image1=Image.getAndCacheByName("9f.3.1.gif")
    messages.append(image1.cachePath)
    image2=Image.getAndCacheByName("9f.3.1.jpg")
    messages.append(path2.cachePath)
    try:
        p = subprocess.Popen(["ls","/tmp"], stdout=subprocess.PIPE)
        result = p.communicate()[0]
        app.logger.debug(result)
        messages.append(result)
    except OSError as ex:
        print "OSError({0}): {1}".format(ex.errno, ex.strerror)
    messages.append(app.config['UPLOAD_FOLDER'])
    return render_template("adminTesting.html", imagesToDisplay = [path1,path2], messageToDisplay = messages)

@app.route( "/reporting" )
def reporting():
    returnTo = request.args.get( 'returnTo' )
    form = ReportForm(who=currentUserFirstName(),when=datetime.datetime.now())
    return render_template("reporting.html", form=form, returnToParam = returnTo)

@app.route( "/sendOrDeleteReport", methods = ['POST'] )
def sendOrDeleteReport():
    returnTo = request.args.get( 'returnTo' )
    if request.method == 'POST':
        if ( request.form['button'] == 'delete' ):
            flash( 'Report cancelled')
        else:
            msg = Message("QDP BUG REPORT",
                          body="Who: %s\nWhen: %s\nWhere: %s\nReport: %s\n\nSesson: %s" % \
                            (request.form['who'], request.form['when'], returnTo, request.form['report'], session),
                          sender=g.user.email,
                          recipients=["headcrash@berkeley.edu"])
            mail.send(msg)
            flash( 'Report sent! Thank you!')
    #return redirect( returnTo )
    return redirect( url_for( 'index' ) ) # Return to top, as request.args may be incorrect at this point (e.g. reviewQuestion and questionID)

# UTILITES

@app.route( "/tmp/<path:path>" )
def tempPath( path ):
    ''' Shiv (to utils) to handle tmp/FILE URL requests (used for images). '''
    resp = makeTempFileResp( path )
    return resp

def currentUserFirstName():
    """ Helper function to return the full name associated with the currently logged in user.
        TODO: Replaced with email, for now, because the registration module doesn't yet ask for full name. """
    if g.user:
        if g.user.email:
            return g.user.email
        else:
#         if g.user.fullname:
#             return g.user.fullname.split( " " )[0]
#         else:
            return "?? anonymous ??"
    return "?? NO GLOBAL USER ??"

# SECURITY

@app.route( "/verifyUsers" )
@login_required
@admin_permission.require()
def verifyUsers():
    """ Admin page for verifying users that have successfully registered. """
    unverifiedUsers = User.getAllUnverifiedUsers()
    return render_template( 'verifyUsers.html', unverifiedUsers = unverifiedUsers )

@app.route( "/verifyingUser" )
@login_required
@admin_permission.require()
def verifyingUser():
    idAsString = request.args.get( 'id' )
    assert idAsString, "ID wasn't passed to verifyingUser??"
    user = User.query.filter( User.id == int( idAsString ) ).first()
    if user:
        if ( user.is_verified() == False ):
            user_datastore = SQLAlchemyUserDatastore( db, User, Role )
            default_role = user_datastore.find_or_create_role( 'user' )
            user_datastore.add_role_to_user( user, default_role )
            db.session.merge( user )
            db.session.commit()
        else:
            flash( "User ID %s is already verified?" % ( idAsString ) )
    else:
        flash( "Couldn't find User ID %s to verify?" % ( idAsString ) )
    return redirect( url_for( 'verifyUsers' ) )

@app.route( "/unverifiedUser" )
@login_required
def unverifiedUser():
    return render_template( 'unverifiedUser.html',
        admins = User.getAllAdmins() )

@lm.user_loader
def load_user( uid ):
    return User.get( int( uid ) )

@app.before_request
def before_request():
    g.user = current_user

@identity_loaded.connect_via( app )
def on_identity_loaded( sender, identity ):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr( current_user, 'id' ):
        identity.provides.add( UserNeed( current_user.id ) )

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr( current_user, 'roles' ):
        for role in current_user.roles:
            identity.provides.add( RoleNeed( role.name ) )

# This processor is added to only the register view
# @security.register_context_processor
# def security_register_processor():
#     app.logger.debug("security_register_processor")

def generate_csrf_token():
    app.logger.debug( "generate_csrf_token" )
    if '_csrf_token' not in session:
        session['_csrf_token'] = app.config['SECRET_KEY']
    return session['_csrf_token']

@lm.token_loader
def load_token( token ):
    """
    Flask-Login token_loader callback.
    The token_loader function asks this function to take the token that was
    stored on the users computer process it to check if its valid and then
    return a User Object if its valid or None if its not valid.
    """

    # The Token itself was generated by User.get_auth_token.  So it is up to
    # us to known the format of the token data itself.

    # The Token was encrypted using itsdangerous.URLSafeTimedSerializer which
    # allows us to have a max_age on the token itself.  When the cookie is stored
    # on the users computer it also has a exipry date, but could be changed by
    # the user, so this feature allows us to enforce the exipry date of the token
    # server side and not rely on the users cookie to exipre.
    max_age = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()

    # Decrypt the Security Token, data = [username, hashpass]
    data = login_serializer.loads( token, max_age = max_age )

    # Find the User
    user = User.get( data[0] )

    # Check Password and return user or None
    if user and data[1] == user.password:
        return user
    return None
