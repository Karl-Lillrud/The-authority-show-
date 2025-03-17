"""
This script populates your MongoDB database with mock data for the following collections:
- accounts
- episodes
- guests
- guests_to_episodes
- podcasts
- teams
- users
- users_to_teams

"""

from pymongo import MongoClient
from faker import Faker
import random
import datetime
import uuid

# Initialize Faker and MongoDB client
fake = Faker()
client = MongoClient("mongodb://localhost:27017/Podmanager")  # adjust connection string as needed
db = client["podmanager_db"]

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
        db.accounts.insert_many(accounts)
        print(f"Inserted {len(accounts)} accounts.")

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
        db.users.insert_many(users)
        print(f"Inserted {len(users)} users.")
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
        db.teams.insert_many(teams)
        print(f"Inserted {len(teams)} teams.")
    return [team["id"] for team in teams]

def create_users_to_teams(user_ids, team_ids):
    user_to_team = []
    for user_id in user_ids:
        # each user can be in 1 to 3 teams
        teams_for_user = random.sample(team_ids, random.randint(1, min(3, len(team_ids))))
        for team_id in teams_for_user:
            mapping = {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "teamId": team_id,
                "role": random.choice(["admin", "member", "editor"]),
                "assignedAt": datetime.datetime.utcnow()
            }
            user_to_team.append(mapping)
    if user_to_team:
        db.users_to_teams.insert_many(user_to_team)
        print(f"Inserted {len(user_to_team)} user-to-team mappings.")

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
        db.podcasts.insert_many(podcasts)
        print(f"Inserted {len(podcasts)} podcasts.")
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
        db.guests.insert_many(guests)
        print(f"Inserted {len(guests)} guests.")
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
        db.episodes.insert_many(episodes)
        print(f"Inserted {len(episodes)} episodes.")
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
        db.guests_to_episodes.insert_many(mappings)
        print(f"Inserted {len(mappings)} guest-to-episode mappings.")

def main():
    # Create mock accounts
    create_accounts(10)
    
    # Create mock users and teams, then link them
    user_ids = create_users(10)
    team_ids = create_teams(5)
    create_users_to_teams(user_ids, team_ids)
    
    # Create podcasts (need account IDs and team IDs)
    # For simplicity, retrieve account IDs from the accounts collection
    account_ids = [acc["id"] for acc in db.accounts.find({}, {"id": 1})]
    podcast_ids = create_podcasts(10, account_ids=account_ids, team_ids=team_ids)
    
    # Create guests associated with podcasts
    guest_ids = create_guests(15, podcast_ids=podcast_ids)
    
    # Create episodes associated with guests and podcasts
    episode_ids = create_episodes(20, guest_ids=guest_ids, podcast_ids=podcast_ids)
    
    # Create mappings between guests and episodes
    create_guests_to_episodes(episode_ids, guest_ids)

if __name__ == "__main__":
    main()
