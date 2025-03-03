async function postPodcastData(podName, podRss) {
  try {
    const response = await fetch("/add_podcasts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ podName, podRss })
    });

    const result = await response.json();

    if (response.ok) {
      return result.redirectUrl; // Return the redirect URL
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error("Failed to register podcast:", error);
    throw error;
  }
}

async function savePodProfile(data) {
  try {
    const response = await fetch("/save_podprofile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();
    if (result.success) {
      return true;
    } else {
      throw new Error("Failed to save pod profile.");
    }
  } catch (error) {
    console.error("Error saving pod profile:", error);
    throw error;
  }
}

async function sendInvitation(email, subject, body) {
  try {
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/html" // Add this header to handle HTML content
      },
      body: JSON.stringify({ email, subject, body })
    });

    const result = await response.json();
    if (result.success) {
      console.log(`Invitation sent to ${email}`);
    } else {
      console.error(`Failed to send invitation to ${email}`);
    }
  } catch (error) {
    console.error("Error sending invitation:", error);
  }
}

async function fetchRSSData(rssUrl) {
  if (!rssUrl) return;
  try {
    const response = await fetch(
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
        rssUrl
      )}`
    );
    const data = await response.json(); // Parse JSON directly

    if (data.status === "ok") {
      document.getElementById("podcastNameInput").value = data.feed.title; // Update the input field with the podcast name
      return data.feed; // Return the feed data
    } else {
      throw new Error("Failed to fetch RSS data");
    }
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
    throw error;
  }
}
