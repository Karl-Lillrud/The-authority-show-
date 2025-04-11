async function buyCredits(credits, price) {
  const user_id = localStorage.getItem("user_id");
  if (!user_id) {
    alert("You must be logged in to buy credits.");
    return;
  }

  try {
    const res = await fetch("/api/buy_credits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, credits, price }),
    });

    const data = await res.json();
    if (data.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      document.getElementById("checkoutStatus").textContent = "❌ Failed to create Stripe checkout.";
    }
  } catch (err) {
    document.getElementById("checkoutStatus").textContent = "❌ Error: " + err.message;
  }
}