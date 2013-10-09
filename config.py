import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

CSRF_ENABLED = True
SECRET_KEY = '6FxLM4DBMHbkgqKty2YRCyfS'
IV='\xb2\xc6\xa2\x06\x81\xc9^\xf1{\x19\xb9q\xe1\x00\x18\xd4'

OPENID_PROVIDERS = [
{'name':'StackExchange', 'url':'https://openid.stackexchange.com'},
{'name':'Google', 'url':'https://www.google.com/accounts/o8/id'},
{'name':'Yahoo', 'url':'https://me.yahoo.com'},
{'name':'Flickr', 'url':'http://www.flickr.com/username'},
{'name':'AOL', 'url':'http://openid.aol.com/username'},
{'name':'Blogspot', 'url':'https://www.blogspot.com/'},
{'name':'LiveJournal', 'url':'http://username.livejournal.com/'},
{'name':'Wordpress', 'url':'https://username.wordpress.com/'},
{'name':'VerisignLabs', 'url':'https://pip.verisignlabs.com/'},
{'name':'MyOpenID', 'url':'https://www.myopenid.com/ - slated to be shut down Feb 2014'},
{'name':'MyVidoop', 'url':'https://myvidoop.com/'},
{'name':'ClaimID', 'url':'https://claimid.com/username'},
{'name':'Technorati', 'url':'https://technorati.com/people/technorati/username/'},
{'name':'PayPal', 'url':'https://www.x.com/developers/paypal/documentation-tools/quick-start-guides/standard-openid-integration-paypal-access'}]

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')