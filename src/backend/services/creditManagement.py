import logging
from datetime import datetime, timezone
from backend.database.mongo_connection import get_db # Assuming you have this helper
from backend.models.credits import CreditsSchema, CreditHistoryEntrySchema # Import schemas

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self):
        self.db = get_db()
        self.credits_collection = self.db.Credits # Or your specific collection name
        self.schema = CreditsSchema()
        self.history_schema = CreditHistoryEntrySchema()

    def _get_raw_credits(self, user_id: str):
        """Internal helper to fetch the raw document."""
        return self.credits_collection.find_one({"user_id": user_id})

    def _log_transaction(self, user_id: str, transaction_data: dict):
        """Internal helper to add a transaction to the history."""
        try:
            # Validate history entry data
            entry = self.history_schema.load(transaction_data)
            self.credits_collection.update_one(
                {"user_id": user_id},
                {"$push": {"creditsHistory": entry}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log credit transaction for user {user_id}: {e}", exc_info=True)
            return False

    def get_store_credits(self, user_id: str) -> dict | None:
        """Gets user credits, initializes if not found, and calculates availableCredits."""
        credits_doc = self._get_raw_credits(user_id)
        if not credits_doc:
            logger.info(f"No credits found for user {user_id}. Initializing.")
            initialized = self.initialize_credits(user_id)
            if not initialized:
                logger.error(f"Failed to initialize credits for user {user_id}.")
                return None
            credits_doc = self._get_raw_credits(user_id) # Fetch again after init

        if not credits_doc: # Still none after init attempt? Problem.
             logger.error(f"Could not retrieve or initialize credits for user {user_id}.")
             return None

        # Calculate available credits dynamically
        credits_doc['availableCredits'] = credits_doc.get('subCredits', 0) + credits_doc.get('storeCredits', 0)
        credits_doc['availableCredits'] = credits_doc.get('subCredits', 0) + credits_doc.get('storeCredits', 0)

        # Convert ObjectId to string for frontend compatibility if needed
        if '_id' in credits_doc:
            credits_doc['_id'] = str(credits_doc['_id'])

        # Remove internal tracking fields before returning if desired
        credits_doc.pop('lastSubResetMonth', None)
        credits_doc.pop('lastSubResetYear', None)

        return credits_doc

    def initialize_credits(self, user_id: str, initial_sub=0, initial_user=0, carry_over=True) -> bool:
        """Initializes credit document for a new user if it doesn't exist."""
        if self._get_raw_credits(user_id):
            logger.warning(f"Credits already exist for user {user_id}. Skipping initialization.")
            return True # Indicate it exists or was just created

        now = datetime.now(timezone.utc)
        initial_data = {
            "user_id": user_id,
            "subCredits": initial_sub,
            "storeCredits": initial_user,
            "usedCredits": 0,
            "lastUpdated": now,
            "carryOverStoreCredits": carry_over,
            "lastSubResetMonth": None, # Explicitly null on init
            "lastSubResetYear": None,
            "creditsHistory": []
        }

        try:
            # Validate initial data
            validated_data = self.schema.load(initial_data)
            result = self.credits_collection.insert_one(validated_data)
            logger.info(f"Successfully initialized credits for user {user_id} with ID {result.inserted_id}")

            # Log initial grants if any
            if initial_sub > 0:
                self._log_transaction(user_id, {
                    "type": "initial_sub", "amount": initial_sub,
                    "description": "Initial Subscription Credits Grant",
                    "balance_after": {"subCredits": initial_sub, "storeCredits": initial_user}
                })
            if initial_user > 0:
                 self._log_transaction(user_id, {
                    "type": "initial_user", "amount": initial_user,
                    "description": "Initial User Credits Grant",
                    "balance_after": {"subCredits": initial_sub, "storeCredits": initial_user}
                })
            return True
        except Exception as e:
            logger.error(f"Error initializing credits for user {user_id}: {e}", exc_info=True)
            return False

    def add_credits(self, user_id: str, amount: int, credit_type: str, description: str) -> bool:
        """Adds credits (either subCredits or storeCredits)."""
        """Adds credits (either subCredits or storeCredits)."""
        if amount <= 0:
            logger.error(f"Amount must be positive to add credits for user {user_id}.")
            return False
        
        if credit_type not in ["subCredits", "storeCredits"]:
            logger.error(f"Invalid credit_type '{credit_type}' for user {user_id}.")
            return False

        now = datetime.now(timezone.utc)
        update_result = self.credits_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {credit_type: amount},
                "$set": {"lastUpdated": now}
            }
        )

        if update_result.matched_count == 0:
            logger.error(f"Cannot add credits: User {user_id} not found.")
            return False
        if update_result.modified_count == 0:
             logger.warning(f"Credits not added for user {user_id} (no change or error).")
             # Could happen if update didn't actually change value, but log warning
             return False # Or True depending on desired behavior on no-op

        logger.info(f"Added {amount} {credit_type} to user {user_id}. Description: {description}")

        # Fetch updated balances for logging
        updated_doc = self._get_raw_credits(user_id)
        sub_bal = updated_doc.get('subCredits', 0)
        user_bal = updated_doc.get('storeCredits', 0)

        log_type = "monthly_sub_grant" if credit_type == "subCredits" else "purchase" # Adjust as needed
        self._log_transaction(user_id, {
            "type": log_type,
            "amount": amount,
            "description": description,
            "balance_after": {"subCredits": sub_bal, "storeCredits": user_bal}
        })
        return True

    def consume_credits(self, user_id: str, amount_to_consume: int, description: str) -> bool:
        """Consumes credits, prioritizing subCredits."""
        """Consumes credits, prioritizing subCredits."""
        if amount_to_consume <= 0:
            logger.error(f"Amount to consume must be positive for user {user_id}.")
            return False

        credits_doc = self._get_raw_credits(user_id)
        if not credits_doc:
            logger.error(f"Cannot consume credits: User {user_id} not found.")
            # Optionally initialize here if desired behavior
            # self.initialize_credits(user_id)
            # credits_doc = self._get_raw_credits(user_id)
            # if not credits_doc: return False
            return False

        current_sub = credits_doc.get('subCredits', 0)
        current_user = credits_doc.get('storeCredits', 0)
        available = current_sub + current_user

        if available < amount_to_consume:
            logger.warning(f"Insufficient credits for user {user_id}. Available: {available}, Required: {amount_to_consume}")
            return False

        sub_consumed = min(current_sub, amount_to_consume)
        user_consumed = amount_to_consume - sub_consumed # Consume from storeCredits only if subCredits weren't enough

        new_sub = current_sub - sub_consumed
        new_user = current_user - user_consumed
        new_total_used = credits_doc.get('usedCredits', 0) + amount_to_consume
        now = datetime.now(timezone.utc)

        update_result = self.credits_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "subCredits": new_sub,
                    "storeCredits": new_user,
                    "usedCredits": new_total_used,
                    "lastUpdated": now
                }
            }
        )

        if update_result.modified_count == 0:
             logger.error(f"Failed to update credits after consumption calculation for user {user_id}.")
             return False # Indicates an issue during the update phase

        logger.info(f"Consumed {amount_to_consume} credits (sub_consumed) sub, {user_consumed} User) for user {user_id}. Description: {description}")
        self._log_transaction(user_id, {
            "type": "consumption",
            "amount": -amount_to_consume, # Log consumption as negative
            "description": description,
            "balance_after": {"subCredits": new_sub, "storeCredits": new_user}
        })
        return True

    def perform_monthly_reset(self, user_id: str, new_sub_allowance: int) -> bool:
        """Resets subCredits and optionally storeCredits based on carryOver flag."""
        now = datetime.now(timezone.utc)
        current_month = now.month
        current_year = now.year

        credits_doc = self._get_raw_credits(user_id)
        if not credits_doc:
            logger.error(f"Cannot reset credits: User {user_id} not found.")
            return False

        last_reset_month = credits_doc.get('lastSubResetMonth')
        last_reset_year = credits_doc.get('lastSubResetYear')

        # Check if reset for this month/year already happened
        if last_reset_year == current_year and last_reset_month == current_month:
            logger.info(f"Monthly reset already performed for user {user_id} in {current_month}/{current_year}. Skipping.")
            return True # Indicate reset is up-to-date

        # --- Perform Reset ---
        updates = {
            "subCredits": new_sub_allowance, # Set to new allowance
            "lastUpdated": now,
            "lastSubResetMonth": current_month,
            "lastSubResetYear": current_year
        }
        log_entries = []

        # Log the reset of old subscription credits
        old_sub = credits_doc.get('subCredits', 0)
        if old_sub > 0 :
             log_entries.append(self.history_schema.load({
                "type": "sub_reset", "amount": -old_sub,
                "description": f"Reset previous month's subscription credits ({current_month-1 if current_month > 1 else 12}/{current_year if current_month > 1 else current_year-1})",
             }))

        # Handle storeCredits carry-over
        old_user = credits_doc.get('storeCredits', 0)
        if not credits_doc.get('carryOverStoreCredits', True):
            updates["storeCredits"] = 0 # Reset user credits if carryOver is False
            if old_user > 0:
                log_entries.append(self.history_schema.load({
                    "type": "user_reset", "amount": -old_user,
                    "description": "Reset non-carryover user credits"
                }))
            new_user_bal = 0
        else:
            new_user_bal = old_user # User credits remain unchanged

        # Log the grant of new subscription credits
        if new_sub_allowance > 0:
            log_entries.append(self.history_schema.load({
                "type": "monthly_sub_grant", "amount": new_sub_allowance,
                "description": f"Monthly subscription credit grant for {current_month}/{current_year}",
                "balance_after": {"subCredits": new_sub_allowance, "storeCredits": new_user_bal}
            }))

        update_result = self.credits_collection.update_one(
            {"user_id": user_id},
            {
                "$set": updates,
                "$push": {"creditsHistory": {"$each": log_entries}} if log_entries else None # Push logs atomically if possible
            }
        )
         # Handle case where $push might not be applicable if log_entries is empty
        if not log_entries:
             update_result = self.credits_collection.update_one(
                {"user_id": user_id},
                {"$set": updates}
             )


        if update_result.modified_count == 0:
             # Could happen if the new allowance is the same as old and user credits didn't reset
             logger.warning(f"Monthly reset for user {user_id} resulted in no document modification (might be okay).")
             # Still update the reset tracking fields if they were null before
             if last_reset_month is None or last_reset_year is None:
                 self.credits_collection.update_one(
                     {"user_id": user_id},
                     {"$set": {
                         "lastUpdated": now,
                         "lastSubResetMonth": current_month,
                         "lastSubResetYear": current_year
                     }}
                 )
             # Consider this a success if the state is now correct for the month
             return True


        logger.info(f"Monthly reset completed for user {user_id} for {current_month}/{current_year}. New Subscription Credits: {new_sub_allowance}")
        return True

    def set_carry_over(self, user_id: str, carry_over: bool) -> bool:
        """Sets the carryOverStoreCredits flag for a user."""
        now = datetime.now(timezone.utc)
        result = self.credits_collection.update_one(
            {"user_id": user_id},
            {"$set": {"carryOverStoreCredits": carry_over, "lastUpdated": now}}
        )
        if result.matched_count == 0:
            logger.error(f"Cannot set carry over: User {user_id} not found.")
            return False
        logger.info(f"Set carryOverStoreCredits to {carry_over} for user {user_id}.")
        return True