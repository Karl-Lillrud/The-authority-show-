from datetime import datetime, timezone
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

# Initialize MongoDB Client
client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]

# Example data for each model
guest_ids = ["GUEST_ID_1", "GUEST_ID_2", "GUEST_ID_3"]

teams = [
    {
        "id": str(uuid.uuid4()),
        "name": "Team Alpha",
        "email": "alpha@example.com",
        "description": "Alpha team description",
        "isActive": True,
        "joinedAt": datetime.now(timezone.utc),
        "lastActive": datetime.now(timezone.utc),
        "members": [{"name": "Alice"}, {"name": "Bob"}],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Team Beta",
        "email": "beta@example.com",
        "description": "Beta team description",
        "isActive": True,
        "joinedAt": datetime.now(timezone.utc),
        "lastActive": datetime.now(timezone.utc),
        "members": [{"name": "Charlie"}, {"name": "Dave"}],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Team Gamma",
        "email": "gamma@example.com",
        "description": "Gamma team description",
        "isActive": True,
        "joinedAt": datetime.now(timezone.utc),
        "lastActive": datetime.now(timezone.utc),
        "members": [{"name": "Eve"}, {"name": "Frank"}],
    },
]

subscriptions = [
    {
        "id": str(uuid.uuid4()),
        "subscriptionPlan": "Basic",
        "autoRenew": True,
        "discountCode": "DISCOUNT10",
    },
    {
        "id": str(uuid.uuid4()),
        "subscriptionPlan": "Premium",
        "autoRenew": True,
        "discountCode": "DISCOUNT20",
    },
    {
        "id": str(uuid.uuid4()),
        "subscriptionPlan": "Enterprise",
        "autoRenew": False,
        "discountCode": "DISCOUNT30",
    },
]

podtasks = [
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "name": "Task 1",
        "action": ["Action 1", "Action 2"],
        "dayCount": 5,
        "description": "Task 1 description",
        "actionUrl": "http://example.com/action1",
        "urlDescribe": "Action 1 description",
        "submissionReq": True,
        "status": "Pending",
        "assignedAt": datetime.now(timezone.utc),
        "dueDate": datetime.now(timezone.utc),
        "priority": "High",
    },
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "name": "Task 2",
        "action": ["Action 3", "Action 4"],
        "dayCount": 10,
        "description": "Task 2 description",
        "actionUrl": "http://example.com/action2",
        "urlDescribe": "Action 2 description",
        "submissionReq": False,
        "status": "Completed",
        "assignedAt": datetime.now(timezone.utc),
        "dueDate": datetime.now(timezone.utc),
        "priority": "Medium",
    },
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "name": "Task 3",
        "action": ["Action 5", "Action 6"],
        "dayCount": 15,
        "description": "Task 3 description",
        "actionUrl": "http://example.com/action3",
        "urlDescribe": "Action 3 description",
        "submissionReq": True,
        "status": "In Progress",
        "assignedAt": datetime.now(timezone.utc),
        "dueDate": datetime.now(timezone.utc),
        "priority": "Low",
    },
]

podcasts = [
    {
        "id": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "accountId": str(uuid.uuid4()),
        "podName": "Podcast Alpha",
        "ownerName": "Owner Alpha",
        "hostName": "Host Alpha",
        "rssFeed": "http://example.com/rss1",
        "googleCal": "http://example.com/cal1",
        "guestUrl": "http://example.com/guest1",
        "socialMedia": ["http://twitter.com/alpha", "http://facebook.com/alpha"],
        "email": "alpha@example.com",
        "description": "Podcast Alpha description",
        "logoUrl": "http://example.com/logo1",
        "category": "Technology",
        "podUrl": "http://example.com/pod1",
    },
    {
        "id": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "accountId": str(uuid.uuid4()),
        "podName": "Podcast Beta",
        "ownerName": "Owner Beta",
        "hostName": "Host Beta",
        "rssFeed": "http://example.com/rss2",
        "googleCal": "http://example.com/cal2",
        "guestUrl": "http://example.com/guest2",
        "socialMedia": ["http://twitter.com/beta", "http://facebook.com/beta"],
        "email": "beta@example.com",
        "description": "Podcast Beta description",
        "logoUrl": "http://example.com/logo2",
        "category": "Business",
        "podUrl": "http://example.com/pod2",
    },
    {
        "id": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "accountId": str(uuid.uuid4()),
        "podName": "Podcast Gamma",
        "ownerName": "Owner Gamma",
        "hostName": "Host Gamma",
        "rssFeed": "http://example.com/rss3",
        "googleCal": "http://example.com/cal3",
        "guestUrl": "http://example.com/guest3",
        "socialMedia": ["http://twitter.com/gamma", "http://facebook.com/gamma"],
        "email": "gamma@example.com",
        "description": "Podcast Gamma description",
        "logoUrl": "http://example.com/logo3",
        "category": "Health",
        "podUrl": "http://example.com/pod3",
    },
]

