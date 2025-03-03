// Kan vara bra att behålla för att visa exempeldata.
const podcasts = [
  {
    _id: "1",
    podName: "The Authority Show",
    ownerName: "John Smith",
    hostName: "John Smith, Jane Doe",
    rssFeed: "https://example.com/feed.rss",
    googleCal: "https://calendar.google.com/calendar/embed?src=example.com",
    guestUrl: "https://forms.example.com/guest",
    email: "contact@theauthorityshow.com",
    description:
      "A podcast about leadership and authority in various industries.",
    logoUrl:
      "https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg",
    category: "Business",
    socialMedia: [
      "https://facebook.com/theauthorityshow",
      "https://instagram.com/theauthorityshow",
      "https://linkedin.com/company/theauthorityshow",
      "https://twitter.com/authorityshow",
      "https://tiktok.com/@theauthorityshow",
      ""
    ]
  },
  {
    _id: "2",
    podName: "Tech Insights",
    ownerName: "Sarah Johnson",
    hostName: "Sarah Johnson",
    rssFeed: "https://techinsights.com/feed.rss",
    googleCal:
      "https://calendar.google.com/calendar/embed?src=techinsights.com",
    guestUrl: "https://forms.techinsights.com/guest",
    email: "info@techinsights.com",
    description:
      "Weekly discussions about the latest in technology and innovation.",
    logoUrl:
      "https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg",
    category: "Technology",
    socialMedia: [
      "https://facebook.com/techinsights",
      "https://instagram.com/techinsights",
      "https://linkedin.com/company/techinsights",
      "https://twitter.com/techinsights",
      "",
      ""
    ]
  },
  {
    _id: "3",
    podName: "Health Matters",
    ownerName: "Dr. Michael Brown",
    hostName: "Dr. Michael Brown, Dr. Lisa White",
    rssFeed: "https://healthmatters.com/feed.rss",
    googleCal: "",
    guestUrl: "https://forms.healthmatters.com/guest",
    email: "contact@healthmatters.com",
    description: "Expert advice on health, wellness, and medical topics.",
    logoUrl:
      "https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg",
    category: "Health & Wellness",
    socialMedia: [
      "https://facebook.com/healthmatters",
      "https://instagram.com/healthmatters",
      "",
      "https://twitter.com/healthmatters",
      "",
      ""
    ]
  }
];

// DOM elements
const loadingElement = document.getElementById("loading");
const podcastListElement = document.getElementById("podcast-list");
const podcastDetailElement = document.getElementById("podcast-detail");
const alertElement = document.getElementById("alert");

// Helper functions
function showAlert(message, type) {
  alertElement.textContent = message;
  alertElement.className = `alert alert-${type}`;
  alertElement.style.display = "block";

  setTimeout(() => {
    alertElement.style.display = "none";
  }, 3000);
}

function renderPodcastList() {
  podcastListElement.innerHTML = "";

  if (podcasts.length === 0) {
    podcastListElement.innerHTML = `
          <div style="text-align: center; padding: 3rem; background-color: white; border-radius: 8px;">
            <p style="color: #666;">No podcasts found</p>
          </div>
        `;
    return;
  }

  podcasts.forEach((podcast) => {
    const podcastCard = document.createElement("div");
    podcastCard.className = "podcast-card";
    podcastCard.innerHTML = `
          <div class="podcast-content">
            <div class="podcast-image" style="background-image: url('${
              podcast.logoUrl
            }')"></div>
            <div class="podcast-info">
              <div class="podcast-header">
                <div>
                  <h2 class="podcast-title">${podcast.podName}</h2>
                  <p class="podcast-meta"><span>Category:</span> ${
                    podcast.category
                  }</p>
                  <p class="podcast-meta"><span>Host:</span> ${
                    podcast.hostName || "Not specified"
                  }</p>
                  <p class="podcast-meta"><span>Owner:</span> ${
                    podcast.ownerName || "Not specified"
                  }</p>
                </div>
                <div class="podcast-actions">
                  <button class="action-btn view-btn" title="View podcast details" data-id="${
                    podcast._id
                  }">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  </button>
                  <button class="action-btn edit-btn" title="Edit podcast" data-id="${
                    podcast._id
                  }">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                    </svg>
                  </button>
                  <button class="action-btn delete-btn" title="Delete podcast" data-id="${
                    podcast._id
                  }">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 6h18"></path>
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <p class="podcast-description">${
                podcast.description || "No description available."
              }</p>
            </div>
          </div>
          <div class="podcast-footer">
            <button class="view-details-btn" data-id="${
              podcast._id
            }">View Details</button>
          </div>
        `;

    podcastListElement.appendChild(podcastCard);
  });

  // Add event listeners
  document
    .querySelectorAll(".view-btn, .view-details-btn")
    .forEach((button) => {
      button.addEventListener("click", (e) => {
        const podcastId = e.target.closest("button").dataset.id;
        viewPodcast(podcastId);
      });
    });

  document.querySelectorAll(".edit-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      const podcastId = e.target.closest("button").dataset.id;
      updatePodcast(podcastId);
    });
  });

  document.querySelectorAll(".delete-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      const podcastId = e.target.closest("button").dataset.id;
      deletePodcast(podcastId);
    });
  });
}

