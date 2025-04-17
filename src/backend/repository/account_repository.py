import logging
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.services.accountService import AccountService

logger = logging.getLogger(__name__)


class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts
        self.account_service = AccountService()

    def create_account(self, data):
        try:
            if not data or "ownerId" not in data or "email" not in data:
                return {"error": "ownerId och email krävs"}, 400

            # Use AccountService to create or retrieve account
            account, status_code = self.account_service.create_account_if_not_exists(
                user_id=data["ownerId"],
                email=data["email"],
                ownerId=data["ownerId"],  # For initialize_credits
                subscriptionId=data.get("subscriptionId"),
                creditId=data.get("creditId"),
                isCompany=data.get("isCompany", False),
                companyName=data.get("companyName", ""),
                subscriptionStatus=data.get("subscriptionStatus", "active"),
                subscriptionStart=datetime.utcnow().isoformat(),
                subscriptionEnd=data.get("subscriptionEnd"),
                referralBonus=data.get("referralBonus", 0),
                isFirstLogin=data.get("isFirstLogin", True),
            )

            if status_code in [200, 201]:
                logger.info(
                    f"Konto {'skapat' if status_code == 201 else 'hittades'} för ownerId {data['ownerId']}: {account['_id']}"
                )
                return {
                    "message": "Konto skapat eller redan existerar",
                    "accountId": account["_id"],
                }, status_code
            else:
                logger.error(
                    f"Misslyckades att skapa/hämta konto för ownerId {data['ownerId']}: {account.get('error')}"
                )
                return {"error": account.get("error")}, status_code

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
