import logging
from datetime import datetime
from bson import ObjectId
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.services.creditService import initialize_credits

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self):
        self.account_collection = collection.database.Accounts
        self.user_collection = collection.database.Users
        self.team_service = None

    def set_team_service(self, team_service: TeamService):
        self.team_service = team_service

    def create_account_if_not_exists(self, user_id, email, **kwargs):
        """
        Creates a new account for the user if one does not exist, or returns the existing account.
        Args:
            user_id (str): The ID of the user.
            email (str): The user's email.
            **kwargs: Optional fields (e.g., subscriptionId, creditId, isCompany, companyName, etc.).
        Returns: (account, status_code)
        """
        try:
            # Validate inputs
            if not user_id or not isinstance(user_id, str):
                logger.error(f"Invalid user_id: {user_id}")
                return {"error": "Invalid or missing user_id"}, 400
            if not email or not isinstance(email, str):
                logger.error(f"Invalid email: {email}")
                return {"error": "Invalid or missing email"}, 400

            # Check if an account already exists for the user
            logger.debug(f"Checking for existing account with user_id: {user_id}")
            existing_account = self.account_collection.find_one({"userId": user_id})
            if existing_account:
                logger.info(
                    f"Account already exists for user {user_id}: {existing_account['_id']}"
                )
                return existing_account, 200

            # Create a new account
            account_data = {
                "_id": str(ObjectId()),
                "ownerId": user_id,
                "email": email,
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
                "isActive": kwargs.get("isActive", True),
                "subscriptionId": kwargs.get("subscriptionId", str(ObjectId())),
                "creditId": kwargs.get("creditId", str(ObjectId())),
                "isCompany": kwargs.get("isCompany", False),
                "companyName": kwargs.get("companyName", ""),
                "subscriptionStatus": kwargs.get("subscriptionStatus", "active"),
                "subscriptionStart": kwargs.get(
                    "subscriptionStart", datetime.utcnow().isoformat()
                ),
                "subscriptionEnd": kwargs.get("subscriptionEnd"),
                "referralBonus": kwargs.get("referralBonus", 0),
                "isFirstLogin": kwargs.get("isFirstLogin", True),
            }
            logger.debug(f"Attempting to create account with data: {account_data}")
            result = self.account_collection.insert_one(account_data)
            if result.inserted_id:
                logger.info(
                    f"New account created for user {user_id}: {account_data['_id']}"
                )
                # Initialize credits if ownerId is provided
                if "ownerId" in kwargs:
                    logger.debug(
                        f"Initializing credits for ownerId: {kwargs['ownerId']}"
                    )
                    try:
                        initialize_credits(kwargs["ownerId"])
                    except Exception as credit_error:
                        logger.error(
                            f"Failed to initialize credits for ownerId {kwargs['ownerId']}: {str(credit_error)}"
                        )
                return account_data, 201
            else:
                logger.error(
                    f"Failed to insert account for user {user_id}: No inserted_id returned"
                )
                return {"error": "Failed to create account due to database error"}, 500

        except Exception as e:
            logger.error(
                f"Error creating account for user {user_id}: {str(e)}", exc_info=True
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def determine_active_account(self, user_id, user_account, team_list):
        try:
            if not team_list:
                return user_account

            for team in team_list:
                team_account = self.account_collection.find_one(
                    {"_id": team.get("accountId")}
                )
                if team_account and team_account.get("isActive"):
                    return team_account
            return user_account
        except Exception as e:
            logger.error(
                f"Error determining active account for user {user_id}: {str(e)}",
                exc_info=True,
            )
            return None
