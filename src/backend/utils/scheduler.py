import os
import logging
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import render_template, current_app
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email
from backend.repository.guest_repository import GuestRepository
from backend.repository.episode_repository import EpisodeRepository

import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Correct path to .env file (three levels up from src/backend/utils to project root)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

SENT_EMAILS_FILE = os.path.join(os.path.dirname(__file__), "sent_emails.json")
# XML_FILE_PATH_FOR_ACTIVATION will be loaded from .env; default is fallback
XML_FILE_PATH_FOR_ACTIVATION = os.getenv("ACTIVATION_XML_FILE_PATH", "src/frontend/static/scraped.xml")  # Default changed to be more sensible if .env fails
API_BASE_URL_FOR_ACTIVATION = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip('/')

ACTIVATION_PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "activation_progress.json")
INITIAL_BATCH_SIZE = int(os.getenv("ACTIVATION_INITIAL_BATCH_SIZE", 68))
INCREMENT_PERCENTAGE = float(os.getenv("ACTIVATION_INCREMENT_PERCENTAGE", 0.20))

scheduler = BackgroundScheduler(daemon=True)
_scheduler_initialized_jobs = False  # Flag to track if jobs have been added for the current scheduler instance

guest_repo = GuestRepository()
episode_repo = EpisodeRepository()


def render_email_content(
    trigger_name,
    guest,
    episode,
    social_network=None,
    guest_email=None,
    podName=None,
    link=None,
    audio_url=None,
):
    try:
        template_path = f"emails/{trigger_name}_email.html"
        email_body = render_template(
            template_path,
            guest_name=guest["name"],
            guest_email=guest_email,
            podName=podName,
            episode_title=episode["title"],
            social_network=social_network,
            link=link,
            audio_url=audio_url,
        )
        return email_body
    except Exception as e:
        logger.error(f"Error rendering email template {template_path}: {str(e)}")
        return "Error loading email content."


def check_and_send_reminders():
    sent_emails = load_sent_emails()
    save_sent_emails(sent_emails)
    logger.info("Checked and sent reminders.")


def load_sent_emails():
    try:
        if os.path.exists(SENT_EMAILS_FILE):
            with open(SENT_EMAILS_FILE, "r") as file:
                sent_emails_list = json.load(file)
                return set(
                    tuple(item) for item in sent_emails_list if isinstance(item, list)
                )
        else:
            logger.info(
                f"{SENT_EMAILS_FILE} not found. Starting with empty sent emails set."
            )
            return set()
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error loading {SENT_EMAILS_FILE}: {e}. Returning empty set.")
        return set()


def save_sent_emails(sent_emails_set):
    try:
        sent_emails_list = [list(item) for item in sent_emails_set]
        with open(SENT_EMAILS_FILE, "w") as file:
            json.dump(sent_emails_list, file, indent=4)
    except IOError as e:
        logger.error(f"Error saving sent emails to {SENT_EMAILS_FILE}: {e}")
    except TypeError as e:
        logger.error(f"Error serializing sent_emails data: {e}")


def check_and_send_reminders_with_context(app):
    with app.app_context():
        check_and_send_reminders()


def _load_podcasts_from_xml_for_scheduler(file_path):
    podcasts = []
    try:
        # Resolve file_path relative to the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        actual_file_path = os.path.join(project_root, file_path) if not os.path.isabs(file_path) else file_path
        
        logger.info(f"Resolved XML file path for activation: {actual_file_path}")

        if not os.path.exists(actual_file_path):
            logger.error(f"XML file for activation not found at resolved path: {actual_file_path} (original: {file_path})")
            return podcasts

        tree = ET.parse(actual_file_path)
        root = tree.getroot()
        for podcast_elem in root.findall("podcast"):
            title = podcast_elem.findtext("title")
            email_element = podcast_elem.find("emails/email")
            email = email_element.text if email_element is not None else None
            rss_feed = podcast_elem.findtext("rss")
            if title and email and rss_feed:
                podcasts.append({"title": title, "email": email, "rss_feed": rss_feed})
            else:
                logger.warning(f"Scheduler: Skipping podcast entry from XML due to missing data: Title={title}, Email={email}, RSS={rss_feed}")
        logger.info(f"Scheduler: Loaded {len(podcasts)} podcasts from {actual_file_path} for activation invites.")
    except FileNotFoundError:
        logger.error(f"Scheduler: XML file not found at {file_path}")
    except ET.ParseError:
        logger.error(f"Scheduler: Error parsing XML file at {file_path}")
    except Exception as e:
        logger.error(f"Scheduler: An unexpected error occurred while loading XML for activation: {e}", exc_info=True)
    return podcasts


