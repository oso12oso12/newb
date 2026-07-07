release: python manage.py migrate
web: gunicorn bankproject.wsgi --log-file - --bind 0.0.0.0:$PORT
