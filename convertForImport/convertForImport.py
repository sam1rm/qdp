import html_entities

NEWLINE = "<br />"

KEYS=["tags","instructions","question","examples","hints","answer"]

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
                
def doConversion(key):
    line = ""
    text = None
    while(text!="`"):
        text=unicode(raw_input(key+"="))
        if (text!=u"`"):
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
    while True:
        text = {}
        for key in KEYS:
            text[key] = doConversion(key)
        print
        for key in KEYS:
            if (text[key]!=""):
                print key+"="+text[key]
        print