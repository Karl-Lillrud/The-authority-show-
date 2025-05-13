"""
This script populates the MongoDB database with mock data for the following collections:
- Accounts
- Episodes
- Guests
- Guests_to_Episodes
- Podcasts
- Teams
- Users
- Users_to_Teams
- Credits
- Edits (clips)
- Podtasks
- Subscriptions

Dependencies:
• pymongo – to connect and interact with MongoDB (install via: pip install pymongo)
• Faker – to generate realistic fake data (install via: pip install Faker)

Usage:
    Set your MONGODB_URI in a .env file and run this script.
    
/RedShadow
"""

from pymongo import MongoClient
from faker import Faker
import random
import datetime
import uuid
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize Faker and MongoDB client
fake = Faker()
try:
    mongodb_uri = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb_uri)  # use connection string from .env
    db = client.get_default_database()
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

def create_accounts(user_ids):
    accounts = []
    for user_id in user_ids:
        account = {
            "id": str(uuid.uuid4()),
            "ownerId": user_id,
            "subscriptionId": str(uuid.uuid4()),
            "creditId": str(uuid.uuid4()),
            "isCompany": fake.boolean(),
            "companyName": fake.company() if fake.boolean() else None,
            "paymentInfo": fake.credit_card_full(),
            "subscriptionStatus": random.choice(["active", "inactive", "pending"]),
            "createdAt": fake.date_time_this_decade(),
            "referralBonus": random.randint(0, 100),
            "subscriptionStart": fake.date_time_this_year(),
            "subscriptionEnd": fake.date_time_this_year(),
            "isFirstLogin" : False,
            "isActive": fake.boolean()
        }
        accounts.append(account)
    if accounts:
        try:
            db.Accounts.insert_many(accounts)
            logger.info(f"Inserted {len(accounts)} Accounts.")
        except Exception as e:
            logger.error(f"Failed to insert Accounts: {e}")

def create_users(n=10):
    users = []
    for _ in range(n):
        user = {
            "id": str(uuid.uuid4()),
            "email": fake.email(),
            "createdAt": fake.date_time_this_decade(),
            "referralCode": fake.lexify(text='????'),
            "referredBy": fake.lexify(text='????') if fake.boolean() else None
        }
        users.append(user)
    if users:
        try:
            db.Users.insert_many(users)
            logger.info(f"Inserted {len(users)} Users.")
        except Exception as e:
            logger.error(f"Failed to insert Users: {e}")
    return [user["id"] for user in users]

def create_teams(n=5):
    teams = []
    for _ in range(n):
        team = {
            "id": str(uuid.uuid4()),
            "name": fake.company(),
            "email": fake.company_email(),
            "description": fake.text(max_nb_chars=100),
            "isActive": fake.boolean(),
            "joinedAt": fake.date_time_this_decade(),
            "lastActive": fake.date_time_this_month(),
            "members": []  # will be linked via Users_to_Teams
        }
        teams.append(team)
    if teams:
        try:
            db.Teams.insert_many(teams)
            logger.info(f"Inserted {len(teams)} Teams.")
        except Exception as e:
            logger.error(f"Failed to insert Teams: {e}")
    return [team["id"] for team in teams]

def create_users_to_teams(user_ids, team_ids):
    user_to_team = []
    for user_id in user_ids:
        # Each user can be in 1 to 3 teams
        teams_for_user = random.sample(team_ids, random.randint(1, min(3, len(team_ids))))
        for team_id in teams_for_user:
            mapping = {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "teamId": team_id,
                "role": random.choice(["admin", "member", "editor"]),
                "assignedAt": datetime.datetime.now(datetime.timezone.utc)
            }
            user_to_team.append(mapping)
    if user_to_team:
        try:
            db.Users_to_Teams.insert_many(user_to_team)
            logger.info(f"Inserted {len(user_to_team)} Users_to_Teams mappings.")
        except Exception as e:
            logger.error(f"Failed to insert Users_to_Teams mappings: {e}")

