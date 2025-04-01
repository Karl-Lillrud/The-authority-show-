# filepath: d:\testdev\The-authority-show-\src\startup.sh
# Start Gunicorn (Flask) på port 8000
gunicorn --chdir src --bind=0.0.0.0:8000 --timeout 600 app:app

# Håll scriptet igång
wait