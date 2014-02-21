import html_entities

NEWLINE = "<br />"

# def replaceAsciiWithMarkup(text,asciiChar,replaceMarkup):
#     location = text.find(asciiChar)
#     while(location != -1):
#         text=text[:location]+replaceMarkup+text[location+1:]
#         location = text.find(asciiChar)
#     return text

def convertTextToHTML(text):
    """
    >>> convertTextToHTML("")
    ''
    >>> convertTextToHTML("a")
    'a'
    >>> convertTextToHTML(chr(9))
    '\\t'
    >>> convertTextToHTML(unichr(8217))
    '&rsquo;'
    >>> convertTextToHTML(u'\u2026')
    '&hellip;'
    """
    line = ""
    for char in text:
        if ord(char) in html_entities.codepoint2name:
            line += "&" + html_entities.codepoint2name[ord(char)] + ";"
        else:
            line += char
#             text = replaceAsciiWithMarkup(text,chr(9),"&nbsp;&nbsp;&nbsp;&nbsp;")
#             text = replaceAsciiWithMarkup(text,chr(226),"&rsquo;")
#             text = replaceAsciiWithMarkup(text,'\xc9',"&hellip;")
    return line
                
def doConversion():
    line = ""
    text = None
    while(text!="convert"):
        text=unicode(raw_input("> "))
        if (text!=u"convert"):
            line += convertTextToHTML(text) 
            line += NEWLINE
    while (line[:6]==NEWLINE):
        line=line[6:]
    while (line[-6:]==NEWLINE):
        line=line[:-6]
    return line
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    text = None
    while ( text != "quit" ):
        text = doConversion()
        if (text != "quit"):
            print
            print text
            print
