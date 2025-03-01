from backend.database.mongo_connection import collection
from datetime import datetime
import uuid


def create_account(account_data):
    try:
        account_id = str(uuid.uuid4())
        account_document = {
            "_id": account_id,
            "ownerId": account_data["userId"],
            "email": account_data["email"],
            "companyName": account_data.get("companyName", ""),
            "isCompany": account_data.get("isCompany", False),
            "createdAt": datetime.utcnow().isoformat(),
            "isActive": True,
        }
        collection.database.Accounts.insert_one(account_document)
        return {"success": True, "accountId": account_id}
    except Exception as e:
        return {"success": False, "details": str(e)}
