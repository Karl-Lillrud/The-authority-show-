import { showNotification } from "../components/notifications.js";

let apiBaseUrl = '';
let stripePublicKey = '';
let stripe = null;

// Fetch configuration when the DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/config'); // Fetch from the backend endpoint
    if (!response.ok) {
       const errorData = await response.json();
       throw new Error(errorData.error || `Failed to fetch config: ${response.statusText}`);
    }
    const config = await response.json();
    apiBaseUrl = config.apiBaseUrl || ''; // Use fetched API base URL or default to relative paths
    stripePublicKey = config.stripePublicKey;

    if (!stripePublicKey) {
      console.error("Stripe Public Key not found in config from server.");
      showNotification("Error", "Configuration error: Payment key missing.", "error");
      // Optionally disable payment/subscription buttons here
      return;
    }

    // Initialize Stripe here after fetching the key
    stripe = Stripe(stripePublicKey);

    // Initialize UI elements that depend on config/Stripe being ready
    initializeSubscriptionButtons();
    updateSubscriptionUI();

  } catch (error) {
    console.error("Error fetching or processing configuration:", error);
    showNotification("Error", "Error loading configuration: " + error.message, "error");
    // Optionally disable payment/subscription buttons here
  }
});

/**
 * Handles subscription plan upgrades via Stripe checkout
 */
async function upgradeSubscription(planName, amount) {
   const button = document.querySelector(`button[data-plan="${planName}"]`);
   if (!stripe) {
      console.error("Stripe is not initialized. Cannot proceed with checkout.");
      showNotification("Error", "Payment system not ready.", "error");
      if (button) { // Reset button if it exists
          button.textContent = "Upgrade";
          button.disabled = false;
      }
      return; // Stop if Stripe didn't initialize
  }

  try {
    // Get UI elements
    if (!button) {
      console.error(`Button not found for plan ${planName}`);
      return;
    }

    // Show loading state
    const originalText = button.textContent;
    button.textContent = "Processing...";
    button.disabled = true;

    // Construct the full URL using the fetched base URL or use relative path if empty
    const checkoutUrl = apiBaseUrl ? `${apiBaseUrl}/create-checkout-session` : "/create-checkout-session";

    // Call the backend to create a checkout session
    const res = await fetch(checkoutUrl, { // Use constructed URL
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
         // Construct redirect URL carefully
        const redirectPath = "/signin?redirect=" + encodeURIComponent(window.location.pathname);
        // Use apiBaseUrl if available for the redirect, otherwise relative path
        window.location.href = apiBaseUrl ? `${apiBaseUrl}${redirectPath}` : redirectPath;
      }, 2000);
      return;
    }

     // Check for non-JSON error responses before trying to parse JSON
     if (!res.ok) {
        let errorMsg = `Failed to create checkout session: ${res.statusText}`;
        try {
            const errorData = await res.json();
            errorMsg = errorData.error || errorMsg;
        } catch (e) {
            // Ignore if response is not JSON
        }
        throw new Error(errorMsg);
    }

    const data = await res.json();

    if (data.sessionId) {
      // Use the globally initialized stripe object to redirect
      await stripe.redirectToCheckout({ sessionId: data.sessionId });
      // Note: redirectToCheckout doesn't return if successful, it navigates away.
      // If it fails, it throws an error caught below.
    } else {
      // This case might be less likely now with the !res.ok check above
      showNotification("Error", data.error || "Failed to create checkout session", "error");
      button.textContent = originalText;
      button.disabled = false;
    }
  } catch (err) {
    console.error("Subscription upgrade error:", err);
    showNotification("Error", "An error occurred while processing your request: " + err.message, "error");

    // Reset button state
    if (button) {
      button.disabled = false;
      // Check if originalText was captured, otherwise default to "Upgrade"
      button.textContent = button.textContent === "Processing..." ? "Upgrade" : button.textContent;
    }
  }
}

/**
 * Fetches the current user's subscription status
 */
