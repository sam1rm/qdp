#!/bin/bash
# heroku login
# heroku git:remote -a qdp
pycco *.py
pycco app/*.py
pycco db_repository/*.py
git push origin master
heroku releases | tail -2 | awk '{print $5"t"$6$7"."$1}' > version.txt
open -a "GitHub"
#git push heroku master