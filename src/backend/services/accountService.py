import logging
from datetime import datetime
import uuid
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self):
        self.account_collection = collection.database.Accounts
        self.team_service = None  # Sätts senare för att undvika cirkulär import

    def set_team_service(self, team_service):
        """Sätt team service för att undvika cirkulär import."""
        self.team_service = team_service

    def create_account_if_not_exists(
        self, user_id, email, is_company=False, company_name=""
    ):
        """Skapa ett konto om det inte redan finns för användaren."""
        existing_account = self.account_collection.find_one(
            {"$or": [{"email": email}, {"ownerId": user_id}]}
        )
        if existing_account:
            logger.info(f"Konto finns redan för email {email} eller userId {user_id}.")
            return existing_account, 200

        account_data = {
            "_id": str(uuid.uuid4()),
            "ownerId": user_id,
            "email": email,
            "isCompany": is_company,
            "companyName": company_name,
            "subscriptionId": str(uuid.uuid4()),
            "creditId": str(uuid.uuid4()),
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow(),
            "referralBonus": 0,
            "subscriptionStart": datetime.utcnow(),
            "subscriptionEnd": None,
            "isActive": True,
            "created_at": datetime.utcnow(),
            "isFirstLogin": True,
        }
        self.account_collection.insert_one(account_data)
        logger.info(f"Konto skapat för userId {user_id}, email {email}.")
        return account_data, 201

    def get_user_account(self, user_id):
        """Hämta konto för en användare baserat på ownerId."""
        account = self.account_collection.find_one({"ownerId": user_id})
        if not account:
            logger.warning(f"Inget konto hittades för userId {user_id}.")
            return None
        logger.info(f"Konto hittades för userId {user_id}: {account['_id']}.")
        return account

    def determine_active_account(self, user_id, user_account, team_list):
        """Bestäm vilket konto som ska användas - personligt eller teamkonto."""
        if user_account:
            logger.info(f"Använder personligt konto för userId {user_id}.")
            return user_account

        if not team_list:
            logger.warning(f"Inga team hittades för userId {user_id}.")
            return None

        first_team = team_list[0]
        team_id = first_team.get("_id")
        logger.info(f"Första teamet: {team_id}")

        owner_id = (
            self.team_service.find_team_owner(team_id) if self.team_service else None
        )
        if owner_id:
            owner_account = self.get_user_account(owner_id)
            if owner_account:
                logger.info(f"Använder teamägarens konto för team {team_id}.")
                return owner_account

        member_id = (
            self.team_service.find_any_team_member(team_id)
            if self.team_service
            else None
        )
        if member_id and member_id != user_id:
            member_account = self.get_user_account(member_id)
            if member_account:
                logger.info(f"Använder teammedlems konto för team {team_id}.")
                return member_account

        logger.warning(f"Inget aktivt konto hittades för userId {user_id}.")
        return None

    def update_account(self, user_id, updates):
        """Uppdatera konto baserat på ownerId."""
        if not updates:
            logger.warning("Inga giltiga fält angivna för uppdatering.")
            return {"error": "Inga giltiga fält angivna för uppdatering"}, 400

        result = self.account_collection.update_one(
            {"ownerId": user_id}, {"$set": updates}
        )
        if result.matched_count == 0:
            logger.warning(
                f"Inget konto hittades för userId {user_id} vid uppdatering."
            )
            return {"error": "Konto hittades inte"}, 404

        logger.info(f"Konto uppdaterat för userId {user_id}.")
        return {"message": "Konto uppdaterat framgångsrikt"}, 200
