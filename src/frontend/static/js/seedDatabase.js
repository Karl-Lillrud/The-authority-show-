// seedDatabase.js - Script to seed the database with initial data
import { addPodcast, fetchPodcasts } from "./requests/podcastRequests.js";
import {
  registerEpisode,
  fetchEpisodesByPodcast
} from "./requests/episodeRequest.js";
import {
  addGuestRequest,
  fetchGuestsRequest
} from "./requests/guestRequests.js";

// Sample podcast logo (base64 encoded placeholder - replace with your actual logo)
const podcastLogo =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgMjAwIDIwMCI+CiAgPHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNmZjdmM2YiLz4KICA8Y2lyY2xlIGN4PSIxMDAiIGN5PSI4MCIgcj0iNDAiIGZpbGw9IiNmZmYiLz4KICA8cmVjdCB4PSI2MCIgeT0iMTMwIiB3aWR0aD0iODAiIGhlaWdodD0iMzAiIGZpbGw9IiNmZmYiLz4KICA8cmVjdCB4PSI3MCIgeT0iMTcwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTAiIGZpbGw9IiNmZmYiLz4KPC9zdmc+";

// Sample data for podcasts
const samplePodcasts = [
  {
    podName: "Tech Insights",
    ownerName: "Sarah Johnson",
    hostName: "Alex Chen",
    rssFeed: "https://techinsights.example.com/feed",
    googleCal: "https://calendar.google.com/calendar/techinsights",
    guestUrl: "https://techinsights.example.com/guest-form",
    email: "contact@techinsights.example.com",
    description:
      "A podcast exploring the latest trends and innovations in technology, featuring interviews with industry leaders and experts.",
    category: "Technology",
    logoUrl: podcastLogo,
    socialMedia: [
      "https://facebook.com/techinsights",
      "https://instagram.com/techinsights",
      "https://linkedin.com/company/techinsights",
      "https://twitter.com/techinsights",
      "https://tiktok.com/@techinsights"
    ]
  },
  {
    podName: "Creative Minds",
    ownerName: "Michael Roberts",
    hostName: "Emily Parker",
    rssFeed: "https://creativeminds.example.com/feed",
    googleCal: "https://calendar.google.com/calendar/creativeminds",
    guestUrl: "https://creativeminds.example.com/guest-form",
    email: "contact@creativeminds.example.com",
    description:
      "Join us as we dive into the creative process with artists, writers, musicians, and other creative professionals from around the world.",
    category: "Arts",
    logoUrl: podcastLogo,
    socialMedia: [
      "https://facebook.com/creativeminds",
      "https://instagram.com/creativeminds",
      "https://linkedin.com/company/creativeminds",
      "https://twitter.com/creativeminds"
    ]
  }
];

// Sample data for episodes
const sampleEpisodes = [
  {
    title: "The Future of AI",
    description:
      "In this episode, we discuss the future of artificial intelligence with leading AI researcher Dr. Jane Smith.",
    publishDate: new Date(2023, 5, 15).toISOString(),
    duration: 45,
    status: "Published"
  },
  {
    title: "Blockchain Revolution",
    description:
      "Exploring how blockchain technology is transforming industries beyond cryptocurrency.",
    publishDate: new Date(2023, 6, 1).toISOString(),
    duration: 52,
    status: "Published"
  },
  {
    title: "Design Thinking",
    description:
      "A conversation with award-winning designer Mark Wilson about the principles of design thinking.",
    publishDate: new Date(2023, 6, 15).toISOString(),
    duration: 38,
    status: "Published"
  }
];

// Sample data for guests
const sampleGuests = [
  {
    name: "Dr. Jane Smith",
    email: "jane.smith@example.com",
    description: "Leading AI researcher and author of 'The AI Future'",
    tags: ["AI", "Machine Learning", "Technology"],
    areasOfInterest: [
      "Artificial Intelligence",
      "Neural Networks",
      "Ethics in AI"
    ],
    linkedin: "https://linkedin.com/in/janesmith",
    twitter: "https://twitter.com/drjanesmith"
  },
  {
    name: "Mark Wilson",
    email: "mark.wilson@example.com",
    description: "Award-winning designer and creative director",
    tags: ["Design", "UX", "Creative"],
    areasOfInterest: ["User Experience", "Product Design", "Design Thinking"],
    linkedin: "https://linkedin.com/in/markwilson",
    twitter: "https://twitter.com/markwilsondesign"
  },
  {
    name: "Lisa Chen",
    email: "lisa.chen@example.com",
    description: "Blockchain expert and technology consultant",
    tags: ["Blockchain", "Cryptocurrency", "Technology"],
    areasOfInterest: [
      "Distributed Ledger Technology",
      "Smart Contracts",
      "Fintech"
    ],
    linkedin: "https://linkedin.com/in/lisachen",
    twitter: "https://twitter.com/lisachentech"
  }
];

