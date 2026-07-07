release: python manage.py migrate && python manage.py create_admin
web: gunicorn bankproject.wsgi --log-file - --bind 0.0.0.0:$PORT
