import datetime

from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, QuestionForm
from models import User, Question, getUnapprovedUsers

@app.route('/')
@login_required
def index():
    ''' Top level location '''
    user = g.user
    if user.is_approved():
        ''' Look for unverified users IF the current user is a "superuser." '''
        unapprovedUsers = None
        if (user.is_superuser_approved()):
            unapprovedUsers = getUnapprovedUsers()
        return render_template('index.html',
            user = user,
            superuserAndUnapprovedUsers = unapprovedUsers,
            helpfileurl=url_for('helpMain'))
    else:
        return redirect(url_for('unapprovedUser'))
        
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

@app.route("/approveUsers")
@login_required
def approveUsers():
    unapprovedUsers = getUnapprovedUsers()
    return render_template('approveUsers.html', unapprovedUsers=unapprovedUsers)

@app.route("/approvingUser")
@login_required
def approvingUser():
    if g.user.is_superuser_approved():
        userToApprove = int(request.args.get('id'))
        user = db.session.query(User).filter(User.id == userToApprove).first()
        if user:
            if (user.is_approved() == False):
                user.approved = 1
                db.session.merge(user)
                db.session.commit()
            else:
                flash("User ID %d is already approved?" % (userToApprove))
        else:
            flash("Couldn't find User ID %d to approve?" % (userToApprove))
        return redirect(url_for('approveUsers'))
    else:
        flash("UNAUTHORIZED APPROVAL")
        return redirect(url_for('index'))

@app.route("/unapprovedUser")
def unapprovedUser():
    superusers = db.session.query(User).filter(User.approved == 0)
    return render_template('unapprovedUser.html',
        superusers = superusers)

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

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['email', 'fullname', 'nickname'])
    return render_template('login.html', 
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
#         app.logger.debug("user is None: %s" % (resp.email))
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(created = datetime.datetime.now(), last_access = datetime.datetime.now(),   \
                    nickname = nickname, email = resp.email, fullname = resp.fullname,          \
                    approved=0) 
        db.session.add(user)
    else:
        user.last_access = datetime.datetime.now()
        db.session.merge(user)
    try:
        db.session.commit()
    except Exception as e:
        #flash(str(e))
        return redirect(url_for('login'))
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    
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

#app.jinja_env.globals['csrf_token'] = generate_csrf_token 
@app.route('/example')
def example():
    return render_template('example.html')
