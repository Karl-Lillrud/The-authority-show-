import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
import logging

logger = logging.getLogger(__name__)

class PodcastRepository:
    def __init__(self):
        self.collection = collection.database.Podcasts

    def add_podcast(self, user_id, data):
        try:
            # Fetch the account document for the logged-in user
            user_account = collection.database.Accounts.find_one({"userId": user_id})
            if not user_account:
                raise ValueError("No account associated with this user")

            # Get the account ID
            account_id = user_account.get("id", str(user_account["_id"]))
            logger.info(f"Found account {account_id} for user {user_id}")

            # Inject the accountId into the data
            data["accountId"] = account_id
            
            # Validate data using PodcastSchema
            schema = PodcastSchema()
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            validated_data = schema.load(data)
            
            # Ensure account exists and belongs to the user
            account_query = {"userId": user_id, "id": account_id} if "id" in user_account else {"userId": user_id, "_id": user_account["_id"]}
            account = collection.database.Accounts.find_one(account_query)
            if not account:
                raise ValueError("Invalid account ID or no permission to add podcast.")
            
            # Generate a unique podcast ID
            podcast_id = str(uuid.uuid4())
            podcast_item = {
                "_id": podcast_id,
                "teamId": validated_data.get("teamId"),
                "accountId": account_id,
                "podName": validated_data.get("podName"),
                "ownerName": validated_data.get("ownerName"),
                "hostName": validated_data.get("hostName"),
                "rssFeed": validated_data.get("rssFeed"),
                "googleCal": validated_data.get("googleCal"),
                "podUrl": validated_data.get("podUrl"),
                "guestUrl": validated_data.get("guestUrl"),
                "socialMedia": validated_data.get("socialMedia", []),
                "email": validated_data.get("email"),
                "description": validated_data.get("description"),
                "logoUrl": validated_data.get("logoUrl"),
                "category": validated_data.get("category"),
                "defaultTasks": validated_data.get("defaultTasks", ""),  # Empty string if not provided
                "created_at": datetime.now(timezone.utc),
            }

            # Insert into database
            result = self.collection.insert_one(podcast_item)
            if result.inserted_id:
                return {"message": "Podcast added successfully", "podcast_id": podcast_id, "redirect_url": "/index.html"}, 201
            else:
                raise ValueError("Failed to add podcast.")

        except ValueError as e:
            # Handle specific business logic errors
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400  # Specific business error
            else:
                return {"error": e.args[0], "details": e.args[1]}, 400  # Validation errors

        except Exception as e:
            # Catch any unexpected errors (e.g., database issues)
            logger.error(f"Error adding podcast: {str(e)}")
            return {"error": "Failed to add podcast", "details": str(e)}, 500
        
    def get_podcasts(self, user_id):
        try:
            user_accounts = list(collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1}))
            user_account_ids = [account.get("id", str(account["_id"])) for account in user_accounts]

            if not user_account_ids:
                return {"podcast": []}, 200  # No podcasts if no accounts

            podcasts = list(self.collection.find({"accountId": {"$in": user_account_ids}}))
            for podcast in podcasts:
                podcast["_id"] = str(podcast["_id"])

            return {"podcast": podcasts}, 200

        except Exception as e:
            logger.error(f"Error fetching podcasts: {str(e)}")
            return {"error": "Failed to fetch podcasts", "details": str(e)}, 500

    def get_podcast_by_id(self, user_id, podcast_id):
        try:
            user_accounts = list(collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1}))
            user_account_ids = [account.get("id", str(account["_id"])) for account in user_accounts]

            if not user_account_ids:
                return {"error": "No accounts found for user"}, 403

            podcast = self.collection.find_one({"_id": podcast_id, "accountId": {"$in": user_account_ids}})
            if not podcast:
                return {"error": "Podcast not found or unauthorized"}, 404

            podcast["_id"] = str(podcast["_id"])
            return {"podcast": podcast}, 200
        except Exception as e:
            logger.error(f"Error fetching podcast: {e}")
            return {"error": f"Failed to fetch podcast: {str(e)}"}, 500
        

    def delete_podcast(self, user_id, podcast_id):
        try:
            # Fetch user account IDs
            user_accounts = list(collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1}))
            user_account_ids = [account.get("id", str(account["_id"])) for account in user_accounts]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one({"_id": podcast_id, "accountId": {"$in": user_account_ids}})
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Perform delete operation
            result = self.collection.delete_one({"_id": podcast_id})
            if result.deleted_count == 1:
                return {"message": "Podcast deleted successfully"}, 200
            else:
                return {"error": "Failed to delete podcast"}, 500

        except ValueError as e:
            # Handle specific errors like no accounts found or podcast not found
            return {"error": str(e)}, 400  # Return a 400 Bad Request for known business errors

        except Exception as e:
            # Catch any unexpected errors (e.g., database connection issues)
            logger.error(f"Error deleting podcast: {str(e)}")
            return {"error": "Failed to delete podcast", "details": str(e)}, 500
        
    def edit_podcast(self, user_id, podcast_id, data):
        try:
            # Fetch user account IDs
            user_accounts = list(collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1}))
            user_account_ids = [account.get("id", str(account["_id"])) for account in user_accounts]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one({"_id": podcast_id, "accountId": {"$in": user_account_ids}})
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Validate input data using schema
            schema = PodcastSchema(partial=True)
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            # Prepare update data by filtering out None values
            update_data = {key: value for key, value in data.items() if value is not None}
            if not update_data:
                return {"message": "No update data provided"}, 200  # No actual update needed

            # Perform update operation
            result = self.collection.update_one({"_id": podcast_id}, {"$set": update_data})

            if result.modified_count == 1:
                return {"message": "Podcast updated successfully"}, 200
            else:
                return {"message": "No changes made to the podcast"}, 200

        except ValueError as e:
            # Specific business logic error
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400  # Return specific error with 400 for bad input
            else:
                return {"error": e.args[0], "details": e.args[1]}, 400  # For validation errors

        except Exception as e:
            # Catch any unexpected errors (e.g., database connection issues)
            logger.error(f"Error updating podcast: {str(e)}")
            return {"error": "Failed to update podcast", "details": str(e)}, 500

        
    

