#!/bin/bash
# heroku login
# heroku git:remote -a qdp
pycco *.py
pycco app/*.py
pycco db_repository/*.py
git push origin master
open -a "GitHub"
#git push heroku master