import base64
import config
import os

from Crypto.Cipher import AES
from Crypto import Random

def writeTempFile(filename,data):
    """ Write some data to a temporary file. Used by Image to pull dynamic images from database
        to be used in some question text.
    >>> print writeTempFile("test.txt","DON'T PANIC!"); print readTempFile("test.txt");
    /tmp/test.txt
    ("DON'T PANIC!", '/tmp/test.txt')
    """
    if ( os.path.exists("tmp") == False ):
        os.mkdir("tmp")
    path = "./"+filename
    fref = open(path,"wb")
    fref.write(data)
    fref.close()
    return path
    
def readTempFile(filename):
    """ Read some data from a temporary file. (See sister-function "write" for more info and tests) """
    path = "./"+filename
    fref=open(path,"rb")
    data=fref.read()
    fref.close()
    return data, path

def convertToHTML(text):
    """ Simple convert some text into HTML code .. mostly a stub to decorate later,
        but does add <br />'s correctly to text which contains a newline (necessary
        to display textfield text correctly.
    >>> print convertToHTML("test")
    test
    >>> print convertToHTML("this\\nis\\na\\ntest.")
    this<br />is<br />a<br />test.
    """
    import flask
    result = ""
    if text:
        for line in text.split('\n'):
            result += flask.Markup.escape(line) + flask.Markup('<br />')
        result = result[:-6]
    return result

def encrypt(message):
    """ Encrypt a 16-byte, length-prefixed, padded message using AES.
        Returned message is base64 encoded.
    >>> message,iv=encrypt("this is a test"); decrypt(message,iv)
    'this is a test'
    """
    iv = Random.new().read(AES.block_size)
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, iv)
    numToPad = 16 - ( len(message) + 4 ) % 16
    paddedMessage = "%04d%s%s" % (len(message),message,config.PADDING[:numToPad])
    encryptedMessage = OBJ.encrypt(paddedMessage)
    return(base64.b64encode(encryptedMessage),base64.b64encode(iv))

def decrypt(b64Message, IV):
    """ Decode a base64 message using AES. Returned is original message minus the padding,
        which is checked for integrity (the length is also a prefix integrity checker) 
        (see sister function encrypt for tests). """
    iv = base64.b64decode(IV)
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, iv)
    message = base64.b64decode(b64Message)
    paddedMessage = OBJ.decrypt(message)
    messageLen = int(paddedMessage[:4])
    numToPad = 16 - ( messageLen + 4 ) % 16
    message = paddedMessage[4:messageLen+4]
    if (paddedMessage[messageLen+4:] != config.PADDING[:numToPad]):
        return "INVALID PADDING"
    return(message)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
