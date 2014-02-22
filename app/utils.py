import re
import os

import flask

TMP_PATH = "/tmp"
IMAGE_REGEX = r'<img src="tmp/(.*?)".*?>'

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
    ['__init__.py', '__init__.pyc', 'forms.py', 'forms.pyc', 'models.py', 'models.pyc', 'oracle.py', 'oracle.pyc', 'utils.py', 'utils.pyc', 'views.py', 'views.pyc']
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
    """ Turn a filename request (e.g. tmp/image.jpg) into a valid request with the proper MIME type.
    If there's a problem, return a string with a message to be 'flash'ed (since we can't import app here)"""
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
        elif (data[1:4]=="PNG"):
            resp.content_type = "image/PNG"
        elif (data[6:10]=="Exif"):
            resp.content_type = "image/JPEG"
            resp = "*** warning: image header for "+filename+" is 'Exif' and not 'JFIF'..."
        elif (filename[-3:]==".gz"):
            resp.content_type = "application/x-gzip"
            resp.headers["Content-Disposition"] = "attachment; filename=app.db.gz"
        # Fallbacks
        else:
            fileExt = filename.split(".")[-1].lower()
            if (fileExt == 'gif'):
                resp.content_type = "image/GIF"
            elif (fileExt == 'png'):
                resp.content_type = "image/PNG"
            elif ((fileExt == 'jpg') or (fileExt == 'jpeg')):
                resp.content_type = "image/JPEG"
            else:
                resp = "*** warning: unable to determine content type from "+filename+"'s data..."
    except IOError as _:
        print 'Unable to open file for reading in makeTempFileResp: %s' % path
        resp = make_response(render_template('404.shtml'), 404)
    return resp

def findImageTags(text):
    """ Replaces [[filename]] with <img src="filename">, and returns the file names of the images to be cached (can't do it here because we need Image (which needs this file))
    >>> print findImageTags('this is a test')
    (Markup(u'this is a test'), set([]))
    >>> print findImageTags('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a test')
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a test'), set(['3.1.gif']))
    >>> print findImageTags('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> another <img src="tmp/3.2.gif" alt="yayface thingy image" width="170" height="98" /> test')
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> another <img src="tmp/3.2.gif" alt="yayface thingy image" width="170" height="98" /> test'), set(['tmp/3.2.gif', 'tmp/3.1.gif']))
    >>> print findImageTags(flask.Markup('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a test'))
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a test'), set([u'3.1.gif']))
    >>> print findImageTags(flask.Markup('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a <br />'))
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a <br />'), set([u'3.1.gif']))
    >>> print findImageTags(flask.Markup('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a &amp;'))
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> a &'), set([u'3.1.gif']))
    >>> print findImageTags(flask.Markup('this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> &amp; <img src="tmp/3.2.gif" alt="yayface thingy image" width="170" height="98" /> test'))
    (Markup(u'this is <img src="tmp/3.1.gif" alt="yayface thingy image" width="170" height="98" /> & <img src="tmp/3.2.gif" alt="yayface thingy image" width="170" height="98" /> test'), set([u'tmp/3.1.gif', u'tmp/3.2.gif']))
    """
    if (type(text) == type(flask.Markup(''))):
        result = flask.Markup.unescape(text)
    else:
        result = text[:]
    imagesToCache = set([])
    if text:
        imageRegExPat = re.compile(IMAGE_REGEX)
        match = imageRegExPat.search(result)
        endMatchPos = 0
        while match:
            filename = match.group(1)
            imagesToCache.add(filename)
            # We don't have to replace the old [[filename]] tags anymore...
            #result = result[:match.start(0)]+'<img src="'+TMP_PATH+'/'+filename+'">'+result[match.end(0):]
            endMatchPos += match.span(0)[1]
            match = imageRegExPat.search(result[endMatchPos:])
    return flask.Markup(result), imagesToCache

# This should no longer be necessary with the tinymce entry box...
# def convertToHTML(text):
#     """ Simple convert some text into HTML code .. appends <br />'s correctly to text which contains 
#         a newline (necessary to display multi-line text correctly). Also changes \tabs into (4) &nbsp;s 
#     >>> print convertToHTML("test")
#     test
#     >>> print convertToHTML('this\\nis\\na\\ntest.')
#     this<br />is<br />a<br />test.
#     """
#     #>>> print convertToHTML(r'this\nis\na\ntest.") # Doctest doesn't work with \n's...
#     #this<br />is<br />a<br />test.
#     #>>> print convertToHTML('this\nis\\na\ntest.\n")
#     #this<br />is<br />a<br />test.
#     #"""
#     result = ""
#     if text:
#         text = text.replace("\\r","\n")
#         text = text.replace("\r","\n")
#         text = text.replace("\\n","\n")
#         for line in text.split('\n'):
#             result += flask.Markup.escape(line) + flask.Markup('<br />')
#         result = result[:-6] # Rip off the final (unnecessary) <br />
#         result = result.replace("\t","&nbsp;&nbsp;&nbsp;&nbsp;")
#         result = result.replace("\\t","&nbsp;&nbsp;&nbsp;&nbsp;")
#     return result

def commaDelimitedStringAsSet(text):
    """ Take a comma delimited string and return it as a set: "1,2,3,2,1" -> (1,2,3)
    >>> commaDelimitedStringAsSet(None)
    set([])
    >>> commaDelimitedStringAsSet("")
    set([])
    >>> commaDelimitedStringAsSet("a")
    set(['a'])
    >>> commaDelimitedStringAsSet("a,b")
    set(['a', 'b'])
    >>> commaDelimitedStringAsSet("a,b,a")
    set(['a', 'b'])
    """    
    itemSet=set()
    if text:
        for item in text.split( "," ):
            itemSet.add(item.lower().strip())
    return itemSet

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print "### DOCTEST COMPLETE ###"