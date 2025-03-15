// Function to add a new podcast
export async function addPodcast(data) {
  try {
    const response = await fetch("/add_podcasts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    return await response.json();
  } catch (error) {
    console.error("Error adding podcast:", error);
    throw error;
  }
}

// Function to get all podcasts
export async function fetchPodcasts() {
  try {
    const response = await fetch("/get_podcasts", {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching podcasts:", error);
    throw error;
  }
}

// Function to get a podcast by ID
export async function fetchPodcast(podcastId) {
  try {
    const response = await fetch(`/get_podcasts/${podcastId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching podcast:", error);
    throw error;
  }
}

// Function to update a podcast
export async function updatePodcast(podcastId, podcastData) {
  try {
    const response = await fetch(`/edit_podcasts/${podcastId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData)
    });
    return await response.json();
  } catch (error) {
    console.error("Error updating podcast:", error);
    throw error;
  }
}

// Function to delete a podcast
export async function deletePodcast(podcastId) {
  try {
    const response = await fetch(`/delete_podcasts/${podcastId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error deleting podcast:", error);
    throw error;
  }
}

// Enhanced function to fetch RSS data with episodes, description, and social media
export async function fetchRSSData(rssUrl) {
  try {
    const response = await fetch(rssUrl);
    if (!response.ok) {
      throw new Error("Failed to fetch RSS feed.");
    }

    const rssText = await response.text();
    const parser = new DOMParser();
    const rssDoc = parser.parseFromString(rssText, "application/xml");

    // Get podcast title
    const titleElement = rssDoc.querySelector("channel > title");
    if (!titleElement) {
      throw new Error("RSS feed does not contain a title.");
    }

    // Get podcast image
    const imageElement = rssDoc.querySelector("channel > image > url");

    // Get podcast description
    const descriptionElement = rssDoc.querySelector("channel > description");

    // Get podcast link (website)
    const linkElement = rssDoc.querySelector("channel > link");

    // Get podcast language
    const languageElement = rssDoc.querySelector("channel > language");

    // Get podcast author/owner
    const authorElement = rssDoc.querySelector(
      "channel > itunes\\:author, author"
    );
    const ownerNameElement = rssDoc.querySelector(
      "channel > itunes\\:owner > itunes\\:name"
    );

    // Get podcast category
    const categoryElement = rssDoc.querySelector("channel > itunes\\:category");
    const category = categoryElement
      ? categoryElement.getAttribute("text")
      : null;

    // Extract social media links from description or link elements
    const socialMediaLinks = extractSocialMediaLinks(
      descriptionElement ? descriptionElement.textContent : "",
      linkElement ? linkElement.textContent : ""
    );

    // Get episodes
    const episodeElements = rssDoc.querySelectorAll("channel > item");
    const episodes = Array.from(episodeElements).map((item) => {
      const episodeTitle = item.querySelector("title")?.textContent || "";
      const episodeDescription =
        item.querySelector("description")?.textContent || "";
      const episodeLink = item.querySelector("link")?.textContent || "";
      const pubDate = item.querySelector("pubDate")?.textContent || "";
      const duration =
        item.querySelector("itunes\\:duration")?.textContent || "";
      const episodeImage =
        item.querySelector("itunes\\:image")?.getAttribute("href") ||
        imageElement?.textContent ||
        null;

      // Get enclosure (audio file)
      const enclosure = item.querySelector("enclosure");
      const audioUrl = enclosure ? enclosure.getAttribute("url") : null;
      const audioType = enclosure ? enclosure.getAttribute("type") : null;
      const audioLength = enclosure ? enclosure.getAttribute("length") : null;

      // Get GUID for unique identifier
      const guidElement = item.querySelector("guid");
      const guid = guidElement ? guidElement.textContent : null;

      // Get episode number and season if available
      const episodeNumber =
        item.querySelector("itunes\\:episode")?.textContent || null;
      const seasonNumber =
        item.querySelector("itunes\\:season")?.textContent || null;

      return {
        title: episodeTitle,
        description: episodeDescription,
        link: episodeLink,
        pubDate: pubDate,
        duration: duration,
        image: episodeImage,
        guid: guid,
        episodeNumber: episodeNumber,
        seasonNumber: seasonNumber,
        audio: {
          url: audioUrl,
          type: audioType,
          length: audioLength
        }
      };
    });

    // Return all RSS data
    return {
      title: titleElement.textContent,
      description: descriptionElement ? descriptionElement.textContent : null,
      link: linkElement ? linkElement.textContent : null,
      language: languageElement ? languageElement.textContent : null,
      author: authorElement
        ? authorElement.textContent
        : ownerNameElement
        ? ownerNameElement.textContent
        : null,
      category: category,
      imageUrl: imageElement ? imageElement.textContent : null,
      socialMedia: socialMediaLinks,
      episodes: episodes,
      raw: rssDoc // Include the entire parsed RSS document
    };
  } catch (error) {
    console.error("Error in fetchRSSData:", error);
    throw new Error(`Error fetching RSS feed: ${error.message}`);
  }
}

// Helper function to extract social media links from text
function extractSocialMediaLinks(description, link) {
  const socialMediaLinks = [];

  // Regular expressions for common social media platforms
  const patterns = {
    twitter: /https?:\/\/(www\.)?twitter\.com\/[a-zA-Z0-9_]+/g,
    facebook: /https?:\/\/(www\.)?facebook\.com\/[a-zA-Z0-9.]+/g,
    instagram: /https?:\/\/(www\.)?instagram\.com\/[a-zA-Z0-9_]+/g,
    youtube: /https?:\/\/(www\.)?youtube\.com\/(channel|user)\/[a-zA-Z0-9_-]+/g,
    linkedin: /https?:\/\/(www\.)?linkedin\.com\/(in|company)\/[a-zA-Z0-9_-]+/g,
    website:
      /https?:\/\/(?!twitter|facebook|instagram|youtube|linkedin)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g
  };

  // Combine description and link for searching
  const textToSearch = `${description} ${link}`;

  // Extract links for each platform
  for (const [platform, pattern] of Object.entries(patterns)) {
    const matches = textToSearch.match(pattern);
    if (matches) {
      matches.forEach((match) => {
        socialMediaLinks.push({
          platform: platform,
          url: match
        });
      });
    }
  }

  return socialMediaLinks;
}
