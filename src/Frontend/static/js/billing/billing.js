async function buyCredits(credits, price) {
    const user_id = localStorage.getItem("user_id");
    if (!user_id) {
      alert("You must be logged in to buy credits.");
      return;
    }
  
    try {
      const res = await fetch("/create-checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id, credits, price }),
      });
  
      const data = await res.json();
      if (data.sessionId) {
        // Redirect to Stripe checkout
        const stripe = Stripe("your-publishable-key-here"); // Replace with your real Stripe publishable key
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else {
        document.getElementById("checkoutStatus").textContent =
          "❌ Failed to create Stripe checkout.";
      }
    } catch (err) {
      document.getElementById("checkoutStatus").textContent =
        "❌ Error: " + err.message;
    }
  }
  
  