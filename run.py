import doctest
import sys

from app import app

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from config import DEBUG

if __name__ == '__main__':
    debugFlag = ("-debug" in sys.argv)
    if (debugFlag or DEBUG):
        doctest.testmod()
        toolbar = DebugToolbarExtension(app)
    app.run(debug=(debugFlag or DEBUG),use_debugger=False,use_reloader=False)  # host='0.0.0.0'