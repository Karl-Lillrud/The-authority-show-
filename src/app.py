from flask import Flask, render_template, request, jsonify, url_for, session, redirect, g, Blueprint
from routes.register import register_bp
from routes.forgot_pass import forgotpass_bp
from routes.signin import signin_bp
from routes.register_podcast import registerpodcast_bp
from routes.dashboard import dashboard_bp
from routes.pod_management import dashboardmanagement_bp
from dotenv import load_dotenv
import os
from database.cosmos_connection import container
from utils import venvupdate

# update the virtual environment and requirements
venvupdate.update_venv_and_requirements()

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY")
app.config['PREFERRED URL SCHEME'] = 'https'
app.register_blueprint(register_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(signin_bp)
app.register_blueprint(registerpodcast_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(dashboardmanagement_bp)

APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

PI_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

@app.before_request
def load_user():
    g.user_id = session.get("user_id")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
