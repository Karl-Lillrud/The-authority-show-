async function postPodcastData(podName, podRss) {
  try {
    const response = await fetch("/post_podcast_data", {
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
        "Content-Type": "application/json"
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
    const data = await response.json();
    if (data.status === "ok") {
      return data.feed; // Return feed data for further processing
    } else {
      console.error("Error fetching RSS feed:", data);
      throw new Error("Error fetching RSS feed");
    }
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
    throw error;
  }
}

// Optionally export the function if you're using modules:
// export { fetchRSSData };
