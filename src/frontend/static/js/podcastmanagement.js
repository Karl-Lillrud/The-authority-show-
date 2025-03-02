import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "{{ url_for('static', filename='requests/podcastRequest.js') }}";

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");

  const formContainer = document.querySelector(".form-box");
  const podcastsContainer = document.querySelector(".podcasts-container");
  const form = document.getElementById("register-podcast-form");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("Form submitted");

    // Retrieve the form elements
    const podName = document.getElementById("pod-name")?.value.trim() || "";
    const email = document.getElementById("email")?.value.trim() || "";
    const category = document.getElementById("category")?.value.trim() || "";

    // Initialize error message
    let errorMessage = "";

    // Check if required fields are empty
    const requiredFields = [
      { name: "podName", value: podName },
      { name: "email", value: email },
      { name: "category", value: category }
    ];

    requiredFields.forEach((field) => {
      if (!field.value) {
        errorMessage += `Please fill in the ${field.name}.<br>`;
      }
    });

    // If there is any missing required field, show an alert
    if (errorMessage) {
      showAlert(errorMessage, "red");
      return;
    }

    // Collect social media values, ensuring empty strings are included but only if they are not empty
    const socialMedia = [
      document.getElementById("facebook")?.value.trim(),
      document.getElementById("instagram")?.value.trim(),
      document.getElementById("linkedin")?.value.trim(),
      document.getElementById("twitter")?.value.trim(),
      document.getElementById("tiktok")?.value.trim(),
      document.getElementById("pinterest")?.value.trim()
    ].filter((link) => link); // Remove empty strings

    // Collect URLs for optional fields, remove if empty
    const googleCal =
      document.getElementById("google-cal")?.value.trim() || null;
    const guestUrl =
      document.getElementById("guest-form-url")?.value.trim() || null;

    // Build the data object
    const data = {
      teamId: "",
      podName,
      ownerName: document.getElementById("pod-owner")?.value.trim() || "",
      hostName: document.getElementById("pod-host")?.value.trim() || "",
      rssFeed: document.getElementById("pod-rss")?.value.trim() || "",
      googleCal: googleCal,
      guestUrl: guestUrl,
      email,
      description: document.getElementById("description")?.value.trim() || "",
      logoUrl:
        "https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg",
      category,
      socialMedia
    };

    // Remove any keys with null or empty values
    Object.keys(data).forEach((key) => {
      if (
        data[key] === null ||
        (Array.isArray(data[key]) && data[key].length === 0) ||
        data[key] === ""
      ) {
        delete data[key];
      }
    });

    try {
      const responseData = await addPodcast(data);
      if (responseData.error) {
        showAlert(
          `Error: ${
            responseData.details
              ? JSON.stringify(responseData.details)
              : responseData.error
          }`,
          "red"
        );
      } else {
        showAlert("Podcast added successfully!", "green");
        setTimeout(
          () => (window.location.href = responseData.redirect_url),
          2500
        );
      }
    } catch (error) {
      console.error("Error:", error);
      showAlert("There was an error with the registration process.", "red");
    }
  });

  function showAlert(message, color) {
    const alertBox = document.getElementById("custom-alert");
    const alertMessage = document.getElementById("alert-message");

    alertMessage.innerHTML = message;
    alertBox.style.background = color;
    alertBox.style.display = "block";

    setTimeout(() => {
      alertBox.style.display = "none";
    }, 2500);
  }

  // CRUD operation buttons
  document
    .getElementById("fetch-podcasts-btn")
    .addEventListener("click", async () => {
      console.log("Fetch All Podcasts button clicked");
      try {
        const response = await fetchPodcasts();
        const podcasts = response.podcast;
        console.log("Fetched Podcasts:", podcasts);

        // Populate podcasts container
        const podcastsList = document.getElementById("podcasts-list");
        podcastsList.innerHTML = "";
        podcasts.forEach((podcast) => {
          const podcastItem = document.createElement("div");
          podcastItem.className = "podcast-item";
          podcastItem.innerHTML = `
            <span>${podcast.podName}</span>
            <input type="checkbox" id="podcast-${podcast._id}" value="${podcast._id}">
          `;
          podcastsList.appendChild(podcastItem);
        });

        // Show popup
        const popup = document.getElementById("podcasts-popup");
        popup.style.display = "flex";
      } catch (error) {
        showAlert("Failed to fetch podcasts.", "red");
      }
    });

  function displayPodcastDetails(podcast) {
    // Populate form with podcast details
    document.getElementById("pod-name").value = podcast.podName || "";
    document.getElementById("pod-owner").value = podcast.ownerName || "";
    document.getElementById("pod-host").value = podcast.hostName || "";
    document.getElementById("pod-rss").value = podcast.rssFeed || "";
    document.getElementById("google-cal").value = podcast.googleCal || "";
    document.getElementById("guest-form-url").value = podcast.guestUrl || "";
    document.getElementById("email").value = podcast.email || "";
    document.getElementById("description").value = podcast.description || "";
    document.getElementById("category").value = podcast.category || "";
    document.getElementById("facebook").value = podcast.socialMedia[0] || "";
    document.getElementById("instagram").value = podcast.socialMedia[1] || "";
    document.getElementById("linkedin").value = podcast.socialMedia[2] || "";
    document.getElementById("twitter").value = podcast.socialMedia[3] || "";
    document.getElementById("tiktok").value = podcast.socialMedia[4] || "";
    document.getElementById("pinterest").value = podcast.socialMedia[5] || "";

    // Show form container and hide podcasts container
    formContainer.style.display = "block";
    podcastsContainer.style.display = "none";

    // Hide popup
    const popup = document.getElementById("podcasts-popup");
    popup.style.display = "none";
  }

  document
    .getElementById("fetch-podcast-btn")
    .addEventListener("click", async () => {
      const podcastId = prompt("Enter Podcast ID:");
      if (podcastId) {
        try {
          const podcast = await fetchPodcast(podcastId);
          console.log("Fetched Podcast:", podcast);
          displayPodcastDetails(podcast.podcast);
        } catch (error) {
          showAlert("Failed to fetch podcast.", "red");
        }
      }
    });

  document
    .getElementById("update-podcast-btn")
    .addEventListener("click", async () => {
      const podcastId = prompt("Enter Podcast ID:");
      if (podcastId) {
        const updateData = prompt("Enter update data in JSON format:");
        if (updateData) {
          try {
            const updatedPodcast = await updatePodcast(
              podcastId,
              JSON.parse(updateData)
            );
            console.log("Updated Podcast:", updatedPodcast);
            showAlert("Updated podcast successfully!", "green");
          } catch (error) {
            showAlert("Failed to update podcast.", "red");
          }
        }
      }
    });

  document
    .getElementById("delete-podcast-btn")
    .addEventListener("click", async () => {
      const podcastId = prompt("Enter Podcast ID:");
      if (podcastId) {
        try {
          const deletedPodcast = await deletePodcast(podcastId);
          console.log("Deleted Podcast:", deletedPodcast);
          showAlert("Deleted podcast successfully!", "green");
        } catch (error) {
          showAlert("Failed to delete podcast.", "red");
        }
      }
    });

  // Close popup
  document.getElementById("close-popup-btn").addEventListener("click", () => {
    const popup = document.getElementById("podcasts-popup");
    popup.style.display = "none";
  });

  // Delete selected podcasts
  document
    .getElementById("delete-selected-podcasts-btn")
    .addEventListener("click", async () => {
      const selectedPodcasts = document.querySelectorAll(
        "#podcasts-list input[type='checkbox']:checked"
      );
      const podcastIds = Array.from(selectedPodcasts).map(
        (checkbox) => checkbox.value
      );

      try {
        for (const podcastId of podcastIds) {
          await deletePodcast(podcastId);
        }
        showAlert("Selected podcasts deleted successfully!", "green");
        document.getElementById("podcasts-popup").style.display = "none";
      } catch (error) {
        showAlert("Failed to delete selected podcasts.", "red");
      }
    });

  // Add HTML content dynamically
  const container = document.querySelector(".container");
  container.insertAdjacentHTML(
    "afterbegin",
    `
    <div class="crud-buttons">
      <button id="fetch-podcasts-btn" class="crud-btn">Fetch All Podcasts</button>
      <button id="fetch-podcast-btn" class="crud-btn">Fetch Podcast by ID</button>
      <button id="update-podcast-btn" class="crud-btn">Update Podcast</button>
      <button id="delete-podcast-btn" class="crud-btn">Delete Podcast</button>
    </div>
    <div class="form-box">
      <div class="form-fields">
        <form id="register-podcast-form">
          <!-- Pod Logo -->
          <div class="form-group">
            <label for="pod-logo">Pod Logo</label>
            <div
              style="display: flex; align-items: center; justify-content: center"
            >
              <img
                src="https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg"
                alt="Pod Logo"
                class="pod-logo pod-logo-inline"
              />
            </div>
          </div>

          <!-- Podcast Name -->
          <div class="field-group">
            <label for="pod-name">Podcast Name</label>
            <input type="text" id="pod-name" name="podName" autocomplete="off" />
          </div>

          <!-- RSS Feed -->
          <div class="field-group">
            <label for="pod-rss">RSS Feed</label>
            <input type="url" id="pod-rss" name="rssFeed" />
          </div>

          <!-- Podcast Owner -->
          <div class="field-group">
            <label for="pod-owner">Podcast Owner</label>
            <input type="text" id="pod-owner" name="ownerName" />
          </div>

          <!-- Host Name -->
          <div class="field-group">
            <label for="pod-host">Host(s) Name(s)</label>
            <input type="text" id="pod-host" name="hostName" />
          </div>

          <!-- Description -->
          <div class="field-group">
            <label for="description">Podcast Description</label>
            <textarea id="description" name="description"></textarea>
          </div>

          <!-- Category -->
          <div class="field-group">
            <label for="category">Category (Required)</label>
            <input type="text" id="category" name="category" required />
          </div>

          <!-- Email Address -->
          <div class="field-group">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" />
          </div>

          <!-- Google Calendar Integration -->
          <div class="field-group">
            <label>Google Calendar Integration</label>
            <button type="button" class="connect-btn">CONNECT</button>
          </div>

          <!-- Google Calendar Link -->
          <div class="field-group">
            <label>Google Calendar Pick a Date URL</label>
            <div class="inline-field">
              <span>podmanager.com/?pod=TheAuthorityShow</span>
            </div>
          </div>

          <!-- Guest Form URL -->
          <div class="field-group">
            <label for="guest-form-url">Guest Form URL</label>
            <input type="url" id="guest-form-url" name="guestUrl" />
          </div>

          <!-- Social Media Links -->
          <div class="field-group">
            <label for="facebook">Facebook</label>
            <input type="url" id="facebook" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="instagram">Instagram</label>
            <input type="url" id="instagram" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="linkedin">LinkedIn</label>
            <input type="url" id="linkedin" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="twitter">Twitter</label>
            <input type="url" id="twitter" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="tiktok">TikTok</label>
            <input type="url" id="tiktok" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="pinterest">Pinterest</label>
            <input type="url" id="pinterest" name="socialMedia[]" />
          </div>

          <button type="submit" class="invite-btn">SAVE</button>
        </form>
      </div>
    </div>
    `
  );
});
