from app import app, db, lm, login_serializer
from app.forms import QuestionForm, ReviewQuestionForm
from app.models import User, Role, ClassInfo, Question
import datetime
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.principal import Principal, Permission, RoleNeed, UserNeed, identity_loaded
from flask.ext.security import Security, SQLAlchemyUserDatastore
import random

# Create a permission with a single Need, in this case a RoleNeed.
user_permission = Permission(RoleNeed('user'))
admin_permission = Permission(RoleNeed('admin'))

@app.route('/')
@login_required
@user_permission.require()
def index():
    ''' Top level location '''
    user = g.user
    if user.is_verified():
        unverifiedUsers = None
        if (user.is_admin()):
            unverifiedUsers = User.getAllUnverified()
        return render_template('index.html',
            user = user,
            superuserAndUnverifiedUsers = unverifiedUsers,
            helpfileurl=url_for('helpMain'))
    else:
        return redirect(url_for('unverifiedUser'))
        
@app.route('/helpMain')
@login_required
@user_permission.require()
def helpMain():
    ''' Help page associated with the main page.
        TODO: Make help dynamic (e.g. __page__Help.html)'''
    return render_template('helpMain.html')

############
# CHOOSERS #
############

@app.route('/chooseClass')
@login_required
@user_permission.require()
def chooseClass():
     ''' "Funneling" location to chose a class for a specific mode (write, edit, review) '''
     argMode = request.args.get('mode')
     session['mode']=argMode
     return render_template('chooseClass.html', title=session['mode'] + ": Choose Class" )

@app.route('/chooseQuestionToEdit')
@login_required
@user_permission.require()
def chooseQuestionToEdit():
    ''' Primary point for editing a question which begins with choosing questions that 
        exist for a previously chosen class.
        TODO: Allow admins to edit _all_ questions. '''
    assert session['classInfo'],"Couldn't find previous class info for class: %s??" % session['classAbbr']
    questions=[]
    for instance in Question.query.filter(Question.classAbbr == session['classAbbr']).order_by(Question.id): 
        questions.append(instance)
    if (len(questions)==0):
        flash("%s, you don't have any questions to edit for class %s!"%(currentUserFirstName(),session['classInfo'].longName))
    return render_template('chooseQuestion.html', questions=questions, \
                           title="Choose Question to Edit for "+session['classAbbr'] +" (" + session['classInfo'].longName +")" )

cachedQuestions=[]

@app.route('/chooseQuiz')
@login_required
@admin_permission.require()
def chooseQuiz():
    ''' Choose from existing unique quiz numbers available
        TODO: Super-inefficient, but tries to cache questions for a generated quiz... '''
    global cachedQuestions
    quizzesFound = set()
    cachedQuestions = Question.query.filter(Question.classAbbr == session['classAbbr']).all()
    for question in cachedQuestions:
         quizzesFound.add(question.quiz)
    return render_template('chooseQuiz.html', quizzes = quizzesFound, finalExamAvailable = (len(quizzesFound) > 0), title="Choose Quiz For "+session['classAbbr'] +" (" + session['classInfo'].longName +")" )

#############
# CHOSE-ERS # <-- Steps following choosers (above)
#############

@app.route('/choseClass')
@login_required
@user_permission.require()
def choseClass():
    ''' Once a class is chosen (above), redirect to the mode's page (etc. 'write'->editQuestion()) '''
#     assert(request.args.get('mode')==session['mode']),"request.args 'mode' (%s) != session['mode'] (%s)"    \
#         %(request.args.get('mode'),session['mode'])
    argForClass = request.args.get('classAbbr')
    session['classAbbr']=argForClass
    session['classInfo']=ClassInfo.get(session['classAbbr'])
    assert session['classInfo'],"Couldn't find class info for class: %s??" % session['classAbbr']
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
    
@app.route('/writeQuestion')
@login_required
@user_permission.require()
def writeQuestion():
    if ( session['classAbbr'] and session['classInfo'] ):
        question = Question(created = datetime.datetime.now(), classAbbr = session['classAbbr'], classID = session['classInfo'].currentID)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for("editQuestion",questionID=Question.idFromNumber(question.id,session['classInfo'])))
    else:
        flash("Please choose a class first.")
    return redirect(url_for("chooseClass",mode=session['mode']))
    
@app.route('/editQuestion', methods=['POST', 'GET'])
@login_required
@user_permission.require()
def editQuestion():
    if ( session['classAbbr'] and session['classInfo'] ):
        editQuestionID = int(request.args.get('questionID'))
        assert(editQuestionID),"editQuestionID (%d) wasn't passed to editQuestion??" % (editQuestionID)
        question = Question.get(editQuestionID)
        similarQuestions = question.getSimilarQuestions()
        question.decryptQuestionText(questionOnly = True)
        form = QuestionForm(request.form, question)
        if request.method == 'POST':
            if (request.form['button'] == 'delete'):
                # TODO: Add confirmation!
                db.session.delete(question)
                if (question.classID == session['classInfo'].currentID):
                    session['classInfo'].currentID = session['classInfo'].currentID - 1
                    db.session.merge(session['classInfo'])
                db.session.commit()
                flash('Question #%d deleted.'% question.number()+1)
                return redirect(url_for("chooseQuestionToEdit"))
            elif form.validate():
                form.populate_obj(question)
                question.modified = datetime.datetime.now()
                question.encryptQuestionText(questionOnly = True)
                db.session.merge(question)
                session['classInfo'].currentID = session['classInfo'].currentID + 1
                db.session.merge(session['classInfo'])
                db.session.commit()
                flash('Question #%d saved.' % question.number(session['classInfo'])+1)
                session['mode'] = 'Edit'
                return redirect(url_for("editQuestion",questionID=Question.idFromNumber(question.id,session['classInfo'])))
            else:
                flash('There was a problem handling the form POST for Question ID:%d'%(question.id))
        return render_template('editQuestion.html', form=form, similarQuestionsToDisplay=similarQuestions, questionToDisplay=question,   \
                               title="%s Question #%d For %s"%(session['mode'], question.number(session['classInfo'])+1, session['classInfo'].longName) )
    else:
        flash("Please choose a class first.")
    return redirect(url_for("chooseClass",mode=session['mode']))
                           
