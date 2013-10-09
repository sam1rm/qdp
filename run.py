import sys

from app import app

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from config import DEBUG

if __name__ == '__main__':
    debugFlag = ("-debug" in sys.argv)
    toolbar = DebugToolbarExtension(app)
    app.run(debug=(debugFlag or DEBUG))  # host='0.0.0.0'