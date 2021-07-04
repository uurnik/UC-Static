#!/bin/bash

set -e

DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASS}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}

while ! nc -z db 3306; do
  sleep 0.1
done

# Run makemigration, migration
echo "Run makemigrations"
python /code/Uuc_api/manage.py makemigrations --settings=${DJANGO_SETTINGS_MODULE}
echo "Run migrate"
python /code/Uuc_api/manage.py migrate --settings=${DJANGO_SETTINGS_MODULE}
echo "Create superuser"
# python /code/backend/Uuc_api/manage.py createsuperuser --username ${DJANGO_SUPERUSER_USERNAME} --email ${DJANGO_SUPERUSER_EMAIL}  --noinput --settings=${DJANGO_SETTINGS_MODULE}  || true
cat /code/scripts/create_super_user.txt | python /code/Uuc_api/manage.py shell