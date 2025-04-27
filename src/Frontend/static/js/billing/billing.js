let apiBaseUrl = '';
let stripePublicKey = '';
let stripe = null;

// Fetch configuration when the DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/config'); // Fetch from the new backend endpoint
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Failed to fetch config: ${response.statusText}`);
    }
    const config = await response.json();
    apiBaseUrl = config.apiBaseUrl || ''; // Use fetched API base URL or default to relative paths
    stripePublicKey = config.stripePublicKey;

    if (!stripePublicKey) {
      console.error("Stripe Public Key not found in config from server.");
      const statusElement = document.getElementById("checkoutStatus");
      if (statusElement) statusElement.textContent = "Configuration error: Payment key missing.";
      // Optionally disable payment buttons here
      return;
    }

    // Initialize Stripe here after fetching the key
    stripe = Stripe(stripePublicKey);

  } catch (error) {
    console.error("Error fetching or processing configuration:", error);
    const statusElement = document.getElementById("checkoutStatus");
    if (statusElement) statusElement.textContent = "Error loading payment configuration: " + error.message;
    // Optionally disable payment buttons here
  }
});

async function buyCredits(credits, amount) {
  const statusElement = document.getElementById("checkoutStatus");
  if (!stripe) {
      console.error("Stripe is not initialized. Cannot proceed with checkout.");
      if (statusElement) statusElement.textContent = "Error: Payment system not ready.";
      return; // Stop if Stripe didn't initialize
  }

  try {
    if (statusElement) statusElement.textContent = "Processing...";

    // Construct the full URL using the fetched base URL or use relative path if empty
    const checkoutUrl = apiBaseUrl ? `${apiBaseUrl}/create-checkout-session` : "/create-checkout-session";

    const res = await fetch(checkoutUrl, { // Use the constructed URL
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, credits }),
      credentials: "same-origin"
    });

    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("text/html")) {
      if (statusElement) statusElement.textContent = "Session expired. Please log in again.";
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
      // Use the globally initialized stripe object
      if (statusElement) statusElement.textContent = "Redirecting to payment...";
      await stripe.redirectToCheckout({ sessionId: data.sessionId });
    } else {
       // This case might be less likely now with the !res.ok check above
      if (statusElement) statusElement.textContent = "Failed to create checkout: " + (data.error || "Unknown error");
    }
  } catch (err) {
    console.error("Error during checkout:", err);
    if (statusElement) statusElement.textContent = "Error: " + err.message;
  }
}

/**
 * Fetches the user's purchase history from the backend.
 */
export async function fetchPurchases() {
  try {
    // Construct the full URL using the fetched base URL or use relative path if empty
    const purchasesUrl = apiBaseUrl ? `${apiBaseUrl}/api/purchases` : "/api/purchases";

    const response = await fetch(purchasesUrl, { // Use constructed URL
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
      credentials: "same-origin", // Include cookies for authentication
    });

    const contentType = response.headers.get("content-type");

    if (!response.ok) {
      let errorMsg = `Failed to fetch purchase history: ${response.statusText}`;
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Ignore if error response is not JSON
        }
      } else if (response.status === 401) {
         errorMsg = "Unauthorized: Please log in.";
      }
      throw new Error(errorMsg);
    }

    // Check content type before parsing JSON
    if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        // Assuming the backend returns { purchases: [...] }
        return data.purchases || []; 
    } else {
        throw new Error("Received non-JSON response from server for purchase history.");
    }

  } catch (error) {
    console.error("Error fetching purchase history:", error);
    // Re-throw the error so the calling function (e.g., in account.js) can handle it and show notifications
    throw error; 
  }
}
