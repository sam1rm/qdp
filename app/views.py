from app import app, db, lm, login_serializer
from app.forms import QuestionForm, ReviewQuestionForm
from app.models import User, Role, ClassInfo, Question, Image
import datetime
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import current_user, login_required
from flask.ext.principal import Permission, RoleNeed, UserNeed, identity_loaded
from flask.ext.security import SQLAlchemyUserDatastore
import random
from utils import readTempFile, writeTempFile, makeTempFileResp

g_CachedQuestions=[]

# Create a permission with a single Need, in this case a RoleNeed.
user_permission = Permission(RoleNeed('user'))
admin_permission = Permission(RoleNeed('admin'))

@app.route('/')
@login_required
@user_permission.require()
def index():
    """ Top level site location. Displays additional buttons for admin: Verify users (if there
        are any), and provide additional administration. """
    user = g.user
    if user.is_verified():
        imageFileURL = url_for('static', filename='img/possibly47abc.png')
        return render_template('index.html',
            user = user,
            isAdmin = user.is_admin(),
            hasUnverifiedUsers = (user.is_admin() and User.hasUnverifiedUsers()),    # redundant on purpose
            help = 'helpMain',
            isDebugging = app.config['DEBUG'])
    else:
        return redirect(url_for('unverifiedUser'))
        
@app.route('/helpMain')
@login_required
@user_permission.require()
def helpMain():
    """ Help page associated with the main page.
        TODO: Make help dynamic (e.g. __page__Help.html)"""
    return render_template('helpMain.html')

############
# CHOOSERS #
############

@app.route('/chooseClass')
@login_required
@user_permission.require()
def chooseClass():
    """ "Funneling" location to chose a class for a specific mode (write, edit, review) """
    argMode = request.args.get('mode')
    if argMode:
        session['mode']=argMode
        return render_template('chooseClass.html', title=session['mode'] + ": Choose Class" )
    else:
        flash("Please choose a task (e.g., 'review') first.")
        return redirect(url_for('/'))

@app.route('/chooseQuestionToEdit')
@login_required
@user_permission.require()
def chooseQuestionToEdit():
    """ Primary point for editing a question which begins with choosing questions that 
        exist for a previously chosen class.
        TODO: Allow admins to edit _all_ questions. """
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        questions=[]
        for instance in Question.query.filter(Question.classAbbr == session['classAbbr']).order_by(Question.id): 
            questions.append(instance)
        if (len(questions)>0):
            return render_template('chooseQuestion.html', questions=questions, \
                                   title="Choose Question to Edit for "+classInfo.classAbbr+"("+classInfo.longName+")")
        else:
            flash("%s, you don't have any questions to edit for %s!"%(currentUserFirstName(),classInfo))
    else:
        flash("Please choose a class first.")
    return redirect(url_for("chooseClass",mode=session['mode']))

@app.route('/chooseQuiz')
@login_required
@admin_permission.require()
def chooseQuiz():
    """ Choose from existing unique quiz numbers available
        TODO: Super-inefficient, but tries to cache questions for a generated quiz... """
    assert session['classAbbr'],"Couldn't find previous classAbbr (ClassInfo)"
    classInfo = ClassInfo.get(session['classAbbr'])
    global g_CachedQuestions
    quizzesFound = set()
    g_CachedQuestions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
    for question in g_CachedQuestions:
        quizzesFound.add(question.quiz)
    return render_template('chooseQuiz.html', quizzes = quizzesFound, finalExamAvailable = (len(quizzesFound) > 0), title="Choose Quiz For "+session['classAbbr'] +" (" + classInfo.longName +")" )

#############
# CHOSE-ERS # <-- Steps following choosers (above)
#############

@app.route('/choseClass')
@login_required
@user_permission.require()
def choseClass():
    """ Once a class is chosen (above), redirect to the mode's page (etc. 'write'->editQuestion()) """
    if 'mode' in session:
        argForClass = request.args.get('classAbbr')
        session['classAbbr']=argForClass
        if (session['mode'] == "Write"):
            return redirect(url_for('writeQuestion'))
        elif (session['mode'] == "Edit"):
            return redirect(url_for('chooseQuestionToEdit'))
        elif (session['mode'] == "Review"):
            return redirect(url_for('requestReviewQuestion'))
        elif (session['mode'] == "Generate"):
            return redirect(url_for('chooseQuiz'))
        else:
            raise Exception("Unknown mode choice: %s" %(session['mode']))
    else:
        flash("Please choose a task (e.g., 'review') first.")
        return redirect(url_for('/'))
    
