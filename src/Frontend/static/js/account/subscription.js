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
    
    if (!currentPlanElement || !statusElement || !expiryElement) {
      console.warn("Subscription UI elements not found");
      return;
    }
    
    if (subscription) {
      currentPlanElement.textContent = subscription.plan || "Free";
      statusElement.textContent = subscription.status || "Inactive";
      
      if (subscription.end_date) {
        const endDate = new Date(subscription.end_date);
        expiryElement.textContent = endDate.toLocaleDateString();
      } else {
        expiryElement.textContent = "N/A";
      }
      
      // Update UI based on current plan
      document.querySelectorAll(".plan-card").forEach(card => {
        const planName = card.querySelector("h3").textContent.trim();
        const upgradeBtn = card.querySelector(".plan-button");
        
        if (planName === subscription.plan) {
          card.classList.add("current-plan");
          if (upgradeBtn) {
            upgradeBtn.textContent = "Current Plan";
            upgradeBtn.disabled = true;
          }
        } else {
          card.classList.remove("current-plan");
        }
      });
    } else {
      // Default values if no subscription found
      currentPlanElement.textContent = "Free";
      statusElement.textContent = "Inactive";
      expiryElement.textContent = "N/A";
    }
  } catch (err) {
    console.error("Error updating subscription UI:", err);
  }
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
  
  // Update UI with current subscription data
  updateSubscriptionUI();
});

// Export functions for use in other files
export { upgradeSubscription, getCurrentSubscription, updateSubscriptionUI };