@app.route('/requestReviewQuestion')
@login_required
@user_permission.require()
def requestReviewQuestion():
    ''' Retrieve a question that's been least reviewed for a chosen class.
        Least reviewed is found by looking for 0, 1, 2, etc. up to 10 prior reviews.'''
    if ( session['classAbbr'] and session['classInfo'] ):
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
                ''' We have a list of least reviewed questions, pick one at random. '''
            questionToReview = random.choice(leastReviewedQuestionsToReview)
            return redirect(url_for('reviewQuestion',questionID=questionToReview.classID))
        flash('There are no questions to review for class: '+session['classInfo'].longName)
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route('/reviewQuestion', methods=['POST', 'GET'])
@login_required
@user_permission.require()
def reviewQuestion():
    ''' Handler for the "Review question" functionality. Redisplays the original question text as
        uneditable and includes comment sections.
        TODO: Show/hide comment sections''' 
    if ( session['classAbbr'] and session['classInfo'] ):
        ''' Handle a question review form '''
        reviewQuestionID = int(request.args.get('questionID'))
        assert(reviewQuestionID),"reviewQuestionID (%d) wasn't passed to reviewQuestion" % (reviewQuestionID)
        question = Question.get(reviewQuestionID)
        similarQuestions = question.getSimilarQuestions()
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
                               title="%s Question #%d For %s (%s)"%(session['mode'],question.number(session['classInfo'])+1,session['classAbbr'],session['classInfo'].longName ))
    else:
        flash("Please choose a class first.")
    return redirect(url_for('chooseClass',mode=session['mode']))

@app.route('/generateQuiz')
@login_required
@admin_permission.require()
def generateQuiz():
    if ( session['classAbbr'] and session['classInfo'] ):
        global cachedQuestions
        if cachedQuestions:
            quizNumber = request.args.get('quizID')
            assert quizNumber, "Generate quiz without a quiz number??"
            generatedQuiz, generatedID = Question.generateQuiz(session['classAbbr'], session['classInfo'], int(quizNumber), cachedQuestions)
            return render_template('generatedQuizOrExam.html', quizNumberToDisplay = quizNumber, generatedIDToDisplay = generatedID, \
                               generatedQuestionsToDisplay = generatedQuiz)
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
    if ( session['classAbbr'] and session['classInfo'] ):
        global cachedQuestions
        if cachedQuestions:
            assert(session['classAbbr']), "Generate final exam without a class??"
            assert session['classInfo'],"Couldn't find previous class info for class: %s??" % session['classAbbr']
            generatedExam, generatedID = Question.generateFinalExam(session['classAbbr'], session['classInfo'], cachedQuestions)
            return render_template('generatedQuizOrExam.html', generatedIDToDisplay = generatedID, generatedQuestionsToDisplay = generatedExam)
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
        code = request.form['code']
        questions = Question.questionsFromID(code)
        messages = get_flashed_messages()
        if (len(messages)==0):
            if (len(questions)==0):
                flash ("No valid questions found for code: %s??"%code)
            return render_template('generatedQuizOrExam.html', generatedIDToDisplay = code, generatedQuestionsToDisplay = questions)
    return render_template('retrieveQuizOrExam.html')

############
# UTILITES #
############

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
    unverifiedUsers = User.getAllUnverified()
    return render_template('verifyUsers.html', unverifiedUsers=unverifiedUsers)

@app.route("/verifyingUser")
@login_required
@admin_permission.require()
def verifyingUser():
    userToVerify = int(request.args.get('id'))
    user = User.query.filter(User.id == userToVerify).first()
    if user:
        if (user.is_verified() == False):
            user_datastore = SQLAlchemyUserDatastore(db, User, Role)
            default_role = user_datastore.find_or_create_role('user')
            user_datastore.add_role_to_user(user, default_role)
            db.session.merge(user)
            db.session.commit()
        else:
            flash("User ID %d is already verified?" % (userToVerify))
    else:
        flash("Couldn't find User ID %d to verify?" % (userToVerify))
    return redirect(url_for('verifyUsers'))

@app.route("/unverifiedUser")
@login_required
@user_permission.require()
def unverifiedUser():
    return render_template('unverifiedUser.html',
        admins = getAdmins())

@lm.user_loader
def load_user(id):
    return User.get(int(id))
 
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
    
from app import security

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