# ===== Imports =====

import datetime
import doctest
import os
import string
import subprocess
import sys
import traceback

from app import utils

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password

from app.models import User, Role, Question, ClassInfo, Image

import app.oracle

# ===== Constants =====

MAKE_HACKABLE_DATABASE = False

CLASSES_FOLDER_PATH = "db_reset/classes/"
ROLE_FOLDER_PATH = "db_reset/roles/"
IMAGE_FOLDER_PATH = "db_reset/images/"
USER_FOLDER_PATH = "db_reset/users/"
QUESTION_BASE_FOLDER_PATH = "db_reset/questions/"

CLASSES = ['9A','9C','9E','9F','9G','9H','47B']

KEY_ROLE_DESCRIPTION = "description"

KEY_USER_EMAIL = "email"
KEY_USER_PASSWORD = "password" # Encrypted! See hashpass.py
KEY_USER_ROLES = "roles"

KEY_CLASS_DESCRIPTION = "description"
KEY_CLASS_STARTING_DB_ID  = "startid"

KEY_QUESTION_TAGS = 'tags'
KEY_QUESTION_INSTRUCTIONS = 'instructions'
KEY_QUESTION_QUESTION = 'question'
KEY_QUESTION_EXAMPLE = 'example'
KEY_QUESTION_HINTS = 'hints'
KEY_QUESTION_ANSWER = 'answer'

# ===== Globals =====
 
# gPathPrefix = "db_reset/"

# ===== Code =====

def removeOldDatabase():
    """ Use the OS to delete the app.db file, the db_repository, and the tmp/ directory. """
    if os.path.exists("app.db"):
        subprocess.call(["rm","app.db"])
    if os.path.exists("db_repository"):
        subprocess.call(["rm","-R","db_repository"])
    if os.path.exists("tmp"):
        subprocess.call(["rm","-R","tmp"])

    if os.path.exists("../app.db"):
        subprocess.call(["rm","../app.db"])
    if os.path.exists("../db_repository"):
        subprocess.call(["rm","-R","../db_repository"])
    if os.path.exists("../tmp"):
        subprocess.call(["rm","-R","../tmp"])
        
def readConfigFile(path,expectingKeys=None,optionalKeys=None):
    import copy
    configuration = {}
    expectingKeysCopy = copy.copy(expectingKeys)
    optionalKeysCopy = copy.copy(optionalKeys)
    try:
        fref = open(path)
        for line in fref.readlines():
            keyValue = line.strip().split("=")
            key = keyValue[0].strip().lower()
            if ((len(keyValue)>1) and (len(keyValue[1])>0)):
                # A ="B =C = D " -> config[a]="B =C = D"
                configuration[key] = string.join(keyValue[1:],"=").strip()
            else:
                # FOO=  ->  configuration[FOO]=None
                configuration[key] = None
        if expectingKeysCopy:
            for key in configuration:
                if key in expectingKeysCopy:
                    expectingKeysCopy.remove(key)
                else:
                    if ((optionalKeys == None) or (key not in optionalKeys)):
                        print "*** ERROR *** NOT EXPECTING KEY in '%s': '%s'" % (path,key) 
            for expectingKey in expectingKeysCopy:
                print "*** ERROR *** MISSING KEY in '%s': '%s'" % (path,expectingKey)
        if optionalKeysCopy:
            for key in configuration:
                if key in optionalKeysCopy:
                    optionalKeysCopy.remove(key)
                else:
                    if ((expectingKeys == None) or (key not in expectingKeys)):
                        print "*** warning *** NOT EXPECTING (optional) KEY in '%s': '%s'" % (path,key) 
            for optionalKey in optionalKeysCopy:
                print "*** warning *** MISSING (optional) KEY in '%s': '%s'" % (path,optionalKey)
    except Exception:
        traceback.print_exc(file=sys.stderr)
    finally:
        fref.close()
    return configuration
        
def addClasses(db):
    """ Walk the classes folder, adding found classes to the database, return class info for added questions later. """
    classes = {}
    for filename in utils.listFiles(CLASSES_FOLDER_PATH):
        fullPath = os.path.join(CLASSES_FOLDER_PATH, filename)
        classAbbrName = string.join(filename.split(".")[:-1],".") # words.blah.foo.txt -> words.blah.foo
        print "Adding class:",classAbbrName
        configuration = readConfigFile(fullPath,[KEY_CLASS_DESCRIPTION,KEY_CLASS_STARTING_DB_ID])
        assert len(configuration[KEY_CLASS_DESCRIPTION])>0, "Class is missing description"
        classInfo = ClassInfo( classAbbr = classAbbrName, longName=configuration[KEY_CLASS_DESCRIPTION],  \
                               startingID = int( configuration[KEY_CLASS_STARTING_DB_ID] ),               \
                               currentID = int( configuration[KEY_CLASS_STARTING_DB_ID] ) )
        db.session.add(classInfo)
        classes[classAbbrName]=classInfo
    return classes

