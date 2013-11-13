#!/bin/bash
# heroku login
# heroku git:remote -a qdp
#pycco *.py
#pycco app/*.py
#pycco db_repository/*.py
#git push origin master
git push heroku master
heroku config:add rel=$(heroku releases | tail -2 | awk '{print $5"t"$6$7"."$1}')
open http://qdp.herokuapp.com