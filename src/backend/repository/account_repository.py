import uuid
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.services.creditService import initialize_credits
import logging

logger = logging.getLogger(__name__)


class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts

    def create_account(self, data):
        try:
            if not data or "ownerId" not in data or "email" not in data:
                return {"error": "ownerId och email krävs"}, 400

            existing_account = self.collection.find_one(
                {"$or": [{"email": data["email"]}, {"ownerId": data["ownerId"]}]}
            )
            if existing_account:
                return {"error": "Konto finns redan för denna email eller ägare"}, 400

            account_id = str(uuid.uuid4())
            account_document = {
                "_id": account_id,
                "ownerId": data["ownerId"],
                "email": data["email"],
                "subscriptionId": data.get("subscriptionId", str(uuid.uuid4())),
                "creditId": data.get("creditId", str(uuid.uuid4())),
                "isCompany": data.get("isCompany", False),
                "companyName": data.get("companyName", ""),
                "subscriptionStatus": data.get("subscriptionStatus", "active"),
                "createdAt": datetime.utcnow(),
                "referralBonus": data.get("referralBonus", 0),
                "subscriptionStart": datetime.utcnow(),
                "subscriptionEnd": data.get("subscriptionEnd"),
                "isActive": data.get("isActive", True),
                "created_at": datetime.utcnow(),
                "isFirstLogin": data.get("isFirstLogin", True),
            }
            self.collection.insert_one(account_document)
            logger.info(f"Konto skapat: {account_id}")
            initialize_credits(data["ownerId"])
            return {"message": "Konto skapat", "accountId": account_id}, 201

        except Exception as e:
            logger.error(f"Fel vid skapande av konto: {e}", exc_info=True)
            return {"error": f"Fel vid skapande av konto: {str(e)}"}, 500

    def get_account(self, account_id):
        try:
            account = self.collection.find_one({"_id": account_id})
            if not account:
                return {"error": "Konto hittades inte"}, 404
            return {"account": account}, 200
        except Exception as e:
            logger.error(f"Fel vid hämtning av konto: {e}", exc_info=True)
            return {"error": f"Fel vid hämtning av konto: {str(e)}"}, 500

    def get_account_by_user(self, user_id):
        try:
            account = self.collection.find_one({"ownerId": user_id})
            if not account:
                return {"error": "Konto hittades inte"}, 404
            return {"account": account}, 200
        except Exception as e:
            logger.error(f"Fel vid hämtning av konto: {e}", exc_info=True)
            return {"error": f"Fel vid hämtning av konto: {str(e)}"}, 500

    def edit_account(self, user_id, data):
        try:
            updates = {k: v for k, v in data.items() if v is not None}
            if not updates:
                return {"error": "Inga giltiga fält angivna för uppdatering"}, 400

            result = self.collection.update_one({"ownerId": user_id}, {"$set": updates})
            if result.matched_count == 0:
                return {"error": "Konto hittades inte"}, 404

            return {"message": "Konto uppdaterat framgångsrikt"}, 200
        except Exception as e:
            logger.error(f"Fel vid uppdatering av konto: {e}", exc_info=True)
            return {"error": f"Fel vid uppdatering av konto: {str(e)}"}, 500

    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"ownerId": user_id})
            logger.info(f"Raderade {result.deleted_count} konton för userId {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Fel vid radering av konton: {e}", exc_info=True)
            return 0
