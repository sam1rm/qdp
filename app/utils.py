import re
import os

import flask

TMP_PATH = "/tmp"
IMAGE_REGEX = r"\[\[(.*?)\]\]"

def listDirectories(filepath):
    """ Get the directories in a path, removing files and invisibles
    >>> listDirectories(".")
    ['static', 'templates']
    >>> listDirectories("templates")
    []"""
    dirs = os.listdir(filepath)
    for index in range(len(dirs),0,-1):
        if ((os.path.isfile(os.path.join(filepath,dirs[index-1]))) or (dirs[index-1][0] == '.')):
            dirs.pop(index-1)
    return dirs        

def listFiles(filepath):
    """ Get the file in a path, removing directories and invisibles
    >>> listFiles(".")
    ['__init__.py', '__init__.pyc', 'forms.py', 'forms.pyc', 'models.py', 'models.pyc', 'utils.py', 'utils.pyc', 'views.py', 'views.pyc']
    >>> listFiles("static")
    []"""
    dirs = os.listdir(filepath)
    for index in range(len(dirs),0,-1):
        if ((os.path.isdir(os.path.join(filepath,dirs[index-1]))) or (dirs[index-1][0] == '.')):
            dirs.pop(index-1)
    return dirs        

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
        elif (data[6:10]=="JFIF"):
            resp.content_type = "image/JPEG"
    except IOError as _:
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
    """ Simple convert some text into HTML code .. appends <br />'s correctly to text which contains 
        a newline (necessary to display multi-line text correctly). Also changes \tabs into (4) &nbsp;s 
    >>> print convertToHTML("test")
    test
    >>> print convertToHTML("this\\nis\\na\\ntest.")
    this<br />is<br />a<br />test.
    """
    #>>> print convertToHTML(r"this\nis\na\ntest.") # Doctest doesn't work with \n's...
    #this<br />is<br />a<br />test.
    #>>> print convertToHTML("this\nis\\na\ntest.\n")
    #this<br />is<br />a<br />test.
    #"""
    result = ""
    if text:
        text = text.replace("\\r","\n")
        text = text.replace("\r","\n")
        text = text.replace("\\n","\n")
        for line in text.split('\n'):
            result += flask.Markup.escape(line) + flask.Markup('<br />')
        result = result[:-6] # Rip off the final (unnecessary) <br />
        result = result.replace("\t","&nbsp;&nbsp;&nbsp;&nbsp;")
        result = result.replace("\\t","&nbsp;&nbsp;&nbsp;&nbsp;")
    return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