@app.route('/writeQuestion')
@login_required
@user_permission.require()
def writeQuestion():
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        question = Question(created = datetime.datetime.now(), classAbbr = session['classAbbr'], classID = classInfo.currentID)
        db.session.add(question)
        classInfo.currentID = classInfo.currentID + 1
        db.session.merge(classInfo)
        db.session.commit()
        return redirect(url_for("editQuestion",questionID=question.id))
    else:
        flash("Please choose a class first.")
    return redirect(url_for("chooseClass",mode=session['mode']))
    
@app.route('/editQuestion', methods=['POST', 'GET'])
@login_required
@user_permission.require()
def editQuestion():
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        assert classInfo,"classInfo wasn't passed to editQuestion??"
        rawQuestionIDAsString = request.args.get('questionID')
        assert rawQuestionIDAsString,"rawQuestionID wasn't passed to editQuestion??"
        question = Question.get(int(rawQuestionIDAsString))
        if question:    # Can be None if there was a problem retrieving this question
            similarQuestions = question.findSimilarQuestions()
            question.decryptQuestionText(questionOnly = True)
            form = QuestionForm(request.form, question)
            if request.method == 'POST':
                if (request.form['button'] == 'delete'):
                    # TODO: Add confirmation!
                    db.session.delete(question)
                    if ( ( question.classID + 1 ) == classInfo.currentID ):
                        classInfo.currentID = classInfo.currentID - 1
                        db.session.merge(classInfo)
                    db.session.commit()
                    flash('Question #%d deleted.' % ( question.offsetNumberFromClass(classInfo) + 1 ) )
                    return redirect(url_for("/"))
                elif form.validate():
                    form.populate_obj(question)
                    question.modified = datetime.datetime.now()
                    question.encryptQuestionText(questionOnly = True)
                    db.session.merge(question)
                    db.session.commit()
                    flash('Question #%d saved.' % ( question.offsetNumberFromClass(classInfo) + 1 ) )
                    session['mode'] = 'Edit'
                    return redirect(url_for("editQuestion",questionID=question.id))
                else:
                    flash('There was a problem handling the form POST for Question ID:%d'%(question.id))
            return render_template('editQuestion.html', form=form, similarQuestionsToDisplay=similarQuestions, questionToDisplay=question,   \
                               title="%s Question #%d For %s"%(session['mode'], (question.offsetNumberFromClass(classInfo)+1), classInfo.longName) )
    else:
        flash("Please choose a class first.")
    return redirect(url_for("chooseClass",mode=session['mode']))
                           
