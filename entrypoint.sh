#!/bin/sh
set -e

DJANGO_PORT=${DJANGO_PORT:-3000}

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django on port $DJANGO_PORT"
exec python manage.py runserver 0.0.0.0:"$DJANGO_PORT"

