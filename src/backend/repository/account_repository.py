import uuid
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.models.accounts import AccountSchema
import logging

logger = logging.getLogger(__name__)

def create_account(data):
    try:
        if not data:
            raise ValueError("No data received or invalid JSON.")

        # Check for required fields
        if "userId" not in data or "email" not in data:
            raise ValueError("Missing required fields: userId and email")

        user_id = data["userId"]
        email = data["email"]
        company_name = data.get("companyName", "")
        is_company = data.get("isCompany", False)

        subscription_id = str(uuid.uuid4())  # Generate unique subscription ID
        account_id = str(uuid.uuid4())  # Generate unique account ID

        # Create account document
        account_document = {
            "_id": account_id,
            "userId": user_id,
            "subscriptionId": subscription_id,
            "email": email,
            "isCompany": is_company,
            "companyName": company_name,
            "paymentInfo": "",  # Placeholder for payment info
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow().isoformat(),
            "referralBonus": 0,
            "subscriptionStart": datetime.utcnow().isoformat(),
            "subscriptionEnd": "",
            "isActive": True,
        }

        # Insert account into the Accounts collection
        try:
            collection.database.Accounts.insert_one(account_document)
            logger.info("Inserting account into the database: %s", account_document)
        except Exception as db_error:
            logger.error("Database insertion error: %s", db_error, exc_info=True)
            return {"error": "Failed to insert account into the database"}, 500

        return {
            "message": "Account created successfully",
            "accountId": account_document["_id"],
        }, 201

    except ValueError as ve:
        logger.error("ValueError: %s", ve)
        return {"error": str(ve)}, 400
    except Exception as e:
        logger.error("Error creating account: %s", e, exc_info=True)
        return {"error": f"Error creating account: {str(e)}"}, 500
