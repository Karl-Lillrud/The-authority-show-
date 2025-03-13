from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from backend.database.mongo_connection import mailing_list_collection, subscriptions_collection  # Import your collections
import logging

Mailing_list_bp = Blueprint("Mailing_list_bp", __name__)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Subscribe route - user is added to mailing list only when they click 'Subscribe'
@Mailing_list_bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    user_id = session.get("user_id")
    
    if user_id:
        if request.method == 'POST':
            user_email = session.get("email")
            
            if user_email:
                # Check if the user is already in the mailing list
                existing_user = mailing_list_collection.find_one({"email": user_email})
                
                if not existing_user:  # Only subscribe if not already in the mailing list
                    result = mailing_list_collection.insert_one({"email": user_email})
                    
                    if result.inserted_id:
                        logger.info(f"User {user_email} added to the mailing list successfully.")
                        
                        # Optionally add to the subscriptions collection here
                        subscription_data = {
                            "user_email": user_email,
                            "subscriptionPlan": "Free Plan",  # Default plan
                            "autoRenew": True,  # Default auto-renew option
                            "discountCode": None  # You can set a discount code if needed
                        }

                        # Insert subscription data
                        subscription_result = subscriptions_collection.insert_one(subscription_data)

                        if subscription_result.inserted_id:
                            logger.info(f"User {user_email} added to the subscriptions collection.")
                            return jsonify({"success": True, "message": "You have been successfully subscribed!"})
                        else:
                            logger.error(f"Failed to add user {user_email} to the subscriptions collection.")
                            return jsonify({"success": False, "message": "Error subscribing to the plan."}), 500

                    else:
                        logger.error(f"Failed to add user {user_email} to the mailing list.")
                        return jsonify({"success": False, "message": "There was an error subscribing. Please try again."}), 500
                else:
                    logger.info(f"User {user_email} is already subscribed.")
                    return jsonify({"success": False, "message": "You are already subscribed to the mailing list."})
            else:
                logger.error("No email found in session.")
                return jsonify({"success": False, "message": "No email found. Please log in again."}), 400
        else:
            # If method is GET, just show the subscribe page
            return render_template('subscribe.html')
    else:
        # If no user is logged in, redirect to the login page
        return redirect(url_for("signin_bp.signin"))


# Unsubscribe route - removes the user from mailing list and subscription collection
@Mailing_list_bp.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    user_id = session.get("user_id")
    
    if user_id:
        user_email = session.get("email")  # Ensure email is in session
        
        if user_email:
            # Remove from mailing list collection
            mailing_list_result = mailing_list_collection.delete_one({"email": user_email})
            if mailing_list_result.deleted_count == 0:
                logger.warning(f"No user found with email {user_email} in the mailing list.")
            
            # Remove from subscriptions collection as well
            subscription_result = subscriptions_collection.delete_one({"user_email": user_email})
            if subscription_result.deleted_count == 0:
                logger.warning(f"No user found with email {user_email} in the subscriptions collection.")
            
            if mailing_list_result.deleted_count > 0 and subscription_result.deleted_count > 0:
                logger.info(f"User {user_email} unsubscribed successfully from both mailing list and subscriptions.")
                # Set a flag in session indicating that the user has unsubscribed
                session["unsubscribed"] = True
                return render_template('unsubscribed.html')  # Confirmation page
            else:
                logger.warning(f"Failed to unsubscribe user {user_email}. Not found in one or both collections.")
                return render_template('error.html', message="No subscription found for this email.")
        
        else:
            logger.error("No email found in session.")
            return redirect(url_for("signin_bp.signin"))
        
    else:
        logger.warning("User is not logged in. Redirecting to login page.")
        return redirect(url_for("signin_bp.signin"))


# This route could be used to check if user has unsubscribed and re-subscribe them if necessary
@Mailing_list_bp.route('/check_subscription', methods=['GET'])
def check_subscription():
    user_id = session.get("user_id")
    
    if user_id:
        user_email = session.get("email")
        
        if user_email:
            # Check if the user is in the mailing list
            existing_user = mailing_list_collection.find_one({"email": user_email})
            
            if not existing_user:  # Only show the subscribe option if not already in the list
                return redirect(url_for('Mailing_list_bp.subscribe'))
            else:
                return redirect(url_for('dashboard_bp.dashboard'))  # Redirect to the dashboard if already subscribed
        else:
            return redirect(url_for("signin_bp.signin"))
    else:
        return redirect(url_for("signin_bp.signin"))