async function getCurrentSubscription() {
  try {
    // Construct the full URL using the fetched base URL or use relative path if empty
    const subscriptionUrl = apiBaseUrl ? `${apiBaseUrl}/api/subscription` : '/api/subscription';

    const response = await fetch(subscriptionUrl, { // Use constructed URL
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
    
    // Make sure cancel button exists
    if (cancelButton) {
      // Default to hidden
      cancelButton.style.display = 'none';
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
          cancelButton.style.display = 'none'; // Hide it completely
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
        
        // Enable and show cancel button if subscription is active and paid
        if (cancelButton && subscription.status === "active" && subscription.plan !== "Free") {
          cancelButton.disabled = false;
          cancelButton.textContent = "Cancel Subscription";
          cancelButton.style.display = 'flex'; // Show it
        } else if (cancelButton) {
          // Hide button for free plan or inactive subscriptions
          cancelButton.style.display = 'none';
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
      
      console.log("Sending cancel subscription request to server...");
      
      // Try using the full path instead of just the endpoint
      // Ensure you're using the correct route with prefix
      const cancelUrl = '/api/cancel-subscription';

      // Make API call to cancel subscription
      const response = await fetch(cancelUrl, { // Use constructed URL
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        credentials: 'same-origin',
        body: JSON.stringify({}) 
      });
      
      console.log("Response received:", response.status, response.statusText);
      
      if (response.status === 404) {
        console.error("Endpoint not found (404). The cancel-subscription route may not be properly registered.");
        showNotification('Error', 'The subscription cancellation service is currently unavailable. Please contact support.', 'error');
        
        // Reset button state
        confirmBtn.innerHTML = 'Yes, Cancel';
        confirmBtn.disabled = false;
        
        // Don't close popup immediately on error
        return;
      }
      
      if (response.ok) {
        // Parse the response to get any additional data
        const data = await response.json();
        console.log("Cancellation successful with data:", data);
        
        // Show success notification with end date if available
        let successMessage = 'Your subscription has been cancelled.';
        if (data.endDate) {
          successMessage = `Your subscription will not renew. You will have access until ${data.endDate}.`;
        }
        
        showNotification('Success', successMessage, 'success');
        
        // Update UI to reflect cancelled status
        setTimeout(() => {
          updateSubscriptionUI();
          
          // Also update credits since they may have changed
          fetchStoreCredits();
        }, 500);
        
        // Close popup
        popup.classList.remove('active');
        setTimeout(() => popup.remove(), 300);
      } else {
        // Handle error
        try {
          const errorData = await response.json();
          console.error("Cancellation error:", errorData);
          showNotification('Error', errorData.error || 'Failed to cancel subscription', 'error');
        } catch (jsonError) {
          console.error("Error parsing error response:", jsonError);
          showNotification('Error', `Server error (${response.status}): Failed to cancel subscription`, 'error');
        }
        
        // Reset button state
        confirmBtn.innerHTML = 'Yes, Cancel';
        confirmBtn.disabled = false;
      }
    } catch (err) {
      console.error('Error cancelling subscription:', err);
      showNotification('Error', 'An error occurred while processing your request: ' + err.message, 'error');
      
      // Reset button state
      confirmBtn.innerHTML = 'Yes, Cancel';
      confirmBtn.disabled = false;
    }
  });
}

// Separate the handler function for better maintainability
function handleCancelClick(e) {
  e.preventDefault(); // Prevent any default action
  console.log("Cancel subscription button clicked");
  
  // Cancel directly without confirmation
  cancelSubscription();
}

/**
 * Directly cancels the subscription without showing a confirmation popup
 */
async function cancelSubscription() {
  // Get the cancel button
  const cancelButton = document.getElementById('cancel-subscription-btn');
  if (!cancelButton) return;
  
  try {
    // Show loading state on button
    const originalText = cancelButton.textContent;
    cancelButton.innerHTML = `
      <svg class="spinner" viewBox="0 0 50 50">
        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
      </svg>
      Processing...
    `;
    cancelButton.disabled = true;
    
    console.log("Sending cancel subscription request to server...");
    
    // Try using the full path instead of just the endpoint
    // Ensure you're using the correct route with prefix
    const cancelUrl = '/cancel-subscription';

    // Make API call to cancel subscription
    const response = await fetch(cancelUrl, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json' 
      },
      credentials: 'same-origin',
      body: JSON.stringify({}) 
    });
    
    console.log("Response received:", response.status, response.statusText);
    
    if (response.status === 404) {
      console.error("Endpoint not found (404). The cancel-subscription route may not be properly registered.");
      showNotification('Error', 'The subscription cancellation service is currently unavailable. Please contact support.', 'error');
      
      // Reset button state
      cancelButton.innerHTML = originalText;
      cancelButton.disabled = false;
      return;
    }
    
    if (response.ok) {
      // Parse the response to get any additional data
      const data = await response.json();
      console.log("Cancellation successful with data:", data);
      
      // Show success notification with end date if available
      let successMessage = 'Your subscription has been cancelled.';
      if (data.endDate) {
        successMessage = `Your subscription will not renew. You will have access until ${data.endDate}.`;
      }
      
      showNotification('Success', successMessage, 'success');
      
      
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
      
    } else {
      // Handle error
      try {
        const errorData = await response.json();
        console.error("Cancellation error:", errorData);
        showNotification('Error', errorData.error || 'Failed to cancel subscription', 'error');
      } catch (jsonError) {
        console.error("Error parsing error response:", jsonError);
        showNotification('Error', `Server error (${response.status}): Failed to cancel subscription`, 'error');
      }
      
      // Reset button state
      cancelButton.innerHTML = originalText;
      cancelButton.disabled = false;
    }
  } catch (err) {
    console.error('Error cancelling subscription:', err);
    showNotification('Error', 'An error occurred while processing your request: ' + err.message, 'error');
    
    // Reset button state
    if (cancelButton) {
      cancelButton.innerHTML = 'Cancel Subscription';
      cancelButton.disabled = false;
    }
  }
}

