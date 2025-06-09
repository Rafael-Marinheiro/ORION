#!/bin/sh
set -e
cd /app/simulador_operacional
python manage.py migrate --noinput
exec gunicorn simulador_operacional.wsgi:application --bind 0.0.0.0:8000
