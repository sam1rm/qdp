from app import app, db, lm
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.security import Security, SQLAlchemyUserDatastore
from app.forms import QuestionForm
from app.models import User, Role, Question, getAdmins, getUnverifiedUsers

# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed('admin'))

@app.route('/')
@login_required
def index():
    ''' Top level location '''
    user = g.user
    if user.is_verified():
        unverifiedUsers = None
        if (user.is_admin()):
            unverifiedUsers = getUnverifiedUsers()
        return render_template('index.html',
            user = user,
            superuserAndUnverifiedUsers = unverifiedUsers,
            helpfileurl=url_for('helpMain'))
    else:
        return redirect(url_for('unverifiedUser'))
        
@app.route('/helpMain')
def helpMain():
    ''' Help page associated with the main page.
        TODO: Make help dynamic (e.g. __page__Help.html)'''
    return render_template('helpMain.html')

@app.route('/writeQuestion', methods=['POST', 'GET'])
@login_required
def writeQuestion():
    ''' Primary location for writing a new or editing an existing question.'''
    form = QuestionForm()
#     form.element(name='section')['_onchange']='window.alert("Section!")'
    if (request.method == "POST"):
        if (form.validate_on_submit()):
            import datetime
            question = Question(created = datetime.datetime.now(), modified = datetime.datetime.now(),                \
                                for_class=session['the_class'],                                                       \
                                quiz=form.quiz.data, section=form.section.data,                                       \
                                instructions=form.instructions.data, question=form.question.data,                     \
                                examples=form.examples.data, hints=form.hints.data, answer=form.answer.data,          \
                                num_reviews=0, user_id=session['user_id'])
            db.session.add(question)
            db.session.commit()
            flash('Question saved.')
        else:
            flash('There was a problem validating the Question form.')
    existing=[]
    editQuestionID = request.args.get('qid')
    if editQuestionID:
        ''' Fill in form with an existing question '''
        question = Question.get(editQuestionID)
        form.quiz.data = question.quiz
        form.section.data = question.section
        form.instructions.data = question.instructions
        form.question.data = question.question
        form.examples.data = question.examples
        form.hints.data = question.hints
        form.answer.data = question.answer
        ''' Query the database for questions that have the same quiz and section.
            TODO: Make this live-update when the section has changed in the form ''' 
        for instance in db.session.query(Question).filter(Question.quiz == question.quiz, Question.section == question.section).order_by(Question.id):
            existing.append(instance) 
    return render_template('writeQuestion.html', the_class=session['the_class'], form=form,   \
                           title="Write Question for "+session['the_class'], existing=existing )
# 
@app.route('/editQuestion')
@login_required
def editQuestion():
    ''' Primary point for editing a question which begins with choosing questions that 
        exist for a previously chosen class. '''
    questions=[]
    for instance in db.session.query(Question).filter(Question.for_class == session['the_class']).order_by(Question.id): 
        questions.append(instance)
#     the_class = request.args.get('the_class')
    assert(request.args.get('the_class')==session['the_class'])
    return render_template('chooseQuestion.html', the_class=session['the_class'], questions=questions)
# 
@app.route('/reviewQuestion')
@login_required
def reviewQuestion():
    ''' Retrieve a question that's been least reviewed for a chosen class.
        Least reviewed = sorted by reviewed count and first one chosen. '''
    if (db.session.query(Question).filter(Question.for_class == session['the_class']).count()>0):
        return redirect(url_for('writeQuestion')+"?qid="+str(db.session.query(Question).filter(Question.for_class == session['the_class']).order_by(Question.num_reviews).first().id))
    else:
        flash('There are no questions to review for class: '+session['the_class'])
        return redirect(url_for('chooseClass')+"?mode="+session['mode'])

@app.route('/generateQuizOrExam')
@login_required
def generateQuizOrExam():
    #the_class = request.args.get('the_class')
    assert(request.args.get('the_class')==session['the_class'])
    return render_template('generateQuizOrExam.html', the_class=session['the_class'])

@app.route("/choseRetrieve")
@login_required
def choseRetrieve():
    return render_template('retrieveQuizOrExam.html') 

@app.route("/verifyUsers")
@admin_permission.require()
def verifyUsers():
    unverifiedUsers = getUnverifiedUsers()
    return render_template('verifyUsers.html', unverifiedUsers=unverifiedUsers)

@app.route("/verifyingUser")
@admin_permission.require()
@login_required
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
def unverifiedUser():
    return render_template('unverifiedUser.html',
        admins = getAdmins())

@app.route('/chooseClass')
@login_required
def chooseClass():
     ''' "Funneling" location to chose a class for a specific mode (write, edit, review) '''
     argMode = request.args.get('mode')
     session['mode']=argMode
     return render_template('chooseClass.html', fromMode = session['mode'], title="Choose Class" )

@app.route('/choseClass')
@login_required
def choseClass():
    ''' Once a class is chosen (above), redirect to the mode's page (etc. 'write'->writeQuestion()) '''
#     assert(request.args.get('mode')==session['mode']),"request.args 'mode' (%s) != session['mode'] (%s)"    \
#         %(request.args.get('mode'),session['mode'])
    argForClass = request.args.get('the_class')
    session['the_class']=argForClass
    if (session['mode'] == "write"):
        return redirect(url_for('writeQuestion', the_class=session['the_class']))
    elif (session['mode'] == "edit"):
        return redirect(url_for('editQuestion', the_class=session['the_class']))
    elif (session['mode'] == "review"):
        return redirect(url_for('reviewQuestion', the_class=session['the_class']))
    elif (session['mode'] == "generate"):
        return redirect(url_for('generateQuizOrExam', the_class=session['the_class']))
    else:
        raise Exception("Unknown mode choice: %s" %(session['mode']))

# @app.route('/login', methods = ['GET', 'POST'])
# def login():
#     ''' Place to handle the login '''
#     if g.user is not None and g.user.is_authenticated():
#         return redirect(url_for('index'))
#     form = ExtendedLoginForm()
#     if form.validate_on_submit():
#         flash(u'Successfully logged in as %s' % form.user.username)
#         user = User.query.filter_by(email = resp.email).first()
#         if user is None:
#     #         app.logger.debug("user is None: %s" % (resp.email))
#             user = User(created = datetime.datetime.now(), last_access = datetime.datetime.now(),   \
#                         email = resp.email, fullname = resp.fullname,                               \
#                         verified=0) 
#             db.session.add(user)
#         else:
#             user.last_access = datetime.datetime.now()
#             db.session.merge(user)
#         try:
#             db.session.commit()
#         except Exception as e:
#             #flash(str(e))
#             return redirect(url_for('security.login'))
#         session['user_id'] = form.user.id
#         if 'remember_me' in session:
#             remember_me = session['remember_me']
#             session.pop('remember_me', None)
#         login_user(user, remember = remember_me)
#         return redirect(request.args.get("next") or url_for("index"))
#     return render_template(url_for('security/login'), 
#         title = 'Sign In',
#         form = form)
#     
# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))
 
@app.before_request
def before_request():
    g.user = current_user
    
from app import security

# This processor is added to only the register view
@security.register_context_processor
def security_register_processor():
    app.logger.debug("security_register_processor")

# @app.before_request
# def csrf_protect():
#     #app.logger.debug("csrf_protect")
#     if request.method == "POST":
#         token = session.pop('_csrf_token', None)
#         if not token or token != request.form.get('_csrf_token'):
#             abort(403)
#             
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
 
#app.jinja_env.globals['csrf_token'] = generate_csrf_token 
@app.route('/example')
def example():
    return render_template('example.html')