@app.route('/requestReviewQuestion')
@login_required
@user_permission.require()
def requestReviewQuestion():
    """ Retrieve a question that's been least reviewed for a chosen class.
        Least reviewed is found by looking for 0, 1, 2, etc. up to 10 prior reviews."""
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        if (Question.query.filter(Question.classAbbr == session['classAbbr']).count()>0):
            questionsToReview = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
            leastReviewed = app.config["REVIEWS_BEFORE_OK_TO_USE"]
            assert(leastReviewed>-1)
            for questionToReview in questionsToReview:
                numTimesReviewed = len(questionToReview.reviewers)
                if ( numTimesReviewed < leastReviewed):
                    leastReviewed = numTimesReviewed
            leastReviewedQuestionsToReview=[]
            for questionToReview in questionsToReview:
                numTimesReviewed = len(questionToReview.reviewers)
                if (numTimesReviewed == leastReviewed):
                    leastReviewedQuestionsToReview.append(questionToReview)
                # We have a list of least reviewed questions, pick one at random.
            questionToReview = random.choice(leastReviewedQuestionsToReview)
            return redirect(url_for('reviewQuestion',questionID=questionToReview.id))
        flash('There are no questions to review for class: '+classInfo.longName)
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route('/reviewQuestion', methods=['POST', 'GET'])
@login_required
@user_permission.require()
def reviewQuestion():
    """ Handler for the "Review question" functionality. Redisplays the original question text as
        uneditable and includes comment sections.
        TODO: Show/hide comment sections""" 
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        # Handle a question review form
        reviewQuestionIDAsString = request.args.get('questionID')
        assert(reviewQuestionIDAsString),"reviewQuestionID (%d) wasn't passed to reviewQuestion" % (reviewQuestionID)
        question = Question.get(int(reviewQuestionIDAsString))
        if question:
            similarQuestions = question.findSimilarQuestions()
            question.decryptQuestionText(commentsOnly = True)
            form = ReviewQuestionForm(request.form, question)
            if request.method == 'POST':
                form.populate_obj(question)
                if (g.user not in question.reviewers):
                    question.reviewers.append(g.user)
                question.modified = datetime.datetime.now()
                question.encryptQuestionText(commentsOnly = True)
                if (request.form['button'] == 'needswork'):
                    db.session.commit()
                    return redirect(url_for("requestReviewQuestion"))
                else:
                    if form.validate():            
                        db.session.merge(question)
                        db.session.commit()
                        return redirect(url_for("requestReviewQuestion"))
                    else:
                        flash('There was a problem handling the form POST for Question ID:%d'%(question.id))
            return render_template('reviewQuestion.html', form=form, similarQuestionsToDisplay = similarQuestions,                                                          \
                                   questionToDisplay=Question.addMarkupToQuestionText(Question.detachAndDecryptQuestionText(question, questionOnly=True)),  \
                                   title="%s Question #%d For %s (%s)"%(session['mode'],(question.offsetNumberFromClass(classInfo)+1),session['classAbbr'],classInfo.longName ))
        else:
            flash("Couldn't find question ID: %s??"%reviewQuestionIDAsString)
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route('/generateQuiz')
@login_required
@admin_permission.require()
def generateQuiz():
    if session['classAbbr']:
        classInfo = ClassInfo.get(session['classAbbr'])
        if g_CachedQuestions:
            quizNumber = request.args.get('quizID')
            assert quizNumber, "Generate quiz without a quiz number??"
            generatedQuiz, generatedID = Question.generateQuiz(classInfo, int(quizNumber), g_CachedQuestions)
            return render_template('generatedQuizOrExam.html', quizNumberToDisplay = quizNumber, generatedIDToDisplay = generatedID, \
                               generatedQuestionsToDisplay = generatedQuiz, classInfoToDisplay = classInfo)
        else:
            flash("Please select a quiz first.")
            return redirect(url_for('chooseQuiz'))
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route('/generateExam')
@login_required
@admin_permission.require()
def generateExam():
    if session['classAbbr']:
        if g_CachedQuestions:
            classInfo = ClassInfo.get(session['classAbbr'])
            generatedExam, generatedID = Question.generateFinalExam(classInfo, g_CachedQuestions)
            return render_template('generatedQuizOrExam.html', generatedIDToDisplay = generatedID, \
                                   generatedQuestionsToDisplay = generatedExam, classInfoToDisplay = classInfo)
        else:
            flash("Please select a quiz first.")
            return redirect(url_for('chooseQuiz'))
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route("/retrieveQuizOrExam", methods=['POST', 'GET'])
@login_required
@admin_permission.require()
def retrieveQuizOrExam():
    from flask.helpers import get_flashed_messages
    if request.method == 'POST':
        classInfo = ClassInfo.get(session['classAbbr'])
        code = request.form['code']
        questions = Question.getQuestionsFromID(code, addMarkupToQuestionTextToo=True)
        messages = get_flashed_messages()
        if (len(messages)==0):
            if (len(questions)==0):
                flash ("No valid questions found for code: %s??"%code)
                return redirect(url_for('retrieveQuizOrExam'))
        return render_template('generatedQuizOrExam.html', generatedIDToDisplay = code, \
           generatedQuestionsToDisplay = questions, classInfoToDisplay = classInfo)
    return render_template('retrieveQuizOrExam.html')

#########
# ADMIN #
#########
        