def load_activation_progress():
    default_progress = {
        "current_day_batch_size": INITIAL_BATCH_SIZE,
        "processed_emails_globally": [],
        "daily_reports": []
    }
    try:
        if os.path.exists(ACTIVATION_PROGRESS_FILE):
            with open(ACTIVATION_PROGRESS_FILE, "r") as file:
                progress_data = json.load(file)
                progress_data.setdefault("current_day_batch_size", INITIAL_BATCH_SIZE)
                progress_data.setdefault("processed_emails_globally", [])
                progress_data.setdefault("daily_reports", [])
                if progress_data["current_day_batch_size"] < INITIAL_BATCH_SIZE and not progress_data["processed_emails_globally"]:
                    progress_data["current_day_batch_size"] = INITIAL_BATCH_SIZE
                return progress_data
        else:
            logger.info(
                f"{ACTIVATION_PROGRESS_FILE} not found. Initializing with default activation progress."
            )
            with open(ACTIVATION_PROGRESS_FILE, "w") as file:
                json.dump(default_progress, file, indent=4)
            return default_progress
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error loading {ACTIVATION_PROGRESS_FILE}: {e}. Returning default progress.")
        try:
            with open(ACTIVATION_PROGRESS_FILE, "w") as file:
                json.dump(default_progress, file, indent=4)
        except Exception as ex_save:
            logger.error(f"Failed to recreate default {ACTIVATION_PROGRESS_FILE}: {ex_save}")
        return default_progress


def save_activation_progress(progress_data):
    try:
        with open(ACTIVATION_PROGRESS_FILE, "w") as file:
            json.dump(progress_data, file, indent=4)
    except IOError as e:
        logger.error(f"Error saving activation progress to {ACTIVATION_PROGRESS_FILE}: {e}")
    except TypeError as e:
        logger.error(f"Error serializing activation progress data: {e}")


