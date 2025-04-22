import { showNotification } from "../components/notifications.js";

/**
 * Handles subscription plan upgrades via Stripe checkout
 */
async function upgradeSubscription(planName, amount) {
  try {
    // Get UI elements
    const button = document.querySelector(`button[data-plan="${planName}"]`);
    if (!button) {
      console.error(`Button not found for plan ${planName}`);
      return;
    }
    
    // Show loading state
    const originalText = button.textContent;
    button.textContent = "Processing...";
    button.disabled = true;

    // Call the backend to create a checkout session
    const res = await fetch("/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        amount, 
        plan: planName 
      }),
      credentials: "same-origin" // Important: include cookies for session
    });

    // Check if the response is HTML (likely a redirect to login page)
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("text/html")) {
      showNotification("Error", "Your session may have expired. Please try logging in again.", "error");
      button.textContent = originalText;
      button.disabled = false;
      
      // Redirect to login after a short delay
      setTimeout(() => {
        window.location.href = "/signin?redirect=" + encodeURIComponent(window.location.pathname);
      }, 2000);
      return;
    }

    const data = await res.json();
    
    if (data.sessionId) {
      // Initialize Stripe and redirect to checkout
      const stripe = Stripe("pk_test_51R4IEVPSYBEkSARW1VDrIwirpgzraNlH1Ms4JDcrHBytkClnLwLIdaTV6zb9FrwYoBmpRqgtnJXGR5Q0VUKYfX7s00kmz7AEQk");
      await stripe.redirectToCheckout({ sessionId: data.sessionId });
    } else {
      // Handle error
      showNotification("Error", data.error || "Failed to create checkout session", "error");
      button.textContent = originalText;
      button.disabled = false;
    }
  } catch (err) {
    console.error("Subscription upgrade error:", err);
    showNotification("Error", "An error occurred while processing your request.", "error");
    
    // Reset button state
    const button = document.querySelector(`button[data-plan="${planName}"]`);
    if (button) {
      button.disabled = false;
      button.textContent = "Upgrade";
    }
  }
}

/**
 * Fetches the current user's subscription status
 */
async function getCurrentSubscription() {
  try {
    const response = await fetch('/api/subscription', {
      credentials: 'same-origin' // Include cookies for auth
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        console.warn("User not authenticated");
        return null;
      }
      throw new Error(`Failed to fetch subscription: ${response.status}`);
    }
    
    const data = await response.json();
    return data.subscription;
  } catch (err) {
    console.error("Error fetching subscription:", err);
    return null;
  }
}

/**
 * Updates the UI to reflect the current subscription
 */
