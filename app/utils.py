import base64
import config
import re
import os

from Crypto.Cipher import AES
from Crypto import Random

import flask

TMP_PATH = "/tmp"
IMAGE_REGEX = r"\[\[(.*?)\]\]"

def writeTempFile(filename,data):
    """ Write some data to a temporary file. Used by Image to pull dynamic images from database
        to be used in some question text.
    >>> print writeTempFile("test.txt","DON'T PANIC!"); print readTempFile("test.txt");
    /tmp/test.txt
    ("DON'T PANIC!", '/tmp/test.txt')
    """
    if ( os.path.exists(TMP_PATH) == False ):
        os.mkdir(TMP_PATH)
    path = TMP_PATH+"/"+filename
    fref = open(path,"wb")
    fref.write(data)
    fref.close()
    return path
    
def readTempFile(filename):
    """ Read some data from a temporary file. (See sister-function "write" for more info and tests) """
    path = TMP_PATH+"/"+filename
    fref=open(path,"rb")
    data=fref.read()
    fref.close()
    return data, path

def makeTempFileResp(filename):
    """ Turn a filename request (e.g. tmp/image.jpg) into a valid request with the proper MIME type. """
    from flask import make_response, render_template
    resp = None
    path = TMP_PATH+"/" + filename
    try:
        fref=open(path,"rb")
        data=fref.read()
        fref.close()
        resp = make_response(data)
        if (data[:3]=="GIF"):
            resp.content_type = "image/GIF"
        elif (data[4:8]=="JFIF"):
            resp.content_type = "image/JPEG"
    except IOError as ex:
        print 'Unable to open file for reading in makeTempFileResp: %s' % path
        resp = make_response(render_template('404.shtml'), 404)
    return resp

def replaceImageTags(text):
    """ Replaces [[filename]] with <img src="filename">, and returns the file names of the images to be cached (can't do it here because we need Image (which needs this file))
        TODO: Make this more efficient during <img> replacement by searching from replacement forward.
    >>> print replaceImageTags("this is a test")
    (Markup(u'this is a test'), set([]))
    >>> print replaceImageTags("this is [[filename.ext]] a test")
    (Markup(u'this is <img src="/tmp/filename.ext"> a test'), set(['filename.ext']))
    >>> print replaceImageTags("this is [[filename.ext]] another [[filename2.ext2]] test")
    (Markup(u'this is <img src="/tmp/filename.ext"> another <img src="/tmp/filename2.ext2"> test'), set(['filename2.ext2', 'filename.ext']))
    >>> print replaceImageTags(flask.Markup("this is [[filename.ext]] a test"))
    (Markup(u'this is <img src="/tmp/filename.ext"> a test'), set([u'filename.ext']))
    >>> print replaceImageTags(flask.Markup("this is [[filename.ext]] a <br />"))
    (Markup(u'this is <img src="/tmp/filename.ext"> a <br />'), set([u'filename.ext']))
    >>> print replaceImageTags(flask.Markup("this is [[filename.ext]] a &amp;"))
    (Markup(u'this is <img src="/tmp/filename.ext"> a &'), set([u'filename.ext']))
    >>> print replaceImageTags(flask.Markup("this is [[filename1.ext]] &amp; [[filename2.ext]] test"))
    (Markup(u'this is <img src="/tmp/filename1.ext"> & <img src="/tmp/filename2.ext"> test'), set([u'filename1.ext', u'filename2.ext']))
    """
    if (type(text) == type(flask.Markup(''))):
        result = flask.Markup.unescape(text)
    else:
        result = text[:]
    imagesToCache = set([])
    if text:
        imageRegExPat = re.compile(IMAGE_REGEX)
        match = imageRegExPat.search(result)
        while match:
            filename = match.group(1)
            imagesToCache.add(filename)
            result = result[:match.start(0)]+'<img src="'+TMP_PATH+'/'+filename+'">'+result[match.end(0):]
            match = imageRegExPat.search(result)
    return flask.Markup(result), imagesToCache

def convertToHTML(text):
    """ Simple convert some text into HTML code .. dds <br />'s correctly to text which contains 
        a newline (necessary to display multi-line text correctly).
    >>> print convertToHTML("test")
    test
    >>> print convertToHTML("this\\nis\\na\\ntest.")
    this<br />is<br />a<br />test.
    """
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
    try:
        iv = base64.b64decode(IV)
    except TypeError as ex:
        return "INVALID IV"
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, iv)
    message = base64.b64decode(b64Message)
    paddedMessage = OBJ.decrypt(message)
    try:
        messageLen = int(paddedMessage[:4])
    except ValueError as ex:
        return "INVALID LENGTH"
    numToPad = 16 - ( messageLen + 4 ) % 16
    message = paddedMessage[4:messageLen+4]
    if (paddedMessage[messageLen+4:] != config.PADDING[:numToPad]):
        return "INVALID PADDING"
    return(message)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