guests = [
    {
        "id": guest_ids[0],
        "podcastId": str(uuid.uuid4()),
        "name": "Guest Alpha",
        "image": "http://example.com/image1",
        "tags": ["Tag1", "Tag2"],
        "description": "Guest Alpha description",
        "bio": "Guest Alpha bio",
        "email": "guestalpha@example.com",
        "linkedin": "http://linkedin.com/in/alpha",
        "twitter": "http://twitter.com/alpha",
        "areasOfInterest": ["Interest1", "Interest2"],
        "status": "Confirmed",
        "scheduled": 1,
        "completed": 0,
        "createdAt": datetime.now(timezone.utc),
        "notes": "Guest Alpha notes",
    },
    {
        "id": guest_ids[1],
        "podcastId": str(uuid.uuid4()),
        "name": "Guest Beta",
        "image": "http://example.com/image2",
        "tags": ["Tag3", "Tag4"],
        "description": "Guest Beta description",
        "bio": "Guest Beta bio",
        "email": "guestbeta@example.com",
        "linkedin": "http://linkedin.com/in/beta",
        "twitter": "http://twitter.com/beta",
        "areasOfInterest": ["Interest3", "Interest4"],
        "status": "Pending",
        "scheduled": 2,
        "completed": 1,
        "createdAt": datetime.now(timezone.utc),
        "notes": "Guest Beta notes",
    },
    {
        "id": guest_ids[2],
        "podcastId": str(uuid.uuid4()),
        "name": "Guest Gamma",
        "image": "http://example.com/image3",
        "tags": ["Tag5", "Tag6"],
        "description": "Guest Gamma description",
        "bio": "Guest Gamma bio",
        "email": "guestgamma@example.com",
        "linkedin": "http://linkedin.com/in/gamma",
        "twitter": "http://twitter.com/gamma",
        "areasOfInterest": ["Interest5", "Interest6"],
        "status": "Declined",
        "scheduled": 0,
        "completed": 0,
        "createdAt": datetime.now(timezone.utc),
        "notes": "Guest Gamma notes",
    },
]

episodes = [
    {
        "id": str(uuid.uuid4()),
        "guestId": guest_ids[0],
        "podcastId": str(uuid.uuid4()),
        "title": "Episode 1",
        "description": "Episode 1 description",
        "publishDate": datetime.now(timezone.utc),
        "duration": 30,
        "status": "Published",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "guestId": guest_ids[1],
        "podcastId": str(uuid.uuid4()),
        "title": "Episode 2",
        "description": "Episode 2 description",
        "publishDate": datetime.now(timezone.utc),
        "duration": 45,
        "status": "Draft",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "guestId": guest_ids[2],
        "podcastId": str(uuid.uuid4()),
        "title": "Episode 3",
        "description": "Episode 3 description",
        "publishDate": datetime.now(timezone.utc),
        "duration": 60,
        "status": "Scheduled",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    },
]

credits = [
    {
        "id": str(uuid.uuid4()),
        "availableCredits": 100,
        "usedCredits": 50,
        "lastUpdated": datetime.now(timezone.utc),
        "creditsHistory": [{"date": datetime.now(timezone.utc), "amount": 10}],
        "creditLimit": 200,
    },
    {
        "id": str(uuid.uuid4()),
        "availableCredits": 200,
        "usedCredits": 100,
        "lastUpdated": datetime.now(timezone.utc),
        "creditsHistory": [{"date": datetime.now(timezone.utc), "amount": 20}],
        "creditLimit": 300,
    },
    {
        "id": str(uuid.uuid4()),
        "availableCredits": 300,
        "usedCredits": 150,
        "lastUpdated": datetime.now(timezone.utc),
        "creditsHistory": [{"date": datetime.now(timezone.utc), "amount": 30}],
        "creditLimit": 400,
    },
]

