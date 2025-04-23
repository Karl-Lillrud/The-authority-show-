// src/frontend/static/requests/activityRequests.js
export async function getActivitiesRequest() {
  try {
    const res = await fetch("/get_activities", { method: "GET" });
    const data = await res.json();
    if (res.ok) {
      return data;
    } else {
      console.error("Failed to fetch activities:", data.error);
      return [];
    }
  } catch (err) {
    console.error("Error fetching activities:", err);
    return [];
  }
}
