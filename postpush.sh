#!/bin/bash
# heroku login
# heroku git:remote -a qdp
# pycco *.py
# pycco app/*.py
# pycco db_repository/*.py
# git push origin master
# git remote -v
git push heroku master
open http://qdp.herokuapp.com