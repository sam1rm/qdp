from app import db, login_serializer
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from werkzeug import generate_password_hash, check_password_hash
  
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), unique=True)
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
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    questions = db.relationship('Question', backref = 'author', lazy = 'dynamic')

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

    def __repr__(self):
        return '<User #%d: %r>' % (self.id, self.email)
 
class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    for_class = db.Column(db.String(4))
    quiz = db.Column(db.Integer)
    section = db.Column(db.String(256))
    instructions = db.Column(db.Text)
    question = db.Column(db.Text)
    examples = db.Column(db.Text)
    hints = db.Column(db.Text)
    answer = db.Column(db.Text)
    num_reviews = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def get(id):
        return Question.query.filter_by(id=id).one()

    def __str__(self):
        print "Question #%d: %s" % (self.id, self.question)

    def __repr__(self):
        return '<Question %r>' % (self.id)
    
    def shortenQuestion(self):
        if (len(self.question)<80):
            return self.question
        else:
            return self.question.strip()[0:38]+"..."+self.question.strip()[-38:]
    
def getAdmins():
    admins = None
    for user in User.query.order_by(User.id):
        if (user.is_admin()):
            if admins:
                admins.append(user)
            else:
                admins=[user]
    return admins

def getUnverifiedUsers():
    unverifiedUsers = None
    for user in User.query.order_by(User.id):
        if (user.is_verified() == False):
            if unverifiedUsers:
                unverifiedUsers.append(user)
            else:
                unverifiedUsers=[user]
    return unverifiedUsers

def encrypt(message):
    obj = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    return(obj.encrypt(message))

def decrypt(message):
    obj = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    return(obj.decrypt(message))