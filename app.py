from flask import Flask, render_template, request, jsonify, redirect, url_for
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import os
import hashlib

# Load environment variables
load_dotenv()

# Azure Cosmos DB configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize Cosmos client (shared across app)
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

# Import and register Blueprints
from register import register_bp

app = Flask(__name__, template_folder='templates')
app.register_blueprint(register_bp, url_prefix='/api')  # Register Blueprint under '/api/register'

@app.route('/test-db', methods=['GET'])
def test_db_connection():
    try:
        users = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
        return jsonify({"message": "Database connection successful", "sample_data": users}), 200
    except Exception as e:
        return jsonify({"error": f"Database connection failed: {str(e)}"}), 500

# ✅ Serves the registration page
@app.route('/register', methods=['GET'])
def register():
    return render_template('register/register.html')

# ✅ Serves the signin page and handles login
@app.route('/', methods=['GET', 'POST'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')
    
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return redirect(url_for('signin'))
    
    email = data['email']
    password = data['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    
    if not users or users[0].get("passwordHash") != hashed_password:
        return redirect(url_for('signin'))
    
    return redirect(url_for('dashboard'))

# ✅ Serves forgot password page
@app.route('/forgotpassword', methods=['GET'])
def forgot_password():
    return render_template('forgotpassword/forgot-password.html')

# ✅ Serves dashboard page
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard/dashboard.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)