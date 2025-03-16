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
    const itunesImageElement = rssDoc.querySelector("channel > itunes\\:image");
    const imageUrl = imageElement
      ? imageElement.textContent
      : itunesImageElement
      ? itunesImageElement.getAttribute("href")
      : null;

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
    const ownerEmailElement = rssDoc.querySelector(
      "channel > itunes\\:owner > itunes\\:email"
    );

    // Get podcast category
    const categoryElement = rssDoc.querySelector("channel > itunes\\:category");
    const category = categoryElement
      ? categoryElement.getAttribute("text")
      : null;

    // Get podcast explicit rating
    const explicitElement = rssDoc.querySelector("channel > itunes\\:explicit");
    const explicit = explicitElement
      ? explicitElement.textContent === "yes" ||
        explicitElement.textContent === "true"
      : false;

    // Get podcast type
    const typeElement = rssDoc.querySelector("channel > itunes\\:type");
    const podcastType = typeElement ? typeElement.textContent : "episodic";

    // Get podcast GUID
    const guidElement = rssDoc.querySelector("channel > guid");
    const guid = guidElement ? guidElement.textContent : null;

    // Get podcast publication date
    const pubDateElement = rssDoc.querySelector("channel > pubDate");
    const pubDate = pubDateElement ? pubDateElement.textContent : null;

    // Get last build date
    const lastBuildDateElement = rssDoc.querySelector(
      "channel > lastBuildDate"
    );
    const lastBuildDate = lastBuildDateElement
      ? lastBuildDateElement.textContent
      : null;

    // Get copyright information
    const copyrightElement = rssDoc.querySelector("channel > copyright");
    const copyright = copyrightElement ? copyrightElement.textContent : null;

    // Get iTunes ID (from feed URL or itunes:new-feed-url)
    const itunesId = extractItunesId(rssUrl) || "";

    // Get podcast keywords/tags
    const keywordsElement = rssDoc.querySelector("channel > itunes\\:keywords");
    const keywords = keywordsElement
      ? keywordsElement.textContent.split(",").map((k) => k.trim())
      : [];

    // Get funding information
    const fundingElement = rssDoc.querySelector("channel > podcast\\:funding");
    const fundingUrl = fundingElement
      ? fundingElement.getAttribute("url")
      : null;
    const fundingText = fundingElement ? fundingElement.textContent : null;

    // Get complete status (if podcast is finished)
    const completeElement = rssDoc.querySelector("channel > itunes\\:complete");
    const complete = completeElement
      ? completeElement.textContent === "yes"
      : false;

    // Extract social media links from description or link elements
    const socialMediaLinks = extractSocialMediaLinks(
      descriptionElement ? descriptionElement.textContent : "",
      linkElement ? linkElement.textContent : ""
    );

    // Get episodes (existing code)
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
        item.querySelector("itunes\\:image")?.getAttribute("href") || imageUrl;

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

      // Get episode type (full, trailer, bonus)
      const episodeType =
        item.querySelector("itunes\\:episodeType")?.textContent || "full";

      // Get episode explicit rating
      const episodeExplicit =
        item.querySelector("itunes\\:explicit")?.textContent === "yes" || false;

      // Get episode keywords
      const episodeKeywords =
        item
          .querySelector("itunes\\:keywords")
          ?.textContent.split(",")
          .map((k) => k.trim()) || [];

      // Get chapter markers if available
      const chapters = Array.from(
        item.querySelectorAll("podcast\\:chapter") || []
      ).map((chapter) => ({
        start: chapter.getAttribute("start"),
        title: chapter.getAttribute("title"),
        img: chapter.getAttribute("img") || null,
        url: chapter.getAttribute("url") || null
      }));

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
        episodeType: episodeType,
        explicit: episodeExplicit,
        keywords: episodeKeywords,
        chapters: chapters,
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
      ownerName: ownerNameElement ? ownerNameElement.textContent : null,
      ownerEmail: ownerEmailElement ? ownerEmailElement.textContent : null,
      category: category,
      explicit: explicit,
      podcastType: podcastType,
      guid: guid,
      pubDate: pubDate,
      lastBuildDate: lastBuildDate,
      copyright: copyright,
      itunesId: itunesId,
      keywords: keywords,
      fundingUrl: fundingUrl,
      fundingText: fundingText,
      complete: complete,
      imageUrl: imageUrl,
      socialMedia: socialMediaLinks,
      episodes: episodes,
      raw: rssDoc // Include the entire parsed RSS document
    };
  } catch (error) {
    console.error("Error in fetchRSSData:", error);
    throw new Error(`Error fetching RSS feed: ${error.message}`);
  }
}

// Helper function to extract iTunes ID from feed URL
function extractItunesId(url) {
  // Try to extract from iTunes URL format
  const itunesMatch = url.match(/\/id(\d+)/);
  if (itunesMatch && itunesMatch[1]) {
    return itunesMatch[1];
  }
  return null;
}

// Helper function to extract social media links from text (existing code)
function extractSocialMediaLinks(description, link) {
  // Your existing implementation
  // ...
}
