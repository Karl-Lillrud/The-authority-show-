async function buyCredits(credits, amount) {
  const user_id = localStorage.getItem("user_id");
  if (!user_id) {
    alert("You must be logged in to buy credits.");
    return;
  }

  try {
    const res = await fetch("/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, amount }) // ✅ FIXED HERE
    });

    const data = await res.json();
    if (data.sessionId) {
      const stripe = Stripe("pk_test_51R4IEVPSYBEkSARW1VDrIwirpgzraNlH1Ms4JDcrHBytkClnLwLIdaTV6zb9FrwYoBmpRqgtnJXGR5Q0VUKYfX7s00kmz7AEQk"); 
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