def trigger_scheduled_activation_invites():
    logger.info("=== [SCHEDULER] Activation email job STARTED ===")
    try:
        logger.info("Scheduler: Starting job to trigger activation invites with progressive rollout.")
        
        activation_progress = load_activation_progress()
        current_day_limit = activation_progress.get("current_day_batch_size", INITIAL_BATCH_SIZE)
        processed_emails_globally_set = set(activation_progress.get("processed_emails_globally", []))

        all_podcasts_from_xml = _load_podcasts_from_xml_for_scheduler(XML_FILE_PATH_FOR_ACTIVATION)
        
        successful_triggers_in_run = 0
        failed_triggers_in_run = 0
        podcasts_actually_attempted_count = 0

        if not all_podcasts_from_xml:
            logger.info("Scheduler: No podcasts found in XML to process for activation invites.")
            next_day_batch_size = int(current_day_limit * (1 + INCREMENT_PERCENTAGE))
            if next_day_batch_size == current_day_limit: 
                next_day_batch_size +=1
            activation_progress["current_day_batch_size"] = next_day_batch_size
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_report_entry = {
                "date": today_str,
                "sent_successfully": 0,
                "failed_to_send": 0,
                "total_attempted_for_day": 0
            }
            reports = activation_progress.get("daily_reports", [])
            reports = [r for r in reports if r.get("date") != today_str]
            reports.append(daily_report_entry)
            activation_progress["daily_reports"] = reports
            
            save_activation_progress(activation_progress)
            return

        unique_pending_podcasts_map = {}
        for p in all_podcasts_from_xml:
            email = p.get("email")
            if email and email not in processed_emails_globally_set:
                if email not in unique_pending_podcasts_map:
                     unique_pending_podcasts_map[email] = p
        
        pending_podcasts_list = list(unique_pending_podcasts_map.values())

        if not pending_podcasts_list:
            logger.info("Scheduler: All podcasts from XML have already been processed for activation invites.")
            next_day_batch_size = int(current_day_limit * (1 + INCREMENT_PERCENTAGE))
            if next_day_batch_size == current_day_limit:
                 next_day_batch_size +=1
            activation_progress["current_day_batch_size"] = next_day_batch_size
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_report_entry = {
                "date": today_str,
                "sent_successfully": 0,
                "failed_to_send": 0,
                "total_attempted_for_day": 0
            }
            reports = activation_progress.get("daily_reports", [])
            reports = [r for r in reports if r.get("date") != today_str]
            reports.append(daily_report_entry)
            activation_progress["daily_reports"] = reports

            save_activation_progress(activation_progress)
            return

        podcasts_for_current_run = pending_podcasts_list[:current_day_limit]
        podcasts_actually_attempted_count = len(podcasts_for_current_run)
        emails_processed_in_this_run = set()

        for podcast_data in podcasts_for_current_run:
            email = podcast_data.get("email")
            rss_url = podcast_data.get("rss_feed")
            podcast_title = podcast_data.get("title")

            if email in emails_processed_in_this_run:
                logger.info(f"Scheduler: Skipping duplicate email in current batch processing: {email} for podcast: {podcast_title}")
                continue

            try:
                logger.info(f"Scheduler: Processing activation invite for: {email}, Podcast: {podcast_title}")
                invite_url = f"{API_BASE_URL_FOR_ACTIVATION}/activation/invite"
                payload = {
                    "email": email,
                    "rss_url": rss_url,
                    "podcast_title": podcast_title
                }
                response = requests.post(invite_url, json=payload, timeout=30) 
                
                if response.ok:
                    logger.info(f"Scheduler: Successfully triggered activation for {email}. API Response: {response.json().get('message')}")
                    successful_triggers_in_run += 1
                    processed_emails_globally_set.add(email) 
                    emails_processed_in_this_run.add(email)   
                else:
                    logger.error(f"Scheduler: Failed to trigger activation for {email} via API: {response.status_code} - {response.text}")
                    failed_triggers_in_run += 1
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Scheduler: API request failed for activation invite to {email}: {req_err}", exc_info=True)
                failed_triggers_in_run += 1
            except Exception as e:
                logger.error(f"Scheduler: Failed to process activation invite for {email}: {e}", exc_info=True)
                failed_triggers_in_run += 1
        
        next_day_batch_size = int(current_day_limit * (1 + INCREMENT_PERCENTAGE))
        if next_day_batch_size == current_day_limit and pending_podcasts_list[current_day_limit:]: 
            next_day_batch_size += 1
        
        activation_progress["current_day_batch_size"] = next_day_batch_size
        activation_progress["processed_emails_globally"] = sorted(list(processed_emails_globally_set)) 

        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_report_entry = {
            "date": today_str,
            "sent_successfully": successful_triggers_in_run,
            "failed_to_send": failed_triggers_in_run,
            "total_attempted_for_day": podcasts_actually_attempted_count
        }
        reports = activation_progress.get("daily_reports", [])
        reports = [r for r in reports if r.get("date") != today_str]
        reports.append(daily_report_entry)
        activation_progress["daily_reports"] = reports
        
        save_activation_progress(activation_progress)
        
        logger.info(f"Scheduler: Activation invite job finished. Processed {podcasts_actually_attempted_count} podcasts in this run. Successfully triggered {successful_triggers_in_run} invites, Failed: {failed_triggers_in_run}.")
        logger.info(f"Scheduler: Next day's batch size set to {next_day_batch_size}. Total unique emails processed globally: {len(processed_emails_globally_set)}.")
    except Exception as e:
        logger.error(f"=== [SCHEDULER] ERROR in activation email job: {e}", exc_info=True)