async function updateSubscriptionUI() {
  try {
    const subscription = await getCurrentSubscription();
    const currentPlanElement = document.getElementById("current-plan");
    const statusElement = document.getElementById("subscription-status");
    const expiryElement = document.getElementById("subscription-expiry");
    const renewalTextElement = document.getElementById("renewal-text");
    const cancelButton = document.getElementById("cancel-subscription-btn");
    
    if (!currentPlanElement || !statusElement || !expiryElement || !renewalTextElement) {
      console.warn("Subscription UI elements not found");
      return;
    }
    
    if (subscription) {
      currentPlanElement.textContent = subscription.plan || "Free";
      
      // Update the expiry date display
      if (subscription.end_date) {
        const endDate = new Date(subscription.end_date);
        expiryElement.textContent = endDate.toLocaleDateString();
      } else {
        expiryElement.textContent = "N/A";
      }
      
      // For cancelled subscriptions:
      if (subscription.is_cancelled) {
        statusElement.textContent = "Cancelled";
        statusElement.classList.add("cancelled");
        
        // Update renewal text for cancelled subscription
        renewalTextElement.textContent = `Your subscription will not renew. Access ends on ${expiryElement.textContent}.`;
        renewalTextElement.classList.add("cancellation-notice");
        
        // Disable cancel button if it exists
        if (cancelButton) {
          cancelButton.disabled = true;
          cancelButton.textContent = "Subscription Cancelled";
        }
      }

      // For active subscriptions:
      // Enable cancel button if subscription is active
      if (cancelButton && subscription.status === "active" && subscription.plan !== "Free") {
        cancelButton.disabled = false;
        cancelButton.textContent = "Cancel Subscription";
      }
      
      // Update status with cancelled indicator if needed
      if (subscription.is_cancelled) {
        statusElement.textContent = "Cancelled";
        statusElement.classList.add("cancelled");
        
        // Update renewal text for cancelled subscription
        renewalTextElement.textContent = `Your subscription will not renew. Access ends on ${expiryElement.textContent}.`;
        renewalTextElement.classList.add("cancellation-notice");
        
        // Disable cancel button if it exists
        if (cancelButton) {
          cancelButton.disabled = true;
          cancelButton.textContent = "Subscription Cancelled";
        }
        
        // Remove any existing renewal message element
        const renewalMessageElement = document.querySelector(".renewal-message");
        if (renewalMessageElement) {
          renewalMessageElement.remove();
        }
      } else {
        statusElement.textContent = subscription.status || "Inactive";
        statusElement.classList.remove("cancelled");
        
        // Update renewal text for active subscription
        if (subscription.status === "active" && subscription.end_date) {
          renewalTextElement.textContent = `Your subscription will automatically renew on ${expiryElement.textContent}.`;
          renewalTextElement.classList.remove("cancellation-notice");
        } else {
          renewalTextElement.textContent = `Expiry date: ${expiryElement.textContent}`;
          renewalTextElement.classList.remove("cancellation-notice");
        }
        
        // Enable cancel button if subscription is active
        if (cancelButton && subscription.status === "active" && subscription.plan !== "Free") {
          cancelButton.disabled = false;
          cancelButton.textContent = "Cancel Subscription";
        }
      }
      
      // Update UI based on current plan
      document.querySelectorAll(".plan-card").forEach(card => {
        const planName = card.querySelector("h3").textContent.trim();
        const upgradeBtn = card.querySelector(".plan-button");
        
        if (planName === "Free") {
          // Special handling for Free tier
          if (subscription.plan === "Free" || 
              (subscription.is_cancelled && subscription.status !== "active")) {
            // Only show Free as current plan if user is actually on Free plan
            // or their paid subscription is already inactive
            card.classList.add("current-plan");
            if (upgradeBtn) {
              upgradeBtn.textContent = "Current Plan";
              upgradeBtn.disabled = true;
            }
          } else if (subscription.is_cancelled && subscription.status === "active") {
            // If paid plan is cancelled but still active, show "Default Plan"
            card.classList.remove("current-plan");
            if (upgradeBtn) {
              upgradeBtn.textContent = "Default Plan";
              upgradeBtn.disabled = true;
            }
          } else {
            // Free is not the current plan and not cancelled
            card.classList.remove("current-plan");
            if (upgradeBtn) {
              upgradeBtn.textContent = "Default Plan";
              upgradeBtn.disabled = true;
            }
          }
        } else if (planName === subscription.plan) {
          // Handle the current subscription plan
          card.classList.add("current-plan");
          if (upgradeBtn) {
            upgradeBtn.textContent = subscription.is_cancelled ? "Cancelled" : "Current Plan";
            upgradeBtn.disabled = true;
          }
        } else {
          // Handle other plans
          card.classList.remove("current-plan");
          if (upgradeBtn) {
            upgradeBtn.textContent = "Upgrade";
            upgradeBtn.disabled = false;
          }
        }
      });
    } else {
      // Default values if no subscription found
      currentPlanElement.textContent = "Free";
      statusElement.textContent = "Inactive";
      expiryElement.textContent = "N/A";
      renewalTextElement.textContent = "Expiry date: N/A";
      
      // Disable cancel button if it exists
      if (cancelButton) {
        cancelButton.disabled = true;
      }
    }
  } catch (err) {
    console.error("Error updating subscription UI:", err);
  }
}

/**
 * Shows a confirmation popup for cancelling a subscription
 */
