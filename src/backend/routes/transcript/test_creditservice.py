# import os
# from dotenv import load_dotenv
# import sys

# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# from backend.services.creditService import initialize_credits, get_user_credits, consume_credits

# # Load environment variables
# load_dotenv()

# dummy_user = "dummy_user_test"

# # Ensure that dummy_user has credits
# if get_user_credits(dummy_user) is None:
#     print(f"Initializing credits for {dummy_user}...")
#     initialize_credits(dummy_user)

# print("Credits record before consuming:", get_user_credits(dummy_user))

# # Try consuming credits for a feature (e.g., "transcription")
# try:
#     result = consume_credits(dummy_user, "transcription")
#     print("Consume credits result:", result)
# except Exception as e:
#     print("Error consuming credits:", e)

# print("Credits record after consuming:", get_user_credits(dummy_user))