accounts = [
    {
        "id": str(uuid.uuid4()),
        "ownerId": str(uuid.uuid4()),
        "subscriptionId": str(uuid.uuid4()),
        "creditId": str(uuid.uuid4()),
        "email": "account1@example.com",
        "isCompany": True,
        "companyName": "Company 1",
        "paymentInfo": "Payment Info 1",
        "subscriptionStatus": "Active",
        "createdAt": datetime.now(timezone.utc),
        "referralBonus": 10,
        "subscriptionStart": datetime.now(timezone.utc),
        "subscriptionEnd": datetime.now(timezone.utc),
        "isActive": True,
    },
    {
        "id": str(uuid.uuid4()),
        "ownerId": str(uuid.uuid4()),
        "subscriptionId": str(uuid.uuid4()),
        "creditId": str(uuid.uuid4()),
        "email": "account2@example.com",
        "isCompany": False,
        "companyName": "Company 2",
        "paymentInfo": "Payment Info 2",
        "subscriptionStatus": "Inactive",
        "createdAt": datetime.now(timezone.utc),
        "referralBonus": 20,
        "subscriptionStart": datetime.now(timezone.utc),
        "subscriptionEnd": datetime.now(timezone.utc),
        "isActive": False,
    },
    {
        "id": str(uuid.uuid4()),
        "ownerId": str(uuid.uuid4()),
        "subscriptionId": str(uuid.uuid4()),
        "creditId": str(uuid.uuid4()),
        "email": "account3@example.com",
        "isCompany": True,
        "companyName": "Company 3",
        "paymentInfo": "Payment Info 3",
        "subscriptionStatus": "Pending",
        "createdAt": datetime.now(timezone.utc),
        "referralBonus": 30,
        "subscriptionStart": datetime.now(timezone.utc),
        "subscriptionEnd": datetime.now(timezone.utc),
        "isActive": True,
    },
]

users_to_teams = [
    {
        "id": str(uuid.uuid4()),
        "userId": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "role": "Admin",
        "assignedAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "userId": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "role": "Member",
        "assignedAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "userId": str(uuid.uuid4()),
        "teamId": str(uuid.uuid4()),
        "role": "Viewer",
        "assignedAt": datetime.now(timezone.utc),
    },
]

edits = [
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "clipName": "Edit 1",
        "duration": 10,
        "createdAt": datetime.now(timezone.utc),
        "editedBy": ["Editor1", "Editor2"],
        "clipUrl": "http://example.com/edit1",
        "status": "Completed",
        "tags": ["Tag1", "Tag2"],
    },
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "clipName": "Edit 2",
        "duration": 15,
        "createdAt": datetime.now(timezone.utc),
        "editedBy": ["Editor3", "Editor4"],
        "clipUrl": "http://example.com/edit2",
        "status": "In Progress",
        "tags": ["Tag3", "Tag4"],
    },
    {
        "id": str(uuid.uuid4()),
        "podcastId": str(uuid.uuid4()),
        "clipName": "Edit 3",
        "duration": 20,
        "createdAt": datetime.now(timezone.utc),
        "editedBy": ["Editor5", "Editor6"],
        "clipUrl": "http://example.com/edit3",
        "status": "Pending",
        "tags": ["Tag5", "Tag6"],
    },
]

users = [
    {
        "id": str(uuid.uuid4()),
        "name": "User Alpha",
        "email": "useralpha@example.com",
        "password": "password1",
        "role": "Admin",
        "createdAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "name": "User Beta",
        "email": "userbeta@example.com",
        "password": "password2",
        "role": "Member",
        "createdAt": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "name": "User Gamma",
        "email": "usergamma@example.com",
        "password": "password3",
        "role": "Viewer",
        "createdAt": datetime.now(timezone.utc),
    },
]


# Insert example data into the database if not already present
def insert_if_not_exists(collection_name, data):
    collection = database[collection_name]
    for item in data:
        if not collection.find_one({"id": item["id"]}):
            collection.insert_one(item)


insert_if_not_exists("teams", teams)
insert_if_not_exists("subscriptions", subscriptions)
insert_if_not_exists("podtasks", podtasks)
insert_if_not_exists("podcasts", podcasts)
insert_if_not_exists("guests", guests)
insert_if_not_exists("episodes", episodes)
insert_if_not_exists("credits", credits)
insert_if_not_exists("accounts", accounts)
insert_if_not_exists("users_to_teams", users_to_teams)
insert_if_not_exists("edits", edits)
insert_if_not_exists("users", users)

print("Example data inserted successfully.")
