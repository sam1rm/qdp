from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    last_access = db.Column(db.DateTime)
    nickname = db.Column(db.String(120), index = True, unique = True)
    fullname = db.Column(db.String(120), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    approved = db.Column(db.Integer)
    questions = db.relationship('Question', backref = 'author', lazy = 'dynamic')
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.id)
    
    def is_approved(self):
        return (self.approved>0)
    
    def is_superuser_approved(self):
        return (self.approved>1)
 
    def __repr__(self):
        return '<User %r>' % (self.username)
 
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
        return db.session.query(Question).filter_by(id=id).one()

    def __str__(self):
        print "Question #%d: %s" % (self.id, self.question)

    def __repr__(self):
        return '<Question %r>' % (self.id)
    
    def shortenQuestion(self):
        if (len(self.question)<80):
            return self.question
        else:
            return self.question.strip()[0:38]+"..."+self.question.strip()[-38:]
    
def getUnapprovedUsers():
    unapprovedUsers = None
    for user in db.session.query(User).filter(User.approved == False).order_by(User.id): 
        if unapprovedUsers:
            unapprovedUsers.append(user)
        else:
            unapprovedUsers=[user]
    return unapprovedUsers

def encrypt(message):
    obj = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    return(obj.encrypt(message))

def decrypt(message):
    obj = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    return(obj.decrypt(message))