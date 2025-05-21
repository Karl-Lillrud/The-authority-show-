from flask import Flask
from flask_cors import CORS
from backend.routes.auth import auth_bp
from backend.routes.email_change import email_change_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configure CORS to allow credentials
    CORS(app, supports_credentials=True)
    
    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure base URL
    app.config['BASE_URL'] = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(email_change_bp)
    
    return app
