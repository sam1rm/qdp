import sys

from app import app

from flask_debugtoolbar import DebugToolbarExtension

from config import DEBUG

if __name__ == '__main__':
    debugFlag = ("-debug" in sys.argv)
    resetFlag = ("-reset" in sys.argv)
    if (debugFlag or DEBUG):
        toolbar = DebugToolbarExtension(app)
    if (resetFlag):
        import db_reset
        from app import db
        db_reset.resetDatabase(db)
    app.run(debug=(debugFlag or DEBUG),use_debugger=False,use_reloader=False)  # host='0.0.0.0'