def addRoles(user_datastore):
    """ Walk the user folder, adding found roles to the database, return roles for added users later. """
    roles = {}
    for filename in utils.listFiles(ROLE_FOLDER_PATH):
        fullPath = os.path.join(ROLE_FOLDER_PATH, filename)
        roleName = string.join(filename.split(".")[:-1],".") # words.blah.foo.txt -> words.blah.foo                print "Adding class:",classAbbrName
        print "Adding role:",roleName
        configuration = readConfigFile(fullPath,[KEY_ROLE_DESCRIPTION])
        role = user_datastore.create_role(name=roleName, description=configuration[KEY_ROLE_DESCRIPTION])
        roles[roleName]=role
    return roles

def addUsers(user_datastore, roles):
    """ Walk the user folder and associate prior roles to a user. """
    assert len(roles) > 0, "NO ROLES GIVEN FOR addUsers()!"
    users = {}
    for filename in utils.listFiles(USER_FOLDER_PATH):
        fullPath = os.path.join(USER_FOLDER_PATH, filename)
        userName = string.join(filename.split(".")[:-1],".") # words.blah.foo.txt -> words.blah.foo
        print "Adding user:",userName
        configuration = readConfigFile(fullPath,[KEY_USER_PASSWORD,KEY_USER_EMAIL,KEY_USER_ROLES])
        user = user_datastore.create_user(password=configuration[KEY_USER_PASSWORD], \
                                          email=configuration[KEY_USER_EMAIL], fullname = userName, \
                                          confirmed_at=datetime.datetime.now() )
        if configuration[KEY_USER_ROLES]:
            rolesToAdd = configuration[KEY_USER_ROLES].split(",")
            for roleToAdd in rolesToAdd:
                if roleToAdd in roles:
                    role = roles[roleToAdd] # 'admin' -> admin_role object previously added to the database
                else:
                    print "*** ERROR *** UKNOWN ROLE (%s) TO ADD TO USER: '%s'" % (roleToAdd,userName)
                user_datastore.add_role_to_user(user, role)
        else:
            print "*** warning *** No roles defined for: '%s'" % userName
        users[userName]=user
    return users

def addQuestions(db, classes, users):
    """ Walk the db_reset/questions folder, processing the directories and text files and 
    adding them to the database. Structure is "questions:class:quiz#:question1.txt,question2.txt,etc.""" 
    assert len(users) > 0, "NO USERS FOR addQuestions()!"
    questions = {}
    for classAbbr in utils.listDirectories(QUESTION_BASE_FOLDER_PATH):
        print "Adding questions for class:",classAbbr
        classFullPath = os.path.join(QUESTION_BASE_FOLDER_PATH, classAbbr)
        for quizNumber in utils.listDirectories(classFullPath):
            print "\tquestions for quiz #",quizNumber
            quizFullPath = os.path.join(classFullPath, quizNumber)
            for filename in utils.listFiles(quizFullPath):
                fullPath = os.path.join(quizFullPath, filename)
                # Read the text file, looking for all parts of a question
                configuration = readConfigFile(fullPath,[KEY_QUESTION_TAGS, \
                                                         KEY_QUESTION_QUESTION, \
                                                         KEY_QUESTION_ANSWER],\
                                                        [KEY_QUESTION_INSTRUCTIONS, \
                                                         KEY_QUESTION_EXAMPLE, KEY_QUESTION_HINTS])
                # Encrypt all of the question parts
                tagIV, tagIVb64 = app.oracle.generateIV()
                questionIV, questionIVb64 = app.oracle.generateIV()
                _, commentIVb64 = app.oracle.generateIV()
                encryptedTags = app.oracle.encrypt(configuration[KEY_QUESTION_TAGS], tagIV)
                if ((KEY_QUESTION_INSTRUCTIONS in configuration) and (configuration[KEY_QUESTION_INSTRUCTIONS])):
                    encryptedInstructions = app.oracle.encrypt(configuration[KEY_QUESTION_INSTRUCTIONS], questionIV)
                else:
                    encryptedInstructions = None
                encryptedQuestion = app.oracle.encrypt(configuration[KEY_QUESTION_QUESTION], questionIV)
                if ((KEY_QUESTION_EXAMPLE in configuration) and (configuration[KEY_QUESTION_EXAMPLE])):
                    encryptedExample = app.oracle.encrypt(configuration[KEY_QUESTION_EXAMPLE], questionIV)
                else:
                    encryptedExample = None
                if ((KEY_QUESTION_HINTS in configuration) and (configuration[KEY_QUESTION_HINTS])):
                    encryptedHints = app.oracle.encrypt(configuration[KEY_QUESTION_HINTS], questionIV)
                else:
                    encryptedHints = None
                encryptedAnswer = app.oracle.encrypt(configuration[KEY_QUESTION_ANSWER], questionIV)
                # Create question instance
                question = Question(classID = classes[classAbbr].currentID, classAbbr = classAbbr, \
                                    created = datetime.datetime.now(), modified = datetime.datetime.now(), \
                                    quiz = int(quizNumber),   \
                                    tags=encryptedTags, \
                                    instructions=encryptedInstructions, \
                                    question = encryptedQuestion, \
                                    examples = encryptedExample, \
                                    hints = encryptedHints, \
                                    answer = encryptedAnswer, \
                                    tagsIV = tagIVb64, \
                                    questionIV=questionIVb64, \
                                    commentsIV = commentIVb64 )