def send_daily_activation_summary():
    logger.info("=== [SCHEDULER] Daily activation summary job STARTED ===")
    try:
        logger.info("Scheduler: Preparing to send daily activation summary.")
        activation_progress = load_activation_progress()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        todays_report = None
        for report in reversed(activation_progress.get("daily_reports", [])):
            if report.get("date") == today_str:
                todays_report = report
                break
        
        if todays_report:
            subject = f"PodManager.ai - Daily Activation Email Summary ({today_str})"
            body_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h2 {{ color: #333; }}
                        table {{ border-collapse: collapse; width: 100%; max-width: 500px; margin-top: 15px; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    <h2>PodManager.ai - Activation Email Log</h2>
                    <p><strong>Date:</strong> {today_str}</p>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Count</th>
                        </tr>
                        <tr>
                            <td>Total Podcasts Processed for Activation Today</td>
                            <td>{todays_report.get('total_attempted_for_day', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td>Activation Emails Successfully Triggered</td>
                            <td>{todays_report.get('sent_successfully', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td>Activation Emails Failed to Trigger (API/Network errors)</td>
                            <td>{todays_report.get('failed_to_send', 'N/A')}</td>
                        </tr>
                    </table>
                    <p><em>This is an automated daily summary from the PodManager.ai scheduler.</em></p>
                </body>
            </html>
            """
            recipients = ["marcuzg@gmail.com", "me@karllillrud.com"]
            for recipient_email in recipients:
                logger.info(f"Sending daily activation summary to {recipient_email}")
                send_email(recipient_email, subject, body_html) 
            logger.info("Daily activation summary email(s) sent.")
        else:
            logger.warning(f"No activation report found for today ({today_str}) to send summary.")
            subject = f"PodManager.ai - No Activation Report for {today_str}"
            body_html = f"<p>No activation email processing report was found for {today_str}.</p>"
            recipients = ["marcuzg@gmail.com", "me@karllillrud.com"]
            for recipient_email in recipients:
                 send_email(recipient_email, subject, body_html)
    except Exception as e:
        logger.error(f"=== [SCHEDULER] ERROR in daily activation summary job: {e}", exc_info=True)


def send_daily_activation_summary_with_context(app):
    with app.app_context():
        send_daily_activation_summary()


def trigger_scheduled_activation_invites_with_context(app):
    with app.app_context():
        trigger_scheduled_activation_invites()


def start_scheduler(flask_app):
    global app, _scheduler_initialized_jobs
    app = flask_app

    # Determine if this process should initialize and start the scheduler
    should_run_scheduler_in_this_process = False
    if flask_app.debug: # Werkzeug reloader is active
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            logger.info("=== [SCHEDULER] Context: Werkzeug child process (debug mode). Scheduler will be initialized here. ===")
            should_run_scheduler_in_this_process = True
        else:
            logger.info("=== [SCHEDULER] Context: Werkzeug parent/monitor process (debug mode). Scheduler will NOT be initialized here. ===")
            # Assign the scheduler object to the app for potential access, but don't start it.
            flask_app.scheduler = scheduler
            return # Explicitly return for Werkzeug parent process
    else: # Not in debug mode (e.g., production with Gunicorn, or Flask run with debug=False)
        logger.info("=== [SCHEDULER] Context: Non-debug mode (e.g., production). Scheduler will be initialized here. ===")
        should_run_scheduler_in_this_process = True

    if not should_run_scheduler_in_this_process:
        # This case should ideally not be reached if the logic above is correct,
        # but as a safeguard:
        logger.info("=== [SCHEDULER] Context: Undetermined or non-primary process. Scheduler will NOT be initialized here. ===")
        flask_app.scheduler = scheduler
        return

    # --- Proceed to add jobs and start scheduler only if in the correct process ---
    if not _scheduler_initialized_jobs:  # Add jobs if not already added for this scheduler instance
        logger.info("=== [SCHEDULER] Initializing and adding jobs... ===")
        scheduler.add_job(
            func=check_and_send_reminders_with_context,
            trigger="interval",
            hours=1,
            id="reminder_job",
            replace_existing=True,
            kwargs={"app": app},
        )

        # Activation invites at 10:15
        scheduler.add_job(
            func=trigger_scheduled_activation_invites_with_context,
            trigger="cron",
            hour=6,
            minute=00,
            id="activation_invite_job",
            replace_existing=True,
            kwargs={"app": app}
        )

        # Daily activation summary at 07:00
        scheduler.add_job(
            func=send_daily_activation_summary_with_context,
            trigger="cron",
            hour=7,
            minute=00,
            id="daily_activation_summary_job",
            replace_existing=True,
            kwargs={"app": app}
        )

        _scheduler_initialized_jobs = True
        logger.info("=== [SCHEDULER] Jobs added. ===")
    else:
        logger.info("=== [SCHEDULER] Jobs already initialized for this scheduler instance. Skipping add_job calls. ===")

    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("=== [SCHEDULER] Scheduler started successfully by this process. ===")
        except Exception as e: 
            if "SchedulerAlreadyRunningError" in str(type(e)) or "scheduler has already been started" in str(e).lower():
                 logger.info("=== [SCHEDULER] Scheduler was already running when start() was called by this process. ===")
            else:
                 logger.error(f"=== [SCHEDULER] Failed to start scheduler: {e}", exc_info=True)
    else:
        logger.info("=== [SCHEDULER] Scheduler is already running in this process. ===")
        # If scheduler is running, ensure jobs are marked as initialized for this instance
        # This might be redundant if the above logic is perfect but acts as a safeguard.
        if not _scheduler_initialized_jobs:
            logger.warning("=== [SCHEDULER] Scheduler running but jobs flag was false. This state is unexpected. Marking jobs as initialized. ===")
            _scheduler_initialized_jobs = True

    flask_app.scheduler = scheduler


def shutdown_scheduler():
    if scheduler.running:
        logger.info("Shutting down reminder scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler was not running.")


if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    start_scheduler(app)