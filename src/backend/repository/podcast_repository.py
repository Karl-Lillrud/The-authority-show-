import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
import logging
import urllib.request
import feedparser

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

            # Inject the accountId into the data
            data["accountId"] = account_id

            if "hostBio" not in data or not data.get("hostBio"):
                logger.warning("⚠️ hostBio is missing or empty in request data")
            if "hostImage" not in data or not data.get("hostImage"):
                logger.warning("⚠️ hostImage is missing or empty in request data")

            # Validate data using PodcastSchema
            schema = PodcastSchema()
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            validated_data = schema.load(data)

            # Ensure account exists and belongs to the user
            account_query = (
                {"userId": user_id, "id": account_id}
                if "id" in user_account
                else {"userId": user_id, "_id": user_account["_id"]}
            )
            account = collection.database.Accounts.find_one(account_query)
            if not account:
                raise ValueError("Invalid account ID or no permission to add podcast.")

            # Fetch RSS feed data
            rss_url = validated_data.get("rssFeed")
            if rss_url:
                rss_data, status_code = self.fetch_rss_feed(rss_url)
                if status_code != 200:
                    raise ValueError("Failed to fetch RSS feed data")

                # Merge RSS feed data into validated_data
                validated_data.update(rss_data)

                # Always assign imageUrl to logoUrl
                if validated_data.get("imageUrl"):
                    validated_data["logoUrl"] = validated_data["imageUrl"]
                validated_data.pop("imageUrl", None)

            # Generate a unique podcast ID
            podcast_id = str(uuid.uuid4())
            podcast_item = {
                "_id": podcast_id,
                "teamId": validated_data.get("teamId"),
                "accountId": account_id,
                "podName": validated_data.get("podName"),
                "ownerName": validated_data.get("ownerName"),
                "hostName": validated_data.get("hostName"),
                "rssFeed": validated_data.get("rssFeed"),  # Ensure rssFeed is included
                "googleCal": validated_data.get("googleCal"),
                "podUrl": validated_data.get("podUrl"),
                "guestUrl": validated_data.get("guestUrl"),
                "socialMedia": validated_data.get("socialMedia", []),
                "email": validated_data.get("email"),
                "description": validated_data.get("description"),
                "logoUrl": validated_data.get("logoUrl"),
                "category": validated_data.get("category", ""),  # Fixed field
                "defaultTasks": validated_data.get(
                    "defaultTasks", ""
                ),  # Empty string if not provided
                "created_at": datetime.now(timezone.utc),
                "title": validated_data.get("title", ""),  # Added field
                "language": validated_data.get("language", ""),  # Added field
                "author": validated_data.get("author", ""),  # Added field
                "copyright_info": validated_data.get(
                    "copyright_info", ""
                ),  # Added field
                "bannerUrl": validated_data.get("bannerUrl", ""),  # Added field
                "tagline": validated_data.get("tagline", ""),  # Added field
                "hostBio": validated_data.get("hostBio", ""),  # Added field
                "hostImage": validated_data.get("hostImage", ""),  # Added field
            }

            # Insert into database
            result = self.collection.insert_one(podcast_item)
            if result.inserted_id:
                return {
                    "message": "Podcast added successfully",
                    "podcast_id": podcast_id,
                    "redirect_url": "/index.html",
                }, 201
            else:
                raise ValueError("Failed to add podcast.")

        except ValueError as e:
            # Handle specific business logic errors
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400  # Specific business error
            else:
                return {
                    "error": e.args[0],
                    "details": e.args[1],
                }, 400  # Validation errors

        except Exception as e:
            # Catch any unexpected errors (e.g., database issues)
            return {"error": "Failed to add podcast", "details": str(e)}, 500

    def get_podcasts(self, user_id):
        try:
            user_accounts = list(
                collection.database.Accounts.find(
                    {"userId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                return {"podcast": []}, 200  # No podcasts if no accounts

            podcasts = list(
                self.collection.find({"accountId": {"$in": user_account_ids}})
            )
            for podcast in podcasts:
                podcast["_id"] = str(podcast["_id"])

            return {"podcast": podcasts}, 200

        except Exception as e:
            return {"error": "Failed to fetch podcasts", "details": str(e)}, 500

    def get_podcast_by_id(self, user_id, podcast_id):
        try:
            user_accounts = list(
                collection.database.Accounts.find(
                    {"userId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                return {"error": "No accounts found for user"}, 403

            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                return {"error": "Podcast not found or unauthorized"}, 404

            podcast["_id"] = str(podcast["_id"])
            return {"podcast": podcast}, 200
        except Exception as e:
            return {"error": f"Failed to fetch podcast: {str(e)}"}, 500

    def delete_podcast(self, user_id, podcast_id):
        try:
            # Fetch user account IDs
            user_accounts = list(
                collection.database.Accounts.find(
                    {"userId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
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
            return {
                "error": str(e)
            }, 400  # Return a 400 Bad Request for known business errors

        except Exception as e:
            return {"error": "Failed to delete podcast", "details": str(e)}, 500

    def edit_podcast(self, user_id, podcast_id, data):
        try:
            # Fetch user account IDs
            user_accounts = list(
                collection.database.Accounts.find(
                    {"userId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Validate input data using schema
            schema = PodcastSchema(partial=True)
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            # Prepare update data by filtering out None values
            update_data = {
                key: value for key, value in data.items() if value is not None
            }
            if not update_data:
                return {
                    "message": "No update data provided"
                }, 200  # No actual update needed

            # Perform update operation
            result = self.collection.update_one(
                {"_id": podcast_id}, {"$set": update_data}
            )

            if result.modified_count == 1:
                return {"message": "Podcast updated successfully"}, 200
            else:
                return {"message": "No changes made to the podcast"}, 200

        except ValueError as e:
            # Specific business logic error
            if isinstance(e.args[0], str):
                return {
                    "error": e.args[0]
                }, 400  # Return specific error with 400 for bad input
            else:
                return {
                    "error": e.args[0],
                    "details": e.args[1],
                }, 400  # For validation errors

        except Exception as e:
            return {"error": "Failed to update podcast", "details": str(e)}, 500

    def fetch_rss_feed(self, rss_url):
        try:
            # Fetch the RSS feed
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (PodManager.ai RSS Parser)"},
            )
            with urllib.request.urlopen(req) as response:
                rss_content = response.read()

            # Parse the RSS feed using feedparser
            feed = feedparser.parse(rss_content)

            # Extract basic podcast info
            title = feed.feed.get("title", "")
            description = feed.feed.get("description", "")
            link = feed.feed.get("link", "")  # Added podcast link
            image_url = feed.feed.get("image", {}).get("href", "")
            language = feed.feed.get("language", "")
            author = feed.feed.get("author", "")
            copyright_info = feed.feed.get("copyright", "")
            generator = feed.feed.get("generator", "")  # Added generator
            last_build_date = feed.feed.get(
                "lastBuildDate", ""
            )  # Added last build date
            itunes_type = feed.feed.get("itunes_type", "")  # Added podcast type
            itunes_owner = {
                "name": feed.feed.get("itunes_owner", {}).get("itunes_name", ""),
                "email": feed.feed.get("itunes_owner", {}).get("itunes_email", ""),
            }  # Added iTunes owner info

            # Handle categories and subcategories
            categories = []
            for cat in feed.feed.get("itunes_categories", []):
                main_cat = cat.get("text", "")
                sub_cats = [sub.get("text", "") for sub in cat.get("subcategories", [])]
                categories.append({"main": main_cat, "subcategories": sub_cats})
            if not categories and feed.feed.get("itunes_category"):
                categories.append(
                    {
                        "main": feed.feed.get("itunes_category", {}).get("text", ""),
                        "subcategories": [],
                    }
                )

            # Extract episodes
            episodes = []
            for entry in feed.entries:
                # Parse duration (e.g., "00:44:56" to seconds)
                duration = entry.get("itunes_duration", "")
                duration_seconds = None
                if duration and ":" in duration:
                    time_parts = duration.split(":")
                    if len(time_parts) == 3:  # HH:MM:SS
                        duration_seconds = (
                            int(time_parts[0]) * 3600
                            + int(time_parts[1]) * 60
                            + int(time_parts[2])
                        )
                    elif len(time_parts) == 2:  # MM:SS
                        duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])

                episode = {
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "pubDate": entry.get("published", ""),
                    "audio": {
                        "url": entry.get("enclosures", [{}])[0].get("href", ""),
                        "type": entry.get("enclosures", [{}])[0].get("type", ""),
                        "length": entry.get("enclosures", [{}])[0].get("length", ""),
                    },
                    "guid": entry.get("guid", ""),
                    "season": entry.get("itunes_season", None),
                    "episode": entry.get("itunes_episode", None),
                    "episodeType": entry.get("itunes_episodetype", None),
                    "explicit": entry.get("itunes_explicit", None),
                    "image": entry.get("itunes_image", {}).get("href", ""),
                    "keywords": entry.get("itunes_keywords", None),
                    "chapters": entry.get("chapters", None),
                    "link": entry.get("link", ""),
                    "subtitle": entry.get("itunes_subtitle", ""),
                    "summary": entry.get("itunes_summary", ""),
                    "author": entry.get("author", ""),
                    "isHidden": entry.get("itunes_isHidden", None),
                    "duration": duration_seconds,  # Added duration in seconds
                    "creator": entry.get("dc_creator", ""),  # Added Dublin Core creator
                }
                episodes.append(episode)

            return {
                "title": title,
                "description": description,
                "link": link,  # Added
                "imageUrl": image_url,
                "language": language,
                "author": author,
                "copyright_info": copyright_info,
                "generator": generator,  # Added
                "lastBuildDate": last_build_date,  # Added
                "itunesType": itunes_type,  # Added
                "itunesOwner": itunes_owner,  # Added
                "categories": categories,  # Updated to include subcategories
                "episodes": episodes[:10],  # Limit to first 10 episodes
            }, 200

        except Exception as e:
            return {"error": f"Error fetching RSS feed: {str(e)}"}, 500
