#!/bin/bash
rm app.db
rm -R db_repository
rm -R tmp
./db_create.sh
python db_populate.py