import logging
import time
import threading
import requests
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
from backend.utils.email_utils import send_email
from backend.services.activateVerification import verify_activation_file_exists

logger = logging.getLogger(__name__)

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


class ActivationEmailTask(SchedulerTask):
    """Task for sending activation emails."""

    def __init__(self, api_base_url, emails_per_batch=5):
        super().__init__("activation_email", interval_seconds=3600)  # Run every hour
        self.api_base_url = api_base_url
        self.emails_per_batch = emails_per_batch

    def execute(self):
        """Send a batch of activation emails."""
        try:
            logger.info("Scheduler: Starting activation email task")
            
            # First, verify that the activation file exists in the blob storage
            if not verify_activation_file_exists():
                logger.error("Scheduler: Activation file not found in blob storage")
                return False
                
            # API call to send emails
            response = requests.post(
                f"{self.api_base_url}/send_activation_emails",
                json={"num_emails": self.emails_per_batch},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Scheduler: Successfully sent {data.get('emails_sent', 0)} activation emails")
                return True
            else:
                logger.error(f"Scheduler: Failed to send activation emails. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Scheduler: Error sending activation emails: {str(e)}", exc_info=True)
            return False

    def process_from_xml(self, xml_path):
        """Process emails from the XML file directly (legacy method)."""
        try:
            if not os.path.exists(xml_path):
                logger.error(f"Scheduler: XML file not found: {xml_path}")
                return []
                
            tree = ET.parse(xml_path)
            root = tree.getroot()
            users = []
            
            for user in root.findall(".//user"):
                email = user.find("email")
                name = user.find("name")
                podcast = user.find("podcast")
                
                if email is not None and email.text:
                    users.append({
                        "email": email.text,
                        "name": name.text if name is not None else "",
                        "podcast": podcast.text if podcast is not None else "Your Podcast"
                    })
            
            return users
            
        except Exception as e:
            logger.error(f"Scheduler: Error processing XML file: {str(e)}", exc_info=True)
            return []
            
    def send_direct_invitation(self, user_data):
        """Send an activation invitation directly (uses API now)."""
        try:
            # Use the API endpoint for consistent tracking
            response = requests.post(
                f"{self.api_base_url}/activation/invite",
                json={
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "podcast": user_data["podcast"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Scheduler: Activation invite sent to {user_data['email']}")
                return True
            else:
                logger.error(f"Scheduler: Failed to trigger activation for {user_data['email']} via API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Scheduler: Error sending activation for {user_data['email']}: {str(e)}", exc_info=True)
            return False


class Scheduler:
    """Background task scheduler."""

    def __init__(self, api_base_url):
        self.running = False
        self.tasks = []
        self.api_base_url = api_base_url
        logger.info(f"Scheduler initialized with API base URL: {api_base_url}")

    def add_task(self, task):
        """Add a task to the scheduler."""
        self.tasks.append(task)
        logger.info(f"Scheduler: Added task '{task.name}' with interval {task.interval_seconds}s")

    def initialize_default_tasks(self):
        """Initialize the default tasks for the scheduler."""
        # Add activation email task
        self.add_task(ActivationEmailTask(self.api_base_url))

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
