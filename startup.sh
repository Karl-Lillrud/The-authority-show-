#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start the Flask application using gunicorn
gunicorn --workers 3 --bind 0.0.0.0:8000 src.app:app