// Function to check if a podcast already exists
async function podcastExists(podName) {
  try {
    const response = await fetchPodcasts();
    const podcasts = response.podcast || [];
    return podcasts.some((podcast) => podcast.podName === podName);
  } catch (error) {
    console.error("Error checking if podcast exists:", error);
    return false;
  }
}

// Function to check if an episode already exists
async function episodeExists(podcastId, title) {
  try {
    const episodes = await fetchEpisodesByPodcast(podcastId);
    return episodes.some((episode) => episode.title === title);
  } catch (error) {
    console.error("Error checking if episode exists:", error);
    return false;
  }
}

// Function to check if a guest already exists
async function guestExists(name, email) {
  try {
    const guests = await fetchGuestsRequest();
    return guests.some((guest) => guest.name === name && guest.email === email);
  } catch (error) {
    console.error("Error checking if guest exists:", error);
    return false;
  }
}

// Main function to seed the database
export async function seedDatabase() {
  console.log("Starting database seeding...");

  // Array to store created podcast IDs
  const podcastIds = [];

  // Create podcasts
  for (const podcastData of samplePodcasts) {
    if (await podcastExists(podcastData.podName)) {
      console.log(`Podcast "${podcastData.podName}" already exists. Skipping.`);

      // Get the ID of the existing podcast
      const response = await fetchPodcasts();
      const existingPodcast = response.podcast.find(
        (p) => p.podName === podcastData.podName
      );
      if (existingPodcast) {
        podcastIds.push(existingPodcast._id);
      }
      continue;
    }

    try {
      const response = await addPodcast(podcastData);
      if (response && response._id) {
        console.log(`Created podcast: ${podcastData.podName}`);
        podcastIds.push(response._id);
      } else {
        console.error(
          `Failed to create podcast: ${podcastData.podName}`,
          response
        );
      }
    } catch (error) {
      console.error(`Error creating podcast ${podcastData.podName}:`, error);
    }
  }

  // If no podcasts were created or found, exit
  if (podcastIds.length === 0) {
    console.log("No podcasts available. Exiting seeding process.");
    return;
  }

  // Create guests
  const guestIds = [];
  for (const guestData of sampleGuests) {
    if (await guestExists(guestData.name, guestData.email)) {
      console.log(`Guest "${guestData.name}" already exists. Skipping.`);

      // Get the ID of the existing guest
      const guests = await fetchGuestsRequest();
      const existingGuest = guests.find(
        (g) => g.name === guestData.name && g.email === guestData.email
      );
      if (existingGuest) {
        guestIds.push(existingGuest._id || existingGuest.id);
      }
      continue;
    }

    try {
      // Assign the guest to the first podcast
      const guestWithPodcastId = {
        ...guestData,
        podcastId: podcastIds[0]
      };

      const response = await addGuestRequest(guestWithPodcastId);
      if (response && (response._id || response.guest_id)) {
        console.log(`Created guest: ${guestData.name}`);
        guestIds.push(response._id || response.guest_id);
      } else {
        console.error(`Failed to create guest: ${guestData.name}`, response);
      }
    } catch (error) {
      console.error(`Error creating guest ${guestData.name}:`, error);
    }
  }

  // Create episodes
  for (let i = 0; i < sampleEpisodes.length; i++) {
    // Alternate between podcasts for the episodes
    const podcastIndex = i % podcastIds.length;
    const podcastId = podcastIds[podcastIndex];

    // Assign a guest to the episode
    const guestIndex = i % guestIds.length;
    const guestId = guestIds[guestIndex];

    const episodeData = {
      ...sampleEpisodes[i],
      podcastId,
      guestId
    };

    if (await episodeExists(podcastId, episodeData.title)) {
      console.log(`Episode "${episodeData.title}" already exists. Skipping.`);
      continue;
    }

    try {
      const response = await registerEpisode(episodeData);
      if (response && response.message) {
        console.log(`Created episode: ${episodeData.title}`);
      } else {
        console.error(
          `Failed to create episode: ${episodeData.title}`,
          response
        );
      }
    } catch (error) {
      console.error(`Error creating episode ${episodeData.title}:`, error);
    }
  }

  console.log("Database seeding completed!");
}

// Export a function to check if seeding is needed
export async function shouldSeedDatabase() {
  try {
    const response = await fetchPodcasts();
    return !response.podcast || response.podcast.length === 0;
  } catch (error) {
    console.error("Error checking if seeding is needed:", error);
    return true; // If there's an error, assume seeding is needed
  }
}
