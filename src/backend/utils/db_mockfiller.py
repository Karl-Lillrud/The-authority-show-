"""
This script populates the MongoDB database with mock data for the following collections:
- accounts
- episodes
- guests
- guests_to_episodes
- podcasts
- teams
- users
- users_to_teams
- credits
- edits (clips)
- podtasks
- subscriptions

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

def create_accounts(n=10):
    accounts = []
    for _ in range(n):
        account = {
            "id": str(uuid.uuid4()),
            "ownerId": str(uuid.uuid4()),
            "subscriptionId": str(uuid.uuid4()),
            "creditId": str(uuid.uuid4()),
            "email": fake.email(),
            "isCompany": fake.boolean(),
            "companyName": fake.company() if fake.boolean() else None,
            "paymentInfo": fake.credit_card_full(),
            "subscriptionStatus": random.choice(["active", "inactive", "pending"]),
            "createdAt": fake.date_time_this_decade(),
            "referralBonus": random.randint(0, 100),
            "subscriptionStart": fake.date_time_this_year(),
            "subscriptionEnd": fake.date_time_this_year(),
            "isActive": fake.boolean()
        }
        accounts.append(account)
    if accounts:
        try:
            db.accounts.insert_many(accounts)
            logger.info(f"Inserted {len(accounts)} accounts.")
        except Exception as e:
            logger.error(f"Failed to insert accounts: {e}")

def create_users(n=10):
    users = []
    for _ in range(n):
        user = {
            "id": str(uuid.uuid4()),
            "email": fake.email(),
            "passwordHash": fake.sha256(),
            "createdAt": fake.date_time_this_decade(),
            "referralCode": fake.lexify(text='????'),
            "referredBy": fake.lexify(text='????') if fake.boolean() else None
        }
        users.append(user)
    if users:
        try:
            db.users.insert_many(users)
            logger.info(f"Inserted {len(users)} users.")
        except Exception as e:
            logger.error(f"Failed to insert users: {e}")
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
            "members": []  # will be linked via users_to_teams
        }
        teams.append(team)
    if teams:
        try:
            db.teams.insert_many(teams)
            logger.info(f"Inserted {len(teams)} teams.")
        except Exception as e:
            logger.error(f"Failed to insert teams: {e}")
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
            db.users_to_teams.insert_many(user_to_team)
            logger.info(f"Inserted {len(user_to_team)} user-to-team mappings.")
        except Exception as e:
            logger.error(f"Failed to insert user-to-team mappings: {e}")

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
            db.podcasts.insert_many(podcasts)
            logger.info(f"Inserted {len(podcasts)} podcasts.")
        except Exception as e:
            logger.error(f"Failed to insert podcasts: {e}")
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
            db.guests.insert_many(guests)
            logger.info(f"Inserted {len(guests)} guests.")
        except Exception as e:
            logger.error(f"Failed to insert guests: {e}")
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
            db.episodes.insert_many(episodes)
            logger.info(f"Inserted {len(episodes)} episodes.")
        except Exception as e:
            logger.error(f"Failed to insert episodes: {e}")
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
            db.guests_to_episodes.insert_many(mappings)
            logger.info(f"Inserted {len(mappings)} guest-to-episode mappings.")
        except Exception as e:
            logger.error(f"Failed to insert guest-to-episode mappings: {e}")

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
            db.credits.insert_many(credits)
            logger.info(f"Inserted {len(credits)} credits.")
        except Exception as e:
            logger.error(f"Failed to insert credits: {e}")

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
            db.edits.insert_many(edits)
            logger.info(f"Inserted {len(edits)} edits (clips).")
        except Exception as e:
            logger.error(f"Failed to insert edits: {e}")

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
            db.podtasks.insert_many(tasks)
            logger.info(f"Inserted {len(tasks)} podtasks.")
        except Exception as e:
            logger.error(f"Failed to insert podtasks: {e}")

def create_su
