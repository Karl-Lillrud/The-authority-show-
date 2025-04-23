import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.creditManagement import CreditService  # Adjust the import based on your project structure
from backend.database.mongo_connection import get_db      # Correct path to your DB helper

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Ensure logging is configured

# --- Scheduler Instance ---
# Use UTC for consistency with server times and avoid DST issues
scheduler = BackgroundScheduler(daemon=True, timezone='UTC')

# --- Helper Functions for the Job ---

def get_all_user_ids_with_credits() -> list[str]:
    """
    Fetches user IDs that have a credit document.
    Adjust this query if you need to reset based on other criteria
    (e.g., all users, users with active subscriptions).
    """
    user_ids = []
    try:
        db = get_db()
        # Find users who actually have a credit document to reset
        credit_docs = db.Credits.find({}, {"user_id": 1, "_id": 0})
        user_ids = [doc["user_id"] for doc in credit_docs if "user_id" in doc]
        logger.info(f"Found {len(user_ids)} users with credit documents to potentially reset.")
    except Exception as e:
        logger.error(f"Error fetching user IDs for credit reset: {e}", exc_info=True)
    return user_ids

def get_pm_allowance_for_user(user_id: str) -> int:
    """
    Determines the monthly PM credit allowance for a given user.
    *** This is a placeholder - Implement your actual logic here ***
    """
    # --- Placeholder Logic ---
    # Replace this with your real logic based on:
    # - User's subscription tier (query Subscriptions collection)
    # - Special promotions
    # - Default free tier allowance
    try:
        db = get_db()
        # Example: Fetch subscription or account info
        # account = db.Accounts.find_one({"ownerId": user_id})
        # subscription = db.Subscriptions.find_one({"_id": account.get("subscriptionId")}) if account else None
        # if subscription and subscription.get("plan") == "premium":
        #     return 5000 # Example premium allowance
        # elif subscription and subscription.get("plan") == "pro":
        #      return 3000 # Example pro allowance
        # else:
             # Default allowance for free tier or if no subscription found
        return 1000 # Example default allowance
    except Exception as e:
        logger.error(f"Error determining PM allowance for user {user_id}: {e}", exc_info=True)
        return 0 # Return 0 if allowance cannot be determined

# --- The Scheduled Job ---

def monthly_credit_reset_job():
    """
    The core job function executed monthly by the scheduler.
    Fetches users, determines their allowance, and calls the reset service.
    """
    logger.info("--- Starting Monthly Credit Reset Job ---")
    # Instantiate the service within the job function to ensure freshness,
    # especially if the service interacts with request contexts (though it shouldn't here)
    credit_service = CreditService()
    user_ids = get_all_user_ids_with_credits()

    success_count = 0
    failure_count = 0

    for user_id in user_ids:
        try:
            allowance = get_pm_allowance_for_user(user_id)
            logger.debug(f"Processing reset for user {user_id} with allowance {allowance}")
            success = credit_service.perform_monthly_reset(user_id, allowance)
            if success:
                success_count += 1
                logger.debug(f"Successfully processed reset for user {user_id}")
            else:
                failure_count += 1
                logger.error(f"Monthly reset failed for user {user_id} according to service.")
        except Exception as e:
            failure_count += 1
            logger.error(f"Exception during reset for user {user_id}: {e}", exc_info=True)

    logger.info(f"--- Monthly Credit Reset Job Finished ---")
    logger.info(f"Successfully processed: {success_count}, Failed: {failure_count}")

# --- Scheduler Control Functions ---

def init_scheduler():
    """
    Adds the monthly reset job to the scheduler and starts it.
    This function should be called ONCE when your Flask application starts.
    """
    if scheduler.running:
        logger.warning("Scheduler is already running.")
        return

    try:
        # Schedule the job to run on the 1st day of every month at 00:05 UTC (5 minutes past midnight)
        scheduler.add_job(
            monthly_credit_reset_job,
            'cron',
            day=1,
            hour=0,
            minute=5,
            id='monthly_credit_reset', # Assign an ID for potential management
            replace_existing=True     # Replace if job with same ID exists
        )
        scheduler.start()
        logger.info("Credit reset scheduler initialized and started.")
        logger.info(f"Next reset run time: {scheduler.get_job('monthly_credit_reset').next_run_time}")

        # Ensure graceful shutdown when the application exits
        atexit.register(shutdown_scheduler)

    except Exception as e:
        logger.error(f"Failed to initialize or start the scheduler: {e}", exc_info=True)

def init_credit_scheduler(app):
    """
    Flask app-aware wrapper for initializing the credit scheduler.
    This ensures the job runs within the Flask application context.
    """
    try:
        # Make the job run within Flask's application context
        original_job = monthly_credit_reset_job
        
        # Create a wrapped job function that pushes the app context
        def context_wrapped_job():
            with app.app_context():
                original_job()
        
        # Schedule using the wrapped job
        scheduler.add_job(
            context_wrapped_job,
            'cron',
            day=1,
            hour=0,
            minute=5,
            id='monthly_credit_reset',
            replace_existing=True
        )
        
        # Start the scheduler if not already running
        if not scheduler.running:
            scheduler.start()
            logger.info("Credit reset scheduler initialized and started.")
            logger.info(f"Next reset run time: {scheduler.get_job('monthly_credit_reset').next_run_time}")
            
            # Register shutdown handler
            atexit.register(shutdown_scheduler)
        else:
            logger.info("Scheduler already running, added/updated the monthly reset job.")
    
    except Exception as e:
        logger.error(f"Failed to initialize credit scheduler: {e}", exc_info=True)

def shutdown_scheduler():
    """Shuts down the scheduler gracefully."""
    if scheduler.running:
        logger.info("Shutting down credit reset scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler was not running.")

# --- Optional: Direct Execution Check (for testing) ---
if __name__ == '__main__':
    # This block allows you to test the job directly if you run the script
    # Note: This requires your DB connection and other dependencies to be available
    print("Running the monthly credit reset job directly for testing...")
    # Make sure environment variables (like MONGODB_URI) are loaded if needed
    # from dotenv import load_dotenv
    # load_dotenv()
    monthly_credit_reset_job()
    print("Test run complete.")