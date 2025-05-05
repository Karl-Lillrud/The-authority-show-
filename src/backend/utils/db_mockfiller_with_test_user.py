import uuid
import random
from datetime import datetime
from faker import Faker
from pymongo import MongoClient

# === Setup ===
fake = Faker()
client = MongoClient("mongodb://localhost:27017/")
db = client["Podmanager"]

# === Credentials ===
email = "testuser@gmail.com"

# === UUIDs (all string-based for compatibility with session logic) ===
user_id = str(uuid.uuid4())
account_id = str(uuid.uuid4())
podcast_id = str(uuid.uuid4())
episode_id = str(uuid.uuid4())
guest_id = str(uuid.uuid4())
task_id = str(uuid.uuid4())
team_id = str(uuid.uuid4())
user_to_team_id = str(uuid.uuid4())
invite_id = str(uuid.uuid4())

# === Insert Data ===

# Users
db.Users.insert_one({
    "_id": user_id,
    "email": email,
    "createdAt": fake.date_time_this_year().isoformat()
})

# Accounts
db.Accounts.insert_one({
    "_id": account_id,
    "userId": user_id,
    "subscriptionId": str(uuid.uuid4()),
    "email": email,
    "isCompany": False,
    "companyName": "FakeCo",
    "paymentInfo": "",
    "subscriptionStatus": "active",
    "createdAt": fake.date_time_this_year().isoformat(),
    "referralBonus": 0,
    "subscriptionStart": fake.date_time_this_year().isoformat(),
    "subscriptionEnd": "",
    "isActive": True,
})

# Podcasts
db.Podcasts.insert_one({
    "_id": podcast_id,
    "teamId": None,
    "accountId": account_id,
    "podName": "Dev Podcast",
    "email": email,
    "socialMedia": [""] * 7,
    "category": "tech",
    "author": "Test User",
    "created_at": fake.date_time_this_year(),
    "hostBio": "",
    "hostImage": "",
    "title": "TestCast",
    "language": "en"
})

# Episodes
db.Episodes.insert_one({
    "_id": episode_id,
    "podcast_id": podcast_id,
    "title": "Welcome to Testing",
    "description": "Sample episode",
    "publishDate": fake.date_time_this_year().isoformat(),
    "duration": 12,
    "status": "draft",
    "userid": user_id,
    "accountId": account_id,
    "created_at": fake.date_time_this_year(),
    "updated_at": fake.date_time_this_year()
})

# Guests
db.Guests.insert_one({
    "_id": guest_id,
    "episodeId": episode_id,
    "name": fake.name(),
    "email": "guest@example.com",
    "tags": ["tech", "ai"],
    "bio": "Guest for testing",
    "description": "Invited speaker",
    "created_at": fake.date_time_this_year(),
    "user_id": user_id
})

# Podtasks
db.Podtasks.insert_one({
    "_id": task_id,
    "podcastId": podcast_id,
    "name": "Review Episode",
    "action": "listen",
    "dayCount": 3,
    "description": "Review and finalize",
    "status": "todo",
    "userid": user_id,
    "created_at": fake.date_time_this_year()
})

# Teams
db.Teams.insert_one({
    "_id": team_id,
    "name": "QA Team",
    "email": email,
    "phone": "",
    "isActive": True,
    "joinedAt": fake.date_time_this_year(),
    "lastActive": fake.date_time_this_year(),
    "members": [
        {"email": email, "role": "creator", "userId": user_id}
    ]
})

# UsersToTeams
db.UsersToTeams.insert_one({
    "_id": user_to_team_id,
    "userId": user_id,
    "teamId": team_id,
    "role": "creator",
    "assignedAt": fake.date_time_this_year()
})

# === Additional team where user is a regular member ===
secondary_team_id = str(uuid.uuid4())
user_to_team_id_2 = str(uuid.uuid4())

# Team entry
db.Teams.insert_one({
    "_id": secondary_team_id,
    "name": "Dev Collab Team",
    "email": "anotherlead@example.com",  # Team lead
    "phone": "+1234567890",
    "isActive": True,
    "joinedAt": fake.date_time_this_year(),
    "lastActive": fake.date_time_this_year(),
    "members": [
        {"email": "anotherlead@example.com", "role": "creator"},
        {"userId": user_id, "email": email, "role": "member"}  # testuser is member
    ]
})

# UsersToTeams entry for test user
db.UsersToTeams.insert_one({
    "_id": user_to_team_id_2,
    "userId": user_id,
    "teamId": secondary_team_id,
    "role": "member",
    "assignedAt": fake.date_time_this_year()
})

# === Final Output ===
print("\n✅ Test user and all connected data created!\n")
print(f"🔑 Login Email: {email}")
print(f"🆔 User ID:    {user_id}")
print(f"🏢 Account ID: {account_id}")
print("\n📦 Collections populated:")
for col in [
    "Users", "Accounts", "Podcasts", "Episodes", "Guests",
    "Podtasks", "Invites", "Teams", "UsersToTeams"
]:
    print(f" - {col}")
