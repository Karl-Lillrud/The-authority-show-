from flask import Flask, render_template, request, jsonify, url_for, session, redirect, g, Blueprint
from routes.register import register_bp
from routes.forgot_pass import forgotpass_bp
from routes.signin import signin_bp
from routes.register_podcast import registerpodcast_bp
from routes.dashboard import dashboard_bp
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

APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

PI_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

@app.before_request
def load_user():
    g.user_id = session.get("user_id")



@app.route('/profile/<guest_id>', methods=['GET'])
def guest_profile(guest_id):
    # Replace this with your actual data retrieval logic,
    # for example, querying your database or another data source.
    guests = load_all_guests()  # This should return a list/dictionary of guest info.
    guest = next((g for g in guests if g["id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template('guest/profile.html', guest=guest)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('settings/index.html')

@app.route('/get_user_podcasts', methods=['GET'])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    query = "SELECT * FROM c WHERE c.creator_id = @user_id"
    parameters = [{"name": "@user_id", "value": g.user_id}]
    podcasts = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    return jsonify(podcasts)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
