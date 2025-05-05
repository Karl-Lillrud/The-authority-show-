import { fetchStoreCredits } from "../../static/js/account/subscription.js";

export async function consumeStoreCredits(featureKey) {
    try {
        const res = await fetch('/credits/consume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feature: featureKey
            })
        });
    
        const result = await res.json();
        if (!res.ok) {
            throw new Error(result.error || "Failed to consume credits");
        }
    
        // ✅ Update the UI to reflect new credit balance
        await fetchStoreCredits();
    
        return result.data;
    } catch (error) {
        console.error("Error consuming credits:", error);
        throw error;
    }
}

export async function getCredits() {
    try {
      const response = await fetch("/api/credits", {
        credentials: "same-origin",
      });

      if (!response.ok) {
        console.warn("Failed to fetch credits:", response.status);
        return;
      }

      const data = await response.json();
      return data.availableCredits;
    } catch (err) {
      console.error("Error fetching user credits:", err);
      return null;
    }
  }
