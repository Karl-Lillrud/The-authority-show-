#isAdded: true

PLAN_BENEFITS = {
    "FREE": {
        "credits": 3000,
        "episode_slots": 2,
        "extra_slot_cost": 5000,
        "max_slots": 3,
        "landing_page": "Free",
        "transcription_limit": 60 * 60 
    },
    "PRO": {
        "credits": 10000,
        "credit_cost": 0.0030,
        "episode_slots": 3,
        "extra_slot_cost": 5000,
        "max_slots": 5,
        "landing_page": "Free",
        "transcription_limit": 60 * 60

    },
    "STUDIO": {
        "credits": 20000,
        "credit_cost": 0.0035,
        "episode_slots": 4,
        "extra_slot_cost": 5000,
        "max_slots": 6,
        "landing_page": "Free or custom domain",
        "transcription_limit": 120 * 60

    },
    "ENTERPRISE": {
        "credits": 30000,
        "episode_slots": "Unlimited",
        "extra_slot_cost": 0,
        "max_slots": "Unlimited",
        "landing_page": "Custom domain",
        "team_collaboration": True,
        "transcription_limit": 240 * 60

    }
}

def get_plan_benefits(plan: str) -> dict:
    return PLAN_BENEFITS.get(plan.upper(), PLAN_BENEFITS["FREE"])

def get_transcription_limit(plan: str) -> int:
    """Shortcut to get just the transcription limit."""
    return get_plan_benefits(plan).get("transcription_limit", 60 * 60)