def create_podcasts(n=10, account_ids=None, team_ids=None):
    podcasts = []
    for _ in range(n):
        podcast = {
            "id": str(uuid.uuid4()),
            "teamId": random.choice(team_ids) if team_ids else None,
            "accountId": random.choice(account_ids) if account_ids else str(uuid.uuid4()),
            "podName": fake.catch_phrase(),
            "ownerName": fake.name(),
            "hostName": fake.name(),
            "rssFeed": fake.url(),
            "googleCal": fake.url(),
            "guestUrl": fake.url(),
            "socialMedia": [fake.url() for _ in range(random.randint(1, 3))],
            "email": fake.email(),
            "description": fake.text(max_nb_chars=200),
            "logoUrl": fake.image_url(),
            "category": random.choice(["tech", "health", "business", "comedy"]),
            "podUrl": fake.url()
        }
        podcasts.append(podcast)
    if podcasts:
        try:
            db.Podcasts.insert_many(podcasts)
            logger.info(f"Inserted {len(podcasts)} Podcasts.")
        except Exception as e:
            logger.error(f"Failed to insert Podcasts: {e}")
    return [pod["id"] for pod in podcasts]

def create_guests(n=15, podcast_ids=None):
    guests = []
    for _ in range(n):
        guest = {
            "id": str(uuid.uuid4()),
            "podcastId": random.choice(podcast_ids) if podcast_ids else str(uuid.uuid4()),
            "name": fake.name(),
            "image": fake.image_url(),
            "tags": [fake.word() for _ in range(random.randint(1, 4))],
            "description": fake.text(max_nb_chars=100),
            "bio": fake.text(max_nb_chars=150),
            "email": fake.email(),
            "linkedin": fake.url(),
            "twitter": fake.user_name(),
            "areasOfInterest": [fake.word() for _ in range(random.randint(1, 3))],
            "status": random.choice(["pending", "confirmed", "declined"]),
            "scheduled": random.randint(0, 5),
            "completed": random.randint(0, 5),
            "createdAt": fake.date_time_this_decade(),
            "notes": fake.sentence()
        }
        guests.append(guest)
    if guests:
        try:
            db.Guests.insert_many(guests)
            logger.info(f"Inserted {len(guests)} Guests.")
        except Exception as e:
            logger.error(f"Failed to insert Guests: {e}")
    return [guest["id"] for guest in guests]

def create_episodes(n=20, guest_ids=None, podcast_ids=None):
    episodes = []
    for _ in range(n):
        episode = {
            "id": str(uuid.uuid4()),
            "guestId": random.choice(guest_ids) if guest_ids else str(uuid.uuid4()),
            "podcastId": random.choice(podcast_ids) if podcast_ids else str(uuid.uuid4()),
            "title": fake.sentence(nb_words=6),
            "description": fake.text(max_nb_chars=200),
            "publishDate": fake.date_time_this_year(),
            "duration": random.randint(600, 3600),  # seconds
            "status": random.choice(["draft", "published", "archived"]),
            "createdAt": fake.date_time_this_decade(),
            "updatedAt": fake.date_time_this_year()
        }
        episodes.append(episode)
    if episodes:
        try:
            db.Episodes.insert_many(episodes)
            logger.info(f"Inserted {len(episodes)} Episodes.")
        except Exception as e:
            logger.error(f"Failed to insert Episodes: {e}")
    return [ep["id"] for ep in episodes]

def create_guests_to_episodes(episode_ids, guest_ids):
    mappings = []
    for episode_id in episode_ids:
        # Map 1 to 2 guests per episode
        for _ in range(random.randint(1, 2)):
            mapping = {
                "id": str(uuid.uuid4()),
                "episodeId": episode_id,
                "guestId": random.choice(guest_ids)
            }
            mappings.append(mapping)
    if mappings:
        try:
            db.Guests_to_Episodes.insert_many(mappings)
            logger.info(f"Inserted {len(mappings)} Guests_to_Episodes mappings.")
        except Exception as e:
            logger.error(f"Failed to insert Guests_to_Episodes mappings: {e}")

def create_credits(n=10):
    credits = []
    for _ in range(n):
        # Create a random credits history list with 2-4 entries
        history = []
        for _ in range(random.randint(2, 4)):
            history.append({
                "action": random.choice(["added", "used", "refunded"]),
                "amount": random.randint(1, 50),
                "timestamp": fake.date_time_this_year()
            })
        credit = {
            "id": str(uuid.uuid4()),
            "availableCredits": random.randint(50, 200),
            "usedCredits": random.randint(0, 50),
            "lastUpdated": fake.date_time_this_year(),
            "creditsHistory": history,
            "creditLimit": random.randint(200, 500)
        }
        credits.append(credit)
    if credits:
        try:
            db.Credits.insert_many(credits)
            logger.info(f"Inserted {len(credits)} Credits.")
        except Exception as e:
            logger.error(f"Failed to insert Credits: {e}")

