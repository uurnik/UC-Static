#!/bin/bash

set -e

bash /code/scripts/prestart.sh
echo $DJANGO_SETTINGS_MODULE

python /code/Uuc_api/manage.py runserver 0.0.0.0:80 --settings=${DJANGO_SETTINGS_MODULE}