function renderPodcastDetail(podcast) {
  podcastDetailElement.innerHTML = `
        <div class="detail-header">
          <button class="back-btn" id="back-to-list">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 19-7-7 7-7"></path>
              <path d="M19 12H5"></path>
            </svg>
            Back to podcasts
          </button>
        </div>
        
        <div class="detail-content">
          <div class="detail-image" style="background-image: url('${
            podcast.logoUrl
          }')"></div>
          
          <div class="detail-info">
            <h1 class="detail-title">${podcast.podName}</h1>
            <p class="detail-category">${podcast.category}</p>
            
            <div class="detail-section">
              <h2>About</h2>
              <p>${podcast.description || "No description available."}</p>
            </div>
            
            <div class="separator"></div>
            
            <div class="detail-grid">
              <div class="detail-item">
                <h3>Podcast Owner</h3>
                <p>${podcast.ownerName || "Not specified"}</p>
              </div>
              <div class="detail-item">
                <h3>Host(s)</h3>
                <p>${podcast.hostName || "Not specified"}</p>
              </div>
              <div class="detail-item">
                <h3>Email Address</h3>
                <p>${podcast.email || "Not specified"}</p>
              </div>
              <div class="detail-item">
                <h3>RSS Feed</h3>
                ${
                  podcast.rssFeed
                    ? `<a href="${podcast.rssFeed}" target="_blank">${podcast.rssFeed}</a>`
                    : "<p>Not specified</p>"
                }
              </div>
            </div>
            
            <div class="separator"></div>
            
            <div class="detail-section">
              <h2>Scheduling</h2>
              <div class="detail-grid">
                <div class="detail-item">
                  <h3>Google Calendar</h3>
                  ${
                    podcast.googleCal
                      ? `<a href="${podcast.googleCal}" target="_blank" style="display: flex; align-items: center; gap: 0.5rem;">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                        <line x1="16" x2="16" y1="2" y2="6"></line>
                        <line x1="8" x2="8" y1="2" y2="6"></line>
                        <line x1="3" x2="21" y1="10" y2="10"></line>
                      </svg>
                      Calendar Link
                    </a>`
                      : `<p style="display: flex; align-items: center; gap: 0.5rem;">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                        <line x1="16" x2="16" y1="2" y2="6"></line>
                        <line x1="8" x2="8" y1="2" y2="6"></line>
                        <line x1="3" x2="21" y1="10" y2="10"></line>
                      </svg>
                      Not connected
                    </p>`
                  }
                </div>
                <div class="detail-item">
                  <h3>Calendar URL</h3>
                  <p>podmanager.com/?pod=${podcast.podName.replace(
                    /\s+/g,
                    ""
                  )}</p>
                </div>
                <div class="detail-item">
                  <h3>Guest Form URL</h3>
                  ${
                    podcast.guestUrl
                      ? `<a href="${podcast.guestUrl}" target="_blank">${podcast.guestUrl}</a>`
                      : "<p>Not specified</p>"
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

  document.getElementById("back-to-list").addEventListener("click", () => {
    podcastDetailElement.style.display = "none";
    podcastListElement.style.display = "flex";
  });
}

// Dessa är inte riktiga CRUDS det är bara för exempeldata.  Riktiga CRUDS finns i podcastRequest.js
function viewPodcast(podcastId) {
  const podcast = podcasts.find((p) => p._id === podcastId);
  if (podcast) {
    renderPodcastDetail(podcast);
    podcastListElement.style.display = "none";
    podcastDetailElement.style.display = "block";
  } else {
    showAlert("Podcast not found", "error");
  }
}

function updatePodcast(podcastId) {
  const podcast = podcasts.find((p) => p._id === podcastId);
  if (podcast) {
    // In a real app, this would navigate to an edit form or open a modal
    // For this demo, we'll just show an alert
    showAlert(`Editing podcast: ${podcast.podName}`, "success");

    // You would typically redirect to an edit form or open a modal here
    viewPodcast(podcastId);
  } else {
    showAlert("Podcast not found", "error");
  }
}

function deletePodcast(podcastId) {
  if (confirm("Are you sure you want to delete this podcast?")) {
    const podcastIndex = podcasts.findIndex((p) => p._id === podcastId);
    if (podcastIndex !== -1) {
      // Remove the podcast from the array
      const deletedPodcast = podcasts.splice(podcastIndex, 1)[0];

      // Re-render the list
      renderPodcastList();

      showAlert(`Deleted podcast: ${deletedPodcast.podName}`, "success");
    } else {
      showAlert("Podcast not found", "error");
    }
  }
}

// Initialize the app
function init() {
  // Simulate loading data
  setTimeout(() => {
    loadingElement.style.display = "none";
    renderPodcastList();
    podcastListElement.style.display = "flex";
  }, 1000);
}

// Start the app
init();
