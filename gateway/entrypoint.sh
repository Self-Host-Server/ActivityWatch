#!/bin/sh
set -e

python manage.py migrate --noinput
python scripts/ensure_table.py

exec gunicorn gatewayproj.wsgi:application --bind 0.0.0.0:8080 --workers 1
