from flask import Flask, render_template, request, jsonify
from cosmos_routes import ( 
    cosmos_bp,  # Import the blueprint for routing the DB methods
    create_item,
    get_items
)
import uuid
import hashlib

app = Flask(__name__, template_folder='templates')
app.register_blueprint(cosmos_bp, url_prefix='/api')

@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')  # ✅ Loads signin.html when visiting root

    # Handle login when method is POST
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400

    data = request.get_json()

    # Ensure required fields exist
    required_fields = {"email", "password"}
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: email, password"}), 400

    # Validate data types
    if not isinstance(data["email"], str) or not isinstance(data["password"], str):
        return jsonify({"error": "Invalid data types. 'email' and 'password' must be strings."}), 400

    # Hash the input password to compare with the stored hashed password
    hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()

    # Query the database for the user
    users, status = get_items()

    if status != 200:
        return jsonify({"error": "Database query failed"}), 500

    user = next((u for u in users if u["email"] == data["email"]), None)

    if not user or user["password"] != hashed_password:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "user_id": user["id"]}), 200

from flask import Flask, render_template, request, jsonify
from cosmos_routes import create_item, get_items
import uuid
import hashlib

app = Flask(__name__, template_folder='templates')
app.register_blueprint(cosmos_bp, url_prefix='/api')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')  # ✅ Shows registration form when accessed via GET

    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400

    data = request.get_json()

    # Ensure required fields exist
    required_fields = {"email", "password"}
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: email, password"}), 400

    # Validate data types
    if not isinstance(data["email"], str) or not isinstance(data["password"], str):
        return jsonify({"error": "Invalid Entry. 'email' and 'password' must be strings."}), 400

    # Hash the password before storing it
    hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()

    # Generate a unique user ID
    user_id = str(uuid.uuid4())

    # Prepare user data for storage
    user_data = {
        "id": user_id,
        "email": data["email"],
        "password": hashed_password,  # Storing hashed password securely
    }

    # Store in Cosmos DB
    response, status = create_item(user_data)

    return jsonify(response), status

@app.route('/forgotpassword/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgotpassword/forgot-password.html')  # ✅ Renders form for password reset

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'GET':
        return render_template('dashboard.html')  # ✅ Renders dashboard when accessed via GET


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)