@app.route("/adminDatabaseReset")
@login_required
@admin_permission.require()
def adminDatabaseReset():
    messageList = []
    for entry in Question.query.all():
        messageList.append("Deleting Question id: %d (class id: %d) (%s)" % (entry.id, entry.classID, entry.shortenedDecryptedQuestionWithMarkup()))
        db.session.delete(entry)
    for entry in User.query.filter(User.fullname != "Glenn Sugden").all():
        messageList.append("Deleting User id: %d (%s)" % (entry.id,entry.fullname))
        db.session.delete(entry)
    for entry in ClassInfo.query.all():
        messageList.append("Resetting class ids for: %s (id: %d)" % (entry.longName, entry.id))
        entry.currentID = entry.startingID
    db.session.commit()
    messageList.append("...done!")
    return render_template('adminOutput.html',title="Admin. - Database Reset", messagesToDisplay = messageList)

@app.route("/adminTesting")
@login_required
@admin_permission.require()
def adminTesting():
    import os
    messages=[]
    image1,path1=Image.getAndCacheByName("9c.3.1.gif")
    app.logger.debug(path1)
    image2,path2=Image.getAndCacheByName("9c.3.1.jpg")
    app.logger.debug(path2)
    return render_template("adminTesting.html", imagesToDisplay = ["/tmp/9c.3.1.gif","/tmp/9c.3.1.jpg"])

############
# UTILITES #
############

@app.route("/tmp/<path:path>")
def tempPath(path):
    ''' Shiv (to utils) to handle tmp/FILE URL requests. '''
    #app.logger.debug(path)
    resp = makeTempFileResp(path)
    return resp

def currentUserFirstName():
    if g.user:
        if g.user.fullname:
            return g.user.fullname.split(" ")[0]
        else:
            return "?? anonymous ??"
    return "?? NO GLOBAL USER ??"
    
############
# SECURITY #
############

@app.route("/verifyUsers")
@login_required
@admin_permission.require()
def verifyUsers():
    unverifiedUsers = User.getAllUnverifiedUsers()
    return render_template('verifyUsers.html', unverifiedUsers=unverifiedUsers)

@app.route("/verifyingUser")
@login_required
@admin_permission.require()
def verifyingUser():
    idAsString = request.args.get('id')
    assert idAsString, "ID wasn't passed to verifyingUser??"
    user = User.query.filter(User.id == int(idAsString)).first()
    if user:
        if (user.is_verified() == False):
            user_datastore = SQLAlchemyUserDatastore(db, User, Role)
            default_role = user_datastore.find_or_create_role('user')
            user_datastore.add_role_to_user(user, default_role)
            db.session.merge(user)
            db.session.commit()
        else:
            flash("User ID %s is already verified?" % (idAsString))
    else:
        flash("Couldn't find User ID %s to verify?" % (idAsString))
    return redirect(url_for('verifyUsers'))

@app.route("/unverifiedUser")
@login_required
@user_permission.require()
def unverifiedUser():
    return render_template('unverifiedUser.html',
        admins = getAdmins())

@lm.user_loader
def load_user(uid):
    return User.get(int(uid))
 
@app.before_request
def before_request():
    g.user = current_user
    
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))
    
# # This processor is added to only the register view
# @security.register_context_processor
# def security_register_processor():
#     app.logger.debug("security_register_processor")

def generate_csrf_token():
    app.logger.debug("generate_csrf_token")
    if '_csrf_token' not in session:
        session['_csrf_token'] = app.config['SECRET_KEY']
    return session['_csrf_token']

@lm.token_loader
def load_token(token):
    """
    Flask-Login token_loader callback. 
    The token_loader function asks this function to take the token that was 
    stored on the users computer process it to check if its valid and then 
    return a User Object if its valid or None if its not valid.
    """
 
    #The Token itself was generated by User.get_auth_token.  So it is up to 
    #us to known the format of the token data itself.  
 
    #The Token was encrypted using itsdangerous.URLSafeTimedSerializer which 
    #allows us to have a max_age on the token itself.  When the cookie is stored
    #on the users computer it also has a exipry date, but could be changed by
    #the user, so this feature allows us to enforce the exipry date of the token
    #server side and not rely on the users cookie to exipre. 
    max_age = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()
 
    #Decrypt the Security Token, data = [username, hashpass]
    data = login_serializer.loads(token, max_age=max_age)
 
    #Find the User
    user = User.get(data[0])
 
    #Check Password and return user or None
    if user and data[1] == user.password:
        return user
    return None