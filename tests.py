import os
import unittest
import tempfile

from app import app

from db_reset import initializeDatabase

# Database stuff

from flask import g
from flask.ext.sqlalchemy import SQLAlchemy
from sqlite3 import dbapi2 as sqlite3

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    with app.test_request_context():
        if not hasattr(g, 'sqlite_db'):
            g.sqlite_db = connect_db()
        return g.sqlite_db

def init_db():
    """Creates the database tables."""
    with app.app_context():
#         db = get_db()
#         with app.open_resource('schema.sql', mode='r') as f:
#             db.cursor().executescript(f.read())
        db = SQLAlchemy(app)
        initializeDatabase(db)
        db.session.commit()

class TestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        basedir = os.path.abspath(os.path.dirname(app.config['DATABASE']))
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + app.config['DATABASE']
        SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
        self.app = app.test_client()
        init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data
        
if __name__ == '__main__':
    unittest.main()
