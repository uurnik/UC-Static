#!/bin/bash

set -e

bash /code/scripts/prestart.sh

cd Uuc_api/
gunicorn Uuc_api.wsgi:application --bind 0.0.0.0:8000 --workers=5 --timeout 900
