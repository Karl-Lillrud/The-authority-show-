import logging
import uuid
from datetime import datetime, timedelta, timezone
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)


class TeamInviteRepository:
    def __init__(self):
        self.invites_collection = collection.database.Invites
        self.teams_collection = collection.database.Teams
        self.users_collection = collection.database.Users
        self.accounts_collection = collection.database.Accounts

    def save_invite(self, team_id, email, inviter_id, role):
        """
        Create a new team invite and save it to the database.
        Raises ValueError for invalid inputs or permissions.
        Returns the invite token on success.
        """
        team = self.teams_collection.find_one({"_id": team_id})
        if not team:
            logger.error(f"Team with ID {team_id} not found")
            raise ValueError(f"Team with ID {team_id} not found")

        # Check if user has permission to invite
        inviter_account = self.accounts_collection.find_one({"userId": inviter_id})
        if not inviter_account:
            logger.error(f"No account found for user {inviter_id}")
            raise ValueError("User not authorized to send invites")

        normalized_email = email.lower().strip()

        # Check if an active invite already exists for this email and team
        existing_invite = self.invites_collection.find_one(
            {
                "teamId": team_id,
                "email": normalized_email,
                "status": "pending",
                "createdAt": {
                    "$gt": datetime.now(timezone.utc) - timedelta(hours=24)
                },  # Expire after 24 hours
            }
        )

        if existing_invite:
            logger.info(
                f"Found existing active invite for {normalized_email} to team {team_id}"
            )
            return existing_invite["_id"]

        # Generate invite token
        invite_token = str(uuid.uuid4())

        # Create invite document with a 24-hour expiration
        invite_data = {
            "_id": invite_token,
            "teamId": team_id,
            "teamName": team.get("name", "Team"),  # Include team name for email
            "email": normalized_email,
            "inviterId": inviter_id,
            "role": role,  # Include role in the invite
            "createdAt": datetime.now(timezone.utc),
            "expiresAt": datetime.now(timezone.utc) + timedelta(hours=24),
            "status": "pending",
        }

        # Insert invite into database
        self.invites_collection.insert_one(invite_data)
        logger.info(
            f"Created new invite {invite_token} for {normalized_email} to team {team_id}"
        )

        return invite_token

    def get_invite(self, invite_token):
        """
        Retrieve an invite by token.
        Returns the invite document or None if not found.
        """
        invite = self.invites_collection.find_one({"_id": invite_token})
        return invite

    def get_team_invites(self, team_id):
        """
        Get all pending invites for a specific team.
        Returns a list of invite documents.
        """
        invites = list(
            self.invites_collection.find({"teamId": team_id, "status": "pending"})
        )
        return invites

    def get_user_invites(self, email):
        """
        Get all pending invites for a specific email.
        Returns a list of invite documents.
        """
        normalized_email = email.lower().strip()
        invites = list(
            self.invites_collection.find(
                {"email": normalized_email, "status": "pending"}
            )
        )
        return invites

    def mark_invite_accepted(self, invite_token):
        """
        Mark an invite as accepted.
        Returns a tuple containing a result dict and a success boolean.
        """
        invite = self.get_invite(invite_token)

        if not invite:
            logger.warning(f"Invite {invite_token} not found")
            return {"error": "Invite not found"}, False

        # Ensure `expiresAt` is a valid datetime
        expires_at = invite.get("expiresAt")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                logger.error(f"Invalid datetime format for invite {invite_token}")
                return {"error": "Invalid invite expiration format"}, False

        if expires_at and expires_at < datetime.now(timezone.utc):
            logger.warning(f"Invite {invite_token} has expired")
            # Update status to expired
            self.invites_collection.update_one(
                {"_id": invite_token}, {"$set": {"status": "expired"}}
            )
            return {"error": "This invite has expired."}, False

        if invite.get("status") == "accepted":
            logger.info(f"Invite {invite_token} was already accepted")
            return {"message": "Invite already accepted."}, True

        # Check if the user registered with the invited email
        registered_user = self.users_collection.find_one({"email": invite["email"]})

        if not registered_user:
            logger.warning(f"User with email {invite['email']} has not registered yet")
            return {"error": "User has not registered yet."}, False

        result = self.invites_collection.update_one(
            {"_id": invite_token},

            {
                "$set": {
                    "status": "accepted",
                    "acceptedAt": datetime.now(timezone.utc),
                    "registeredUserId": registered_user[
                        "_id"
                    ],  # Store user ID for reference
                }
            },
        )

        if result.modified_count == 1:
            logger.info(
                f"Invite {invite_token} marked as accepted for user {registered_user['_id']}"
            )

            {"$set": {
                "status": "accepted", 
                "acceptedAt": datetime.now(timezone.utc),  # Proper datetime object, not string
                "registeredUserId": registered_user["_id"]  # Store user ID for reference
            }}
        )

        if result.modified_count == 1:
            logger.info(f"Invite {invite_token} marked as accepted for user {registered_user['_id']}")
            
            # Immediately delete the invite after 5 minutes (alternative approach)
            # This won't work for scheduling but shows intent
            # In practice, you would set up a scheduled task for this
            self.schedule_accepted_invite_deletion(invite_token)
            

            return {"message": "Invite accepted successfully"}, True
        else:
            logger.warning(f"Failed to mark invite {invite_token} as accepted")
            return {"error": "Failed to accept invite"}, False
            
    def schedule_accepted_invite_deletion(self, invite_token):
        """
        Schedule deletion of an accepted invite.
        In a real implementation, this would set up a scheduled task.
        For demonstration, we just log the intent.
        """
        logger.info(f"Scheduled deletion of accepted invite {invite_token} in 5 minutes")
        # In a real system, you would use a task scheduler like Celery here
        # For example:
        # delete_accepted_invite.apply_async(args=[invite_token], countdown=300)  # 5 minutes
        
    def cancel_invite(self, invite_token, user_id):
        """
        Cancel a pending invite.
        Returns a tuple containing a result dict and a success boolean.
        """
        invite = self.get_invite(invite_token)

        if not invite:
            return {"error": "Invite not found"}, False

        # Ensure `expiresAt` is a valid datetime before comparing
        expires_at = invite.get("expiresAt")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                logger.error(f"Invalid datetime format for invite {invite_token}")
                return {"error": "Invalid invite expiration format"}, False

        # If the invite is expired, automatically cancel it
        if invite["status"] == "expired" or (
            expires_at and expires_at < datetime.now(timezone.utc)
        ):
            self.invites_collection.update_one(
                {"_id": invite_token}, {"$set": {"status": "cancelled"}}
            )
            logger.info(f"Invite {invite_token} was expired and is now cancelled")
            return {"message": "Invite was expired and has been cancelled."}, True

        # Check permission - only the inviter or team admin can cancel manually
        if invite["inviterId"] != user_id:
            team_member = self.teams_collection.find_one(
                {
                    "_id": invite["teamId"],
                    "members": {"$elemMatch": {"userId": user_id, "role": "admin"}},
                }
            )

            if not team_member:
                return {"error": "Permission denied"}, False

        # Manually cancel invite if still pending
        result = self.invites_collection.update_one(
            {"_id": invite_token, "status": "pending"},
            {"$set": {"status": "cancelled"}},
        )

        if result.modified_count == 1:
            return {"message": "Invite cancelled successfully"}, True
        else:
            return {"error": "Failed to cancel invite"}, False

    def cleanup_old_invites(self):
        """
        Delete expired, old pending, and recently accepted invites from the database.
        Returns a dict with counts of deleted documents.
        """

        # Delete expired invites (more than 7 days old)
        result_expired = self.invites_collection.delete_many(
            {
                "status": "expired",
                "expiresAt": {"$lt": datetime.now(timezone.utc) - timedelta(days=3)},
            }
        )
        logger.info(f"Deleted {result_expired.deleted_count} expired invites")

        # Delete unused invites that are still "pending" after 30 days
        result_pending = self.invites_collection.delete_many(
            {
                "status": "pending",
                "createdAt": {"$lt": datetime.now(timezone.utc) - timedelta(days=10)},
            }
        )

        # Delete expired invites (more than 3 days old)
        result_expired = self.invites_collection.delete_many({
            "status": "expired",
            "expiresAt": {"$lt": datetime.now(timezone.utc) - timedelta(days=3)}
        })
        logger.info(f"Deleted {result_expired.deleted_count} expired invites")

        # Delete unused invites that are still "pending" after 10 days
        result_pending = self.invites_collection.delete_many({
            "status": "pending",
            "createdAt": {"$lt": datetime.now(timezone.utc) - timedelta(days=10)}
        })

        logger.info(f"Deleted {result_pending.deleted_count} old pending invites")
        
        # Delete accepted invites that are more than 5 minutes old
        # Handle both string and datetime formats for acceptedAt
        current_time = datetime.now(timezone.utc)
        five_mins_ago = current_time - timedelta(minutes=5)
        
        # First, try to delete documents with proper datetime objects
        result_accepted_datetime = self.invites_collection.delete_many({
            "status": "accepted",
            "acceptedAt": {"$type": "date", "$lt": five_mins_ago}
        })
        
        # Then handle string format dates (for backward compatibility with existing data)
        # This is complex and might not be perfect - better to fix data format going forward
        # This is a simplified approach that might need adjustment
        five_mins_ago_str = five_mins_ago.isoformat()
        result_accepted_string = self.invites_collection.delete_many({
            "status": "accepted",
            "acceptedAt": {"$type": "string", "$lt": five_mins_ago_str}
        })
        
        total_accepted_deleted = result_accepted_datetime.deleted_count + result_accepted_string.deleted_count
        logger.info(f"Deleted {total_accepted_deleted} accepted invites (older than 5 minutes)")

        return {
            "expired_deleted": result_expired.deleted_count,
            "pending_deleted": result_pending.deleted_count,


            "accepted_deleted": total_accepted_deleted

        }

    def mark_expired_invites(self):
        """
        Mark invites as expired if they've passed their expiration date.
        Returns the count of newly marked expired invites.
        """
        result = self.invites_collection.update_many(
            {"status": "pending", "expiresAt": {"$lt": datetime.now(timezone.utc)}},
            {"$set": {"status": "expired"}},
        )

        logger.info(f"Marked {result.modified_count} invites as expired")
        return result.modified_count


        
    def fix_string_dates(self):
        """
        One-time fix to convert string dates to proper MongoDB datetime objects.
        Returns the count of fixed documents.
        """
        # Find documents with string acceptedAt
        string_date_docs = list(self.invites_collection.find(
            {"status": "accepted", "acceptedAt": {"$type": "string"}}
        ))
        
        fixed_count = 0
        for doc in string_date_docs:
            try:
                # Parse the string date
                date_str = doc["acceptedAt"]
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                # Update the document
                result = self.invites_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"acceptedAt": parsed_date}}
                )
                
                if result.modified_count == 1:
                    fixed_count += 1
            except (ValueError, KeyError) as e:
                logger.error(f"Error fixing date format for invite {doc.get('_id')}: {str(e)}")
                
        logger.info(f"Fixed date format for {fixed_count} invites")
        return fixed_count

