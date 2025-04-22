import os


def get_client_secret():
    """
    Dynamically return the correct client secret based on the environment.
    """
    environment = os.getenv("ENVIRONMENT", "local").lower()
    if environment == "production":
        return os.getenv("PUBLIC_CLIENT_SECRET")
    return os.getenv("LOCAL_CLIENT_SECRET")