function showCancellationConfirmation() {
  // Create confirmation popup
  const popup = document.createElement('div');
  popup.className = 'confirmation-popup';
  
  // Ensure CSS is loaded
  const cssLink = document.querySelector('link[href*="subscription.css"]');
  if (!cssLink) {
    // Create and append the CSS link if not already present
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/css/account/subscription.css';
    document.head.appendChild(link);
  }
  
  popup.innerHTML = `
    <div class="confirmation-content">
      <h3>Cancel Subscription</h3>
      <p>Are you sure you want to cancel your subscription? You'll lose access to premium features at the end of your current billing period.</p>
      <div class="confirmation-buttons">
        <button class="cancel-btn">No, Keep My Plan</button>
        <button class="confirm-btn">Yes, Cancel</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  
  // Add animation after a short delay to ensure CSS transitions work
  setTimeout(() => popup.classList.add('active'), 10);
  
  // Add event listeners
  const cancelBtn = popup.querySelector('.cancel-btn');
  const confirmBtn = popup.querySelector('.confirm-btn');
  
  // Close popup when cancel is clicked
  cancelBtn.addEventListener('click', () => {
    popup.classList.remove('active');
    setTimeout(() => popup.remove(), 300);
  });
  
  // Handle confirmation action
  confirmBtn.addEventListener('click', async () => {
    try {
      // Show loading state on button
      confirmBtn.innerHTML = `
        <svg class="spinner" viewBox="0 0 50 50">
          <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
        </svg>
        Processing...
      `;
      confirmBtn.disabled = true;
      
      // Make API call to cancel subscription
      const response = await fetch('/cancel-subscription', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({})
      });
      
      if (response.ok) {
        // Parse the response to get any additional data
        const data = await response.json();
        
        // Show success notification with end date if available
        let successMessage = 'Your subscription has been cancelled.';
        if (data.endDate) {
          successMessage = `Your subscription will not renew. You will have access until ${data.endDate}.`;
        }
        
        showNotification('Success', successMessage, 'success');
        
        // Update UI to reflect cancelled status
        updateSubscriptionUI();
      } else {
        // Handle error
        const data = await response.json();
        showNotification('Error', data.error || 'Failed to cancel subscription', 'error');
      }
      
      // Close popup
      popup.classList.remove('active');
      setTimeout(() => popup.remove(), 300);
      
    } catch (err) {
      console.error('Error cancelling subscription:', err);
      showNotification('Error', 'An error occurred while processing your request.', 'error');
      
      // Reset button state
      confirmBtn.innerHTML = 'Yes, Cancel';
      confirmBtn.disabled = false;
    }
  });
}

// Initialize subscription buttons when document is loaded
document.addEventListener("DOMContentLoaded", function() {
  // Add click handlers to the subscription buttons
  const proButton = document.querySelector('.plan-card:nth-child(2) .plan-button');
  const enterpriseButton = document.querySelector('.plan-card:nth-child(3) .plan-button');
  
  if (proButton) {
    proButton.setAttribute('data-plan', 'Pro');
    proButton.addEventListener('click', () => upgradeSubscription('Pro', 9.99));
  }
  
  if (enterpriseButton) {
    enterpriseButton.setAttribute('data-plan', 'Enterprise');
    enterpriseButton.addEventListener('click', () => upgradeSubscription('Enterprise', 29.99));
  }
  
  // Add cancel subscription button handler
  const cancelSubscriptionBtn = document.getElementById('cancel-subscription-btn');
  if (cancelSubscriptionBtn) {
    cancelSubscriptionBtn.addEventListener('click', showCancellationConfirmation);
  }
  
  // Update UI with current subscription data
  updateSubscriptionUI();
});

// At the bottom of your DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", function() {
  // Add cancel subscription button handler
  const cancelSubscriptionBtn = document.getElementById('cancel-subscription-btn');
  if (cancelSubscriptionBtn) {
    console.log("Cancel subscription button found in subscription.js");
    cancelSubscriptionBtn.addEventListener('click', function(e) {
      console.log("Cancel button clicked in subscription.js");
      e.preventDefault(); // Prevent any default form submission
      showCancellationConfirmation();
    });
  } else {
    console.log("Cancel subscription button not found in subscription.js");
  }
});

// Export functions for use in other files
export { upgradeSubscription, getCurrentSubscription, updateSubscriptionUI, showCancellationConfirmation };