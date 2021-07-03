#!/bin/bash

while ! nc -z db 3306; do
  sleep 0.1
done

python manage.py makemigrations api
python manage.py migrate 
cat ../create_super_user.txt | python3 manage.py shell
gunicorn Uuc_api.wsgi:application --bind 0.0.0.0:8000 --workers=5 --timeout 900