def create_edits(n=10, episode_ids=None):
    edits = []
    for _ in range(n):
        edit = {
            "id": str(uuid.uuid4()),
            "episodeId": random.choice(episode_ids) if episode_ids else str(uuid.uuid4()),
            "clipName": fake.sentence(nb_words=3),
            "duration": random.randint(30, 300),  # seconds
            "createdAt": fake.date_time_this_year(),
            "editedBy": [fake.name() for _ in range(random.randint(1, 3))],
            "clipUrl": fake.url(),
            "status": random.choice(["pending", "approved", "rejected"]),
            "tags": [fake.word() for _ in range(random.randint(1, 4))]
        }
        edits.append(edit)
    if edits:
        try:
            db.Edits.insert_many(edits)
            logger.info(f"Inserted {len(edits)} Edits (clips).")
        except Exception as e:
            logger.error(f"Failed to insert Edits: {e}")

def create_podtasks(n=10, podcast_ids=None):
    tasks = []
    for _ in range(n):
        assigned_at = fake.date_time_this_year()
        due_date = assigned_at + datetime.timedelta(days=random.randint(1, 30))
        task = {
            "id": str(uuid.uuid4()),
            "podcastId": random.choice(podcast_ids) if podcast_ids else str(uuid.uuid4()),
            "name": fake.sentence(nb_words=4),
            "action": [random.choice(["record", "edit", "publish", "promote"]) for _ in range(random.randint(1, 3))],
            "dayCount": random.randint(1, 10),
            "description": fake.text(max_nb_chars=150),
            "actionUrl": fake.url(),
            "urlDescribe": fake.sentence(nb_words=6),
            "submissionReq": fake.boolean(),
            "status": random.choice(["open", "in progress", "completed"]),
            "assignedAt": assigned_at,
            "dueDate": due_date,
            "priority": random.choice(["low", "medium", "high"])
        }
        tasks.append(task)
    if tasks:
        try:
            db.Podtasks.insert_many(tasks)
            logger.info(f"Inserted {len(tasks)} Podtasks.")
        except Exception as e:
            logger.error(f"Failed to insert Podtasks: {e}")

def create_subscriptions(n=10):
    subscriptions = []
    plans = ["basic", "premium", "enterprise"]
    for _ in range(n):
        subscription = {
            "id": str(uuid.uuid4()),
            "subscriptionPlan": random.choice(plans),
            "autoRenew": fake.boolean(),
            "discountCode": fake.lexify(text='DISCOUNT-????')
        }
        subscriptions.append(subscription)
    if subscriptions:
        try:
            db.Subscriptions.insert_many(subscriptions)
            logger.info(f"Inserted {len(subscriptions)} Subscriptions.")
        except Exception as e:
            logger.error(f"Failed to insert Subscriptions: {e}")

def main():
    try:
        # Create mock Users
        user_ids = create_users(10)

        # Create mock Accounts for the new mock Users
        create_accounts(user_ids)

        # Create mock Teams then link them to Users
        team_ids = create_teams(5)
        create_users_to_teams(user_ids, team_ids)
        
        # Create Podcasts (need account IDs and team IDs)
        account_ids = [acc["id"] for acc in db.Accounts.find({}, {"id": 1})]
        podcast_ids = create_podcasts(10, account_ids=account_ids, team_ids=team_ids)
        
        # Create Guests associated with Podcasts
        guest_ids = create_guests(15, podcast_ids=podcast_ids)
        
        # Create Episodes associated with Guests and Podcasts
        episode_ids = create_episodes(20, guest_ids=guest_ids, podcast_ids=podcast_ids)
        
        # Create mappings between Guests and Episodes
        create_guests_to_episodes(episode_ids, guest_ids)
        
        # Create additional collections
        create_credits(10)
        create_edits(10, episode_ids=episode_ids)
        create_podtasks(10, podcast_ids=podcast_ids)
        create_subscriptions(10)
    except Exception as e:
        logger.error(f"An error occurred during the mock data creation process: {e}")

if __name__ == "__main__":
    main()
