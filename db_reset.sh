#!/bin/bash
rm app.db
rm -R db_repository
rm -R tmp 2>/dev/null
./db_create.sh
python db_populate.py