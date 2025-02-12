from flask import Blueprint, request, jsonify, url_for, render_template
from azure.cosmos import CosmosClient, exceptions
import os
import uuid
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import string

# ✅ Define Blueprint
register_bp = Blueprint('register_bp', __name__)

# Load environment variables
load_dotenv()

# Azure Cosmos DB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize Cosmos DB client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

def generate_referral_code():
    """Genererar en unik 8-teckens referral-kod"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register/register.html')

    if request.content_type == "application/json":
        data = request.get_json()
    else:
        data = request.form  

    # 🛠️ Debugging - Se vad som skickas med i registreringen
    print(f"🛠️ Debugging Referral: Raw data received -> {data}")
    print(f"🔹 Extracted Referral Code: {data.get('referral', 'No referral code found')}")

    if "email" not in data or "password" not in data:
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)
    referral_code = generate_referral_code()  # 🟢 Skapa en unik kod
    referrer_code = data.get("referral", "").strip()  # 🟢 Hämta referral-kod från URL

    print(f"📩 New Registration Attempt: {email} | Referral Code Used: {referrer_code}")

    # Kontrollera om användaren redan finns
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    existing_users = list(container.query_items(
        query=query, parameters=parameters, enable_cross_partition_query=True
    ))

    if existing_users:
        return jsonify({"error": "Email already registered."}), 409

    # Skapa användare med 3000 credits och en unik referral-kod
    user_document = {
        "id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": hashed_password,
        "createdAt": datetime.utcnow().isoformat(),
        "partitionKey": email,
        "credits": 3000,
        "credits_expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "referral_code": referral_code,  # 🟢 Spara referral-koden
        "referred_by": referrer_code if referrer_code else None  # 🟢 Spara referrer om den finns
    }

    try:
        container.create_item(body=user_document)
        print(f"✅ New user created: {email} | Referral Code: {referral_code}")

        # 🟢 Om användaren registrerade sig via en referral-kod, ge 200 extra credits till referrern
        if referrer_code:
            print(f"🔍 Checking referrer: {referrer_code}")  # ✅ Debug-logg

            query = "SELECT * FROM c WHERE c.referral_code = @referral_code"
            params = [{"name": "@referral_code", "value": referrer_code}]
            referrer_users = list(container.query_items(
                query=query, parameters=params, enable_cross_partition_query=True
            ))

            if referrer_users:
                referrer = referrer_users[0]
                print(f"✅ Found referrer: {referrer['email']} - Adding 200 credits!")  # ✅ Debug-logg

                referrer["credits"] += 200
                container.replace_item(referrer["id"], referrer)
                print(f"🎉 {referrer['email']} now has {referrer['credits']} credits!")

            else:
                print(f"❌ No referrer found with code {referrer_code}")

        return jsonify({
            "message": "Registration successful!",
            "credits": user_document["credits"],
            "credits_expires_at": user_document["credits_expires_at"],
            "referral_code": referral_code,  # 🟢 Skicka referral-koden till frontend
            "redirect_url": url_for('signin', _external=True)
        }), 201

    except exceptions.CosmosHttpResponseError as e:
        print(f"❌ Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
