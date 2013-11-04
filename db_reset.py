import datetime
import doctest
import os
import subprocess

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password

from app.models import User, Role, Question, ClassInfo, Image, encrypt

def resetDatabase(db):
    
    # Remove old database
    
    try:
        subprocess.call(["rm","app.db"])
    except OSError as ex:
        print "OSError({0}): {1}".format(ex.errno, ex.strerror)
    
    try:
        subprocess.call(["rm","-R","db_repository"])
    except OSError as ex:
        print "OSError({0}): {1}".format(ex.errno, ex.strerror)
    
    try:
        subprocess.call(["rm","-R","tmp"])
    except OSError as ex:
        print "OSError({0}): {1}".format(ex.errno, ex.strerror)
    
    # Create a new, empty database
    
    db.create_all()
    
    # Create a new migration repository
    
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
    
    # Load up Flask
    
    app = Flask(__name__)
    app.config.from_object('config')
    
    db = SQLAlchemy(app)
    
    # Setup Flask-Security
    
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)
    
    # Populate the database
    
    #########
    # ROLES #
    #########
    
    default_role = user_datastore.create_role(name='user', description='Generic user role')
    
    admin_role = user_datastore.create_role(name='admin', description='Generic administrator role')
    
    #########
    # USERS #
    #########
    
    with app.app_context():
        password = encrypt_password('shouldnotbepassword')
        #print password
    
    user1 = user_datastore.create_user(password=password, email = "headcrash@berkeley.edu", fullname = "Glenn Sugden", confirmed_at=datetime.datetime.now())
    
    user_datastore.add_role_to_user(user1, default_role)
    user_datastore.add_role_to_user(user1, admin_role)
    
    user2 = user_datastore.create_user(password=password, email = "carolm@EECS.berkeley.edu", confirmed_at=datetime.datetime.now(), fullname = "Carol Marshall")
    
    user_datastore.add_role_to_user(user2, default_role)
    user_datastore.add_role_to_user(user2, admin_role)
    
    user3 = user_datastore.create_user(password=password, email = "user@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Joe User")
    
    user_datastore.add_role_to_user(user3, default_role)
    
    user4 = user_datastore.create_user(password=password, email = "arie.coach@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Arie Meir")
    
    user_datastore.add_role_to_user(user4, default_role)
    
    user5 = user_datastore.create_user(password=password, email = "unverified@gmail.com", confirmed_at=datetime.datetime.now(), fullname = "Unverified User")
    
    user6 = user_datastore.create_user(password=password, email = "hack666@gmail.com", fullname = "Joe Hacker")
    
    ##############
    # CLASS INFO #
    ##############
        
    classInfo9A = ClassInfo( classAbbr = "9A", longName="Matlab", startingID = 0, currentID = 0 )
    db.session.add(classInfo9A)
    classInfo9C = ClassInfo( classAbbr = "9C", longName="C", startingID = 10000, currentID = 10000 )
    db.session.add(classInfo9C)
    classInfo9E = ClassInfo( classAbbr = "9E", longName="Unix", startingID = 20000, currentID = 20000 )
    db.session.add(classInfo9E)
    classInfo9F = ClassInfo( classAbbr = "9F", longName="C++", startingID = 30000, currentID = 30000 )
    db.session.add(classInfo9F)
    classInfo9G = ClassInfo( classAbbr = "9G", longName="Java", startingID = 40000, currentID = 40000 )
    db.session.add(classInfo9G)
    classInfo9H = ClassInfo( classAbbr = "9H", longName="Python", startingID = 50000, currentID = 50000 )
    db.session.add(classInfo9H)
    
    #############
    # QUESTIONS #
    #############
    
    ##########
    # IMAGES #
    ##########
    
    def add_image(filename):
        path = "db_populate_images/"
        imageDataFileRef = open(path+filename)
        assert imageDataFileRef,"Can't find %s??"%path+filename
        imageData = imageDataFileRef.read()
        assert imageData,"Image (%s) is empty??"%path+filename
        imageDataFileRef.close()
        image = Image( name=filename, data=imageData )
        db.session.add(image)
    
    add_image("9f.3.1.gif")
    add_image("9f.3.1.jpg")
    
    ##########
    # HELPER #
    ##########
    
    def add_question(classID,classAbbr,quiz,tags,instructions,question,example,answer,user_id,reviewers,isOKFlags):
        encryptedTags, encryptedTagsIV = encrypt(tags)
        if instructions:
            encryptedInstructions, encryptedInstructionsIV = encrypt(instructions)
        else:
            encryptedInstructions, encryptedInstructionsIV = None, None
        encryptedQuestion, encryptedQuestionIV = encrypt(question)
        if example:
            encryptedExample, encryptedExampleIV = encrypt(example)
        else:
            encryptedExample, encryptedExampleIV = None, None
        encryptedAnswer, encryptedAnswerIV = encrypt(answer)
        question = Question(classID = classID, classAbbr = classAbbr, \
                            created = datetime.datetime.now(), modified = datetime.datetime.now(), \
                            quiz = quiz,   \
                            tags=encryptedTags, tagsIV=encryptedTagsIV, \
                            instructions=encryptedInstructions, instructionsIV=encryptedInstructionsIV, \
                            question = encryptedQuestion, \
                            examples = encryptedExample, examplesIV =encryptedExampleIV, \
                            answer = encryptedAnswer, answerIV = encryptedAnswerIV, \
                            questionIV=encryptedQuestionIV,           \
                            user_id = user_id, \
                            reviewers = reviewers, \
                            isOKFlags = isOKFlags  )
        db.session.add(question)    
    
    ###############
    # 9A : MATLAB #
    ###############
        
    add_question(
        classInfo9A.startingID, \
        classInfo9A.classAbbr, \
        1, \
        u"Matrix Basics,Vectors", \
        None, \
        u"Suppose that A is a vector. Give two ways to define a vector that is as long as A and whose elements are all 1.", \
        None, \
        u"<ask Arie>", \
        1, \
        [], \
        0 )
    
    ##########
    # 9C : C #
    ##########
    
    add_question( classInfo9C.startingID, classInfo9C.classAbbr, \
        3, \
        u"Arrays,Files,Struct,Typedef", \
        None, \
        u'''In a single statement, define and initialize a seven-element table of day names named dayNames. The first element of dayNames is "Sunday", the second "Monday", and so on.''', \
        None, \
        u'''char* dayNames[7]={"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"};''', \
        1, \
        [], \
        0 )
    
    #####+######
    # 9F : C++ #
    ############
    
    add_question( classInfo9F.startingID, classInfo9F.classAbbr, \
        2, \
        u"Arrays,Streams", \
        None, \
        u"Write a boolean function AreIncreasing that determines whether the integers in its vector argument are in strictly increasing order. Your function should work for vectors of any length. Watch out for off-by-one errors.", \
        None, \
        u"bool AreIncreasing(vector<int> integers) {\n\tfor (int i = 0; i < integers.size()-1; i++) {\n\t\tif (integers[i] <= integers[i+i]) {\n\t\t\t, return false; }\n\t\treturn true; }", \
        1, \
        [], \
        0 )
    
    add_question(classInfo9F.startingID,classInfo9F.classAbbr, \
        1, \
        u"Fundamentals,Operators,Expressions", \
        u"Circle the correct expression. Assume default meanings for each operator.", \
        u"cin >> x or cin << x\ncout << \"value for n?\" or cout << \'value for n?\'", \
        None, \
        u"cin >> x\ncout << \"value for n?\"", \
        1, \
        [], \
        0)
        
    add_question(classInfo9F.startingID,classInfo9F.classAbbr, \
        3, \
        u"Dynamically allocated data", \
        u"Given the following declaration:\n\tclass ListNode {\n\tpublic:\n\t\tListNode (const int k);\n\t\tListNode (const int k, const ListNode* ptr);\n\t\t...\n\tprivate:\n\t\tint value;\n\t\tListNode *next;\n\t};", \
        u"Suppose that p, list1, and list2 are variables of type ListNode *, and that list1 and list2 point to the following structures.\n\t[[9f.3.1.gif]]\nDraw the diagram that results from executing the following code segment.\n\tp = list1->next;\n\tlist1->next->next = list2;\n\tp->next->next = list1;\n\tlist2->next->value = 5;", \
        None, \
        "[[9f.3.1.jpg]],", \
        1, \
        [], \
        0)
    
    db.session.commit()
    
    print "Done!"
    
if __name__ == "__main__":
    from app import db
    doctest.testmod()
    resetDatabase(db)