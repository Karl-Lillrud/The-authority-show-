from flask import Flask, session, g, render_template
from flask_cors import CORS  # Import CORS
from dotenv import load_dotenv
import os
from database.mongo_connection import collection
from utils import venvupdate
from utils.blueprint_register import register_blueprints  # Import the utility function

venvupdate.update_venv_and_requirements()

load_dotenv()
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"
register_blueprints(app, "routes", [os.path.dirname(__file__) + "/routes"])
CORS(app)


# Pass API_BASE_URL to templates
@app.context_processor
def inject_api_base_url():
    return dict(API_BASE_URL=os.getenv("API_BASE_URL"))


@app.before_request
def load_user():
    g.user_id = session.get("user_id")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True, use_reloader=False)
