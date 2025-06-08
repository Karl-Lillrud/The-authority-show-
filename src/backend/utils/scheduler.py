import logging
import time
import threading
import requests
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
from backend.utils.email_utils import send_email, send_summary_email  # Updated import
from backend.services.activateVerificationService import verify_activation_file_exists
from backend.utils.activate import process_activation_emails, get_activation_stats

logger = logging.getLogger(__name__)

def render_email_content(template_name, **context):
    """
    Renders email content from a template.
    
    Args:
        template_name (str): The template name/path to render
        **context: The context variables to pass to the template
        
    Returns:
        str: The rendered HTML content
    """
    try:
        from flask import current_app, render_template
        with current_app.app_context():
            content = render_template(f'emails/{template_name}', **context)
            return content
    except Exception as e:
        logger.error(f"Error rendering email template '{template_name}': {e}", exc_info=True)
        # Fallback simple template if rendering fails
        fallback_content = f"""
        <html>
        <body>
            <h2>{context.get('subject', 'Notification')}</h2>
            <p>Hello {context.get('name', 'User')},</p>
            <p>{context.get('message', 'Thank you for using our service.')}</p>
            <p>Best regards,<br>PodManager Team</p>
        </body>
        </html>
        """
        return fallback_content

class SchedulerTask:
    """Base class for scheduler tasks."""

    def __init__(self, name, interval_seconds):
        self.name = name
        self.interval_seconds = interval_seconds
        self.last_run = datetime.now() - timedelta(seconds=interval_seconds)  # Run immediately on first check

    def should_run(self):
        """Check if the task should run based on its interval."""
        now = datetime.now()
        return (now - self.last_run).total_seconds() >= self.interval_seconds

    def execute(self):
        """Execute the task. Should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

    def mark_executed(self):
        """Mark the task as executed at the current time."""
        self.last_run = datetime.now()


class TimeBasedSchedulerTask(SchedulerTask):
    """Base class for scheduler tasks that run at a specific time of day."""

    def __init__(self, name, hour, minute=0):
        """
        Initialize a time-based task.
        
        Args:
            name (str): Name of the task
            hour (int): Hour to run the task (24-hour format)
            minute (int): Minute to run the task
        """
        super().__init__(name, interval_seconds=86400)  # 24 hours in seconds
        self.hour = hour
        self.minute = minute
        self.last_run_date = datetime.now().date() - timedelta(days=1)  # Force run on first day

    def should_run(self):
        """Check if the task should run based on the current time and last run date."""
        now = datetime.now()
        
        # Only run if we're in the correct hour and minute range (within 15 minutes)
        # and we haven't already run today
        return (now.hour == self.hour and 
                now.minute >= self.minute and 
                now.minute < self.minute + 15 and 
                now.date() > self.last_run_date)

    def mark_executed(self):
        """Mark the task as executed with the current date."""
        self.last_run_date = datetime.now().date()
        self.last_run = datetime.now()


class ActivationEmailTask(TimeBasedSchedulerTask):
    """Task for sending activation emails at 5 AM."""

    def __init__(self, api_base_url, emails_per_batch=None, flask_app=None):
        # Set to run at 5 AM
        super().__init__("activation_email", hour=5, minute=0)
        
        # Fix: Ensure api_base_url is a valid URL with schema
        if api_base_url and not api_base_url.startswith(('http://', 'https://')):
            # Convert relative URL to absolute URL with proper schema
            if os.getenv("ENVIRONMENT", "production").lower() == "local":
                # Local development
                self.api_base_url = f"http://localhost:{os.getenv('PORT', '8000')}"
            else:
                # Production environment
                self.api_base_url = f"https://{os.getenv('API_BASE_URL', 'app.podmanager.ai')}"
            
            logger.info(f"Converted API base URL to: {self.api_base_url}")
        else:
            self.api_base_url = api_base_url
            
        # We'll use None to indicate dynamic sizing based on days running
        # with initial batch of 89 and 20% daily increase
        self.emails_per_batch = emails_per_batch
        self.flask_app = flask_app  # Store Flask app instance

        logger.info(f"ActivationEmailTask initialized with API base URL: {self.api_base_url}, scheduled for 5:00 AM")
        if emails_per_batch is None:
            logger.info("Using dynamic batch sizing starting at 89 emails with 20% daily growth")
        else:
            logger.info(f"Using fixed batch size of {emails_per_batch} emails")
        if not self.flask_app:
            logger.warning("No Flask app provided to ActivationEmailTask - template rendering may fail if not handled downstream.")

    def execute(self):
        """Send a batch of activation emails using activate.py module."""
        try:
            logger.info(f"Scheduler: Starting activation email task at {datetime.now()}")
            
            result = None
            # Use process_activation_emails from activate.py
            # Pass None to use dynamic batch sizing
            if self.flask_app:
                with self.flask_app.app_context():
                    logger.info("ActivationEmailTask: Running process_activation_emails within app context.")
                    result = process_activation_emails(self.emails_per_batch)
            else:
                logger.warning("ActivationEmailTask: No Flask app context available. Running process_activation_emails without explicit context.")
                result = process_activation_emails(self.emails_per_batch)
            
            if result and result.get("success"):
                batch_size = result.get("batch_size", "unknown")
                logger.info(f"Scheduler: Successfully sent {result.get('emails_sent', 0)} activation emails out of batch size {batch_size}")
                return True
            else:
                logger.error(f"Scheduler: Failed to send activation emails: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Scheduler: Error sending activation emails: {str(e)}", exc_info=True)
            return False


class SummaryEmailTask(TimeBasedSchedulerTask):
    """Task for sending daily summary emails at 7 AM."""

    def __init__(self, api_base_url, flask_app=None):
        # Set to run at 7 AM
        super().__init__("summary_email", hour=7, minute=0)
        
        # Fix: Ensure api_base_url is a valid URL with schema
        if api_base_url and not api_base_url.startswith(('http://', 'https://')):
            # Convert relative URL to absolute URL with proper schema
            if os.getenv("ENVIRONMENT", "production").lower() == "local":
                # Local development
                self.api_base_url = f"http://localhost:{os.getenv('PORT', '8000')}"
            else:
                # Production environment
                self.api_base_url = f"https://{os.getenv('API_BASE_URL', 'app.podmanager.ai')}"
            
            logger.info(f"Converted API base URL to: {self.api_base_url}")
        else:
            self.api_base_url = api_base_url
        
        # Store Flask app reference for application context
        self.flask_app = flask_app
        if not flask_app:
            logger.warning("No Flask app provided to SummaryEmailTask - rendering templates may fail")
            
        logger.info(f"SummaryEmailTask initialized with API base URL: {self.api_base_url}, scheduled for 7:00 AM")

    def execute(self):
        """Send a daily summary email."""
        try:
            logger.info(f"Scheduler: Starting summary email task at {datetime.now()}")
            
            # Get activation statistics
            stats = get_activation_stats()
            if not stats or not stats.get("success"):
                logger.error(f"Scheduler: Failed to get activation stats: {stats.get('error', 'Unknown error')}")
                return False
            
            # Get batch configuration information
            try:
                from backend.utils.activate import get_batch_config
                batch_config = get_batch_config()
                current_batch_size = batch_config["batch_size"]
                days_running = batch_config["days_running"]
                next_batch_size = int(current_batch_size * 1.20)  # 20% growth
            except Exception as e:
                logger.error(f"Failed to get batch configuration: {e}")
                current_batch_size = "Unknown"
                days_running = "Unknown"
                next_batch_size = "Unknown"
            
            # Send summary email to admin
            admin_email = os.getenv("ADMIN_EMAIL", "contact@podmanager.ai")
            subject = f"PodManager Daily Activation Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Prepare context for the email template
            context = {
                "subject": subject,
                "total_podcasts": stats.get("total_podcasts", 0),
                "emails_sent": stats.get("emails_sent", 0),
                "podcasts_remaining": stats.get("podcasts_remaining", 0),
                "last_sent_date": stats.get("last_sent_date", "Never"),
                "batch_size": current_batch_size,
                "days_running": days_running,
                "next_batch_size": next_batch_size,
                "current_year": datetime.now().year  # Add current year for the footer
            }
            
            # Use the send_summary_email function with proper app context
            if self.flask_app:
                with self.flask_app.app_context():
                    # Import here to avoid circular import
                    from backend.utils.email_utils import send_summary_email
                    logger.info(f"Sending summary email to {admin_email} with app context")
                    result = send_summary_email(admin_email, subject, context)
            else:
                # Try to get current app if flask_app wasn't provided
                try:
                    from flask import current_app
                    with current_app.app_context():
                        from backend.utils.email_utils import send_summary_email
                        logger.info(f"Sending summary email to {admin_email} with current_app context")
                        result = send_summary_email(admin_email, subject, context)
                except Exception as app_err:
                    logger.error(f"No Flask app context available: {app_err}")
                    # Attempt a direct send without app context as fallback
                    from backend.utils.email_utils import send_email
                    
                    # Create a basic HTML email directly without template
                    html_content = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2>PodManager Activation Summary</h2>
                            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                            <p><strong>Total Podcasts:</strong> {stats.get("total_podcasts", 0)}</p>
                            <p><strong>Emails Sent:</strong> {stats.get("emails_sent", 0)}</p>
                            <p><strong>Podcasts Remaining:</strong> {stats.get("podcasts_remaining", 0)}</p>
                            <p><strong>Last Sent Date:</strong> {stats.get("last_sent_date", "Never")}</p>
                            <p><strong>Current Batch Size:</strong> {current_batch_size}</p>
                            <p><strong>Days Running:</strong> {days_running}</p>
                            <p><strong>Next Batch Size:</strong> {next_batch_size}</p>
                        </div>
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                            <p style="color: #666; font-size: 14px;">
                                &copy; {datetime.now().year} PodManager.ai. All rights reserved.
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    logger.info(f"Sending summary email to {admin_email} without app context (fallback)")
                    result = send_email(admin_email, subject, html_content)
            
            if result.get("success", False):
                logger.info(f"Scheduler: Successfully sent summary email to {admin_email}")
                return True
            else:
                logger.error(f"Scheduler: Failed to send summary email: {result.get('error', 'Unknown error')}")
                return False
            
        except Exception as e:
            logger.error(f"Scheduler: Error sending summary email: {str(e)}", exc_info=True)
            return False


class Scheduler:
    """Background task scheduler."""

    def __init__(self, api_base_url, flask_app=None):
        self.running = False
        self.tasks = []
        self.api_base_url = api_base_url
        self.flask_app = flask_app
        logger.info(f"Scheduler initialized with API base URL: {api_base_url}")
        if flask_app:
            logger.info("Flask app provided to scheduler")
        else:
            logger.warning("No Flask app provided to scheduler - template rendering may fail")

    def add_task(self, task):
        """Add a task to the scheduler."""
        self.tasks.append(task)
        logger.info(f"Scheduler: Added task '{task.name}' with interval {task.interval_seconds}s")

    def initialize_default_tasks(self):
        """Initialize the default tasks for the scheduler."""
        # Add activation email task (runs at 5 AM) with dynamic batch sizing
        self.add_task(ActivationEmailTask(self.api_base_url, emails_per_batch=None, flask_app=self.flask_app))
        
        # Add summary email task (runs at 7 AM)
        self.add_task(SummaryEmailTask(self.api_base_url, flask_app=self.flask_app))

    def run_forever(self):
        """Run the scheduler in a loop."""
        self.running = True
        logger.info("Scheduler: Starting main loop")

        while self.running:
            try:
                for task in self.tasks:
                    if task.should_run():
                        logger.info(f"Scheduler: Running task '{task.name}'")
                        success = task.execute()
                        if success:
                            task.mark_executed()
                            logger.info(f"Scheduler: Task '{task.name}' completed successfully")
                        else:
                            logger.warning(f"Scheduler: Task '{task.name}' failed")
            except Exception as e:
                logger.error(f"Scheduler: Error in main loop: {str(e)}", exc_info=True)

            # Sleep for a short period to avoid CPU hogging
            time.sleep(5)

    def start(self):
        """Start the scheduler in a background thread."""
        thread = threading.Thread(target=self.run_forever, daemon=True)
        thread.start()
        logger.info("Scheduler: Started in background thread")
        return thread

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Scheduler: Stopping")

# Add this function to initialize and start the scheduler
def start_scheduler(api_base_url_or_app):
    """
    Initializes and starts the scheduler with the given API base URL or Flask app.
    
    Args:
        api_base_url_or_app: The base URL for API requests or the Flask app instance
        
    Returns:
        Scheduler: The initialized and started scheduler instance
    """
    try:
        flask_app = None
        api_base_url = None
        
        # Handle case where we get a Flask app instead of a URL string
        if str(api_base_url_or_app).startswith('<Flask'):
            flask_app = api_base_url_or_app
            # Use environment variables to determine the proper URL
            if os.getenv("ENVIRONMENT", "production").lower() == "local":
                api_base_url = f"http://localhost:{os.getenv('PORT', '8000')}"
            else:
                api_base_url = f"https://{os.getenv('API_BASE_URL', 'app.podmanager.ai')}"
            logger.info(f"Extracted Flask app and API URL: {api_base_url}")
        else:
            api_base_url = api_base_url_or_app
        
        logger.info(f"Initializing scheduler with API base URL: {api_base_url}")
        
        # Create a scheduler instance with both API URL and Flask app
        scheduler_instance = Scheduler(api_base_url, flask_app=flask_app)
        
        # Initialize default tasks
        scheduler_instance.initialize_default_tasks()
        
        # Start the scheduler
        thread = scheduler_instance.start()
        
        logger.info(f"Scheduler started successfully on thread: {thread.name}")
        
        return scheduler_instance
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
        raise