// Wrap button initialization in a function called after config is loaded
function initializeSubscriptionButtons() {
  // Add click handlers to the subscription buttons
  const proButton = document.querySelector('.plan-card:nth-child(2) .plan-button');
  const enterpriseButton = document.querySelector('.plan-card:nth-child(3) .plan-button');

  if (proButton) {
    proButton.setAttribute('data-plan', 'Pro');
    // Ensure amount is in dollars (the server will convert to cents)
    proButton.addEventListener('click', () => upgradeSubscription('Pro', 9.99));
  }

  if (enterpriseButton) {
    enterpriseButton.setAttribute('data-plan', 'Enterprise');
    // Ensure amount is in dollars (the server will convert to cents)
    enterpriseButton.addEventListener('click', () => upgradeSubscription('Enterprise', 29.99));
  }

  // Add cancel subscription button handler
  const cancelSubscriptionBtn = document.getElementById('cancel-subscription-btn');
  if (cancelSubscriptionBtn) {
    // Remove any existing event listeners to avoid duplicates
    cancelSubscriptionBtn.removeEventListener('click', handleCancelClick);
    // Add the click event listener
    cancelSubscriptionBtn.addEventListener('click', handleCancelClick);
    console.log("Cancel subscription button initialized");
  } else {
    console.log("Cancel subscription button not found in DOM");
  }
}

// Check if we just returned from a successful checkout
document.addEventListener('DOMContentLoaded', function() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('subscription_updated') === 'true') {
    // Force refresh credits display
    fetchStoreCredits();
    // Update the subscription UI
    updateSubscriptionUI();
    // Clear the URL parameter
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});

/**
 * Fetches the current user's available credits
 */
async function fetchStoreCredits() {
  try {
    const creditsElement = document.getElementById("available-credits");
    if (!creditsElement) return;
    
    const response = await fetch('/api/credits', {
      credentials: 'same-origin'
    });
    
    if (response.ok) {
      const data = await response.json();
      
      // Update the main credit display
      creditsElement.textContent = data.availableCredits;
      
      // Optionally, if you have elements for showing the breakdown:
      const subElement = document.getElementById("subscription-credits");
      const userElement = document.getElementById("purchased-credits");
      
      if (subElement) {
        subElement.textContent = data.subCredits || 0;
      }
      
      if (userElement) {
        userElement.textContent = data.storeCredits || 0;
      }
    }
  } catch (err) {
    console.error("Error fetching user credits:", err);
  }
}

// Export functions for use in other files
export { upgradeSubscription, getCurrentSubscription, updateSubscriptionUI, showCancellationConfirmation };