from datetime import timedelta

TRIGGERS = {
    "booking": {"status": "Not Recorded", "time_check": None},
    "preparation": {"status": "Not Recorded", "time_check": timedelta(days=1)},
    "missing_info": {"status": "Not Recorded", "time_check": timedelta(days=20)},
    "publishing_reminder": {"status": "Recorded", "time_check": timedelta(days=7)},
    "join_link": {"status": "Not Recorded", "time_check": timedelta(hours=1)},
    "thank_you": {"status": "Published", "time_check": timedelta(days=0)},
    "recommendations": {"status": "Published", "time_check": timedelta(days=14)},
    "suggestions": {"status": "Published", "time_check": timedelta(days=0)},
    "missing_social_media": {"status": "Recorded", "time_check": None},
}