#                                     user_id = user_id, \
#                                     reviewers = reviewers, \
#                                     isOKFlags = isOKFlags  )
                # Increment the classID (see Question model for explanation of classID vs. id)
                classes[classAbbr].currentID += 1
                # Used primarily for debugging, return the questions associated with a class
                if classAbbr in questions:
                    questions[classAbbr].append(question)
                else:
                    questions[classAbbr]=[question]
                # Add the question to the database
                db.session.add(question)   
    return questions

def addImages(db):
    """ Walk the images folder, storing the names and paths of images found in a dictionary. """
    images = {}
    for classAbbr in utils.listDirectories(IMAGE_FOLDER_PATH):
            fullPath = os.path.join(IMAGE_FOLDER_PATH, classAbbr)
            for oneFilename in utils.listFiles(fullPath):
                fullPath = os.path.join(fullPath, oneFilename)
                # Read the image file
                imageDataFileRef = open(fullPath)
                assert imageDataFileRef,"Can't open '%s'??" % fullPath
                imageData = imageDataFileRef.read()
                assert (imageData and len(imageData)>0),"Image '%s' is empty??" % fullPath
                imageDataFileRef.close()
                # Encrypt the image data
                dataIV,dataIV64 = app.oracle.generateIV();
                # Create new Image instance & add it to the database
                image = Image( filename=oneFilename, classAbbr=classAbbr, data=app.oracle.encrypt(imageData,dataIV), dataIV=dataIV64 )
                db.session.add(image)
                # Used primarily for debugging, return the filenames in the images folder 
                if classAbbr in images:
                    images[classAbbr].append(oneFilename)
                else:
                    images[classAbbr]=[oneFilename]
    return images

def initializeDatabase(db):

    db.create_all()
    
    # Create a new migration repository
    
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

def resetDatabase(db):
    
    messages = []
        
    # Remove old database
    
    removeOldDatabase()
    
    messages.append("Removed old database")
    
    # Create a new, empty database
    
    initializeDatabase(db)

    messages.append("Initialized new database")
            
    # Load up Flask
    
    app = Flask(__name__)
    app.config.from_object('config')
    
    db = SQLAlchemy(app)
    
    # Set up Flask-Security
    
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)
    
    # Populate the database
    
    classes = addClasses(db)
    
    messages.append("Added classes: "+str(classes))
        
    roles = addRoles(user_datastore)
    
    messages.append("Added roles: "+str(roles))
    
    users = addUsers(user_datastore, roles)
    
    messages.append("Added users: "+str(users))
        
    questions = addQuestions(db, classes, users)
    
    messages.append("Added questions: "+str(questions))
    
    images = addImages(db)
    
    messages.append("Added images: "+str(images))
    
    messages.append("...committing to database...");
    
    db.session.commit()
    
    messages.append("...done!")
    
    return messages
  
###############################################################
# MAIN (if run from the command line, execute doctests first) #
###############################################################
  
if __name__ == "__main__":
    from app import db
    doctest.testmod()
    messages = resetDatabase(db)
    for message in messages:
        print "-",message
#     global gPathPrefix
#     if ((os.path.exists("utils.py")==False) and (os.path.exists("../utils.py"))==True):
#         gPathPrefix = ""