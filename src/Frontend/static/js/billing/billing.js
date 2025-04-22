async function buyCredits(credits, amount) {
  try {
    const statusElement = document.getElementById("checkoutStatus");
    if (statusElement) statusElement.textContent = "Processing...";

    const res = await fetch("/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, credits }),  // ✅ FIXED HERE
      credentials: "same-origin"
    });

    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("text/html")) {
      if (statusElement) statusElement.textContent = "Session expired. Please log in again.";
      setTimeout(() => {
        window.location.href = "/signin?redirect=" + encodeURIComponent(window.location.pathname);
      }, 2000);
      return;
    }

    const data = await res.json();
    if (data.sessionId) {
      const stripe = Stripe("pk_test_51R4IEVPSYBEkSARW1VDrIwirpgzraNlH1Ms4JDcrHBytkClnLwLIdaTV6zb9FrwYoBmpRqgtnJXGR5Q0VUKYfX7s00kmz7AEQk"); 
      if (statusElement) statusElement.textContent = "Redirecting to payment...";
      await stripe.redirectToCheckout({ sessionId: data.sessionId });
    } else {
      if (statusElement) statusElement.textContent = "Failed to create checkout: " + (data.error || "Unknown error");
    }
  } catch (err) {
    console.error("Error during checkout:", err);
    const statusElement = document.getElementById("checkoutStatus");
    if (statusElement) statusElement.textContent = "Error: " + err.message;
  }
}
