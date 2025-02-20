document.addEventListener("DOMContentLoaded", function () {
  // ---------------------------
  // Utility Functions
  // ---------------------------

  function loadGuests() {

    const stored = localStorage.getItem("guests");

    if (stored) {

      return JSON.parse(stored);

    } else {

      // Initial array without engagement, pending, or social media fields.

      const initialGuests = [

        {
          id: "jonathan",
          name: "Jonathan Nizol",
          image: "guest1.jpg",
          tags: ["Male Health", "Mental Health", "Fitness", "Sports"],
          description: "A brief description for listing purposes.",
          bio: "I have over 10 years of experience in health and fitness...",
          email: "jonathan@example.com",
          linkedin: "https://linkedin.com/in/jonathan",
          twitter: "https://twitter.com/jonathan",
          areasOfInterest: ["Fitness", "Health"],
          inCalendar: true,  // guest is in the user's calendar
          scheduled: "5",
          completed: "10",
          profileLink: "profile.html?id=jonathan"
        },

        {
          id: "sardor",
          name: "Sardor Akhmedov",
          image: "guest2.jpg",
          tags: ["Business", "Entrepreneurship", "AI", "Technology"],
          description: "A brief description for listing purposes.",
          bio: "I am an entrepreneur and AI strategist...",
          email: "sardor@example.com",
          linkedin: "https://linkedin.com/in/sardor",
          twitter: "https://twitter.com/sardor",
          areasOfInterest: ["Business", "Technology", "AI"],
          inCalendar: false, // guest is not in the user's calendar
          scheduled: "0",
          completed: "0",
          profileLink: "profile.html?id=sardor"
        }

      ];

      localStorage.setItem("guests", JSON.stringify(initialGuests));

      return initialGuests;

    }
  }

  function saveGuests(guests) {

    localStorage.setItem("guests", JSON.stringify(guests));

  }

  function generateId() {

    return '_' + Math.random().toString(36).substr(2, 9);

  }

  // ---------------------------
  // Popup Functionality
  // ---------------------------
  function openPopup(title, fields, callback) {

    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupForm = document.getElementById("popup-form");

    popupTitle.textContent = title;
    popupForm.innerHTML = "";
    popup.style.display = "block";
    popup.classList.remove("hidden");

    fields.forEach(field => {

      const label = document.createElement("label");
      label.textContent = field.label;

      const input = document.createElement("input");
      input.type = field.type;
      input.id = field.id;

      if (field.value) {

        input.value = field.value;

      }

      popupForm.appendChild(label);
      popupForm.appendChild(input);

    });

    const submitButton = document.createElement("button");

    submitButton.textContent = "Submit";
    submitButton.type = "button";
    submitButton.addEventListener("click", function (e) {

      e.preventDefault();
      callback();
      closePopup();

    });

    popupForm.appendChild(submitButton);

  }

  // Custom Add Guest Popup with Profile Pic Uploader (Index Page)
  function openAddGuestPopup() {

    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupForm = document.getElementById("popup-form");

    popupTitle.textContent = "Add Guest";
    popupForm.innerHTML = "";
    popup.style.display = "flex";
    popup.classList.remove("hidden");

    // Profile Pic Uploader
    const picUploader = document.createElement("div");

    picUploader.id = "popup-profile-pic";
    picUploader.className = "profile-pic-uploader";
    picUploader.textContent = "Upload";

    const picInput = document.createElement("input");

    picInput.type = "file";
    picInput.accept = "image/*";
    picInput.id = "popup-profile-pic-input";
    picInput.style.display = "none";

    picUploader.addEventListener("click", function () {

      picInput.click();

    });

    picInput.addEventListener("change", function () {

      const file = this.files[0];

      if (file) {

        const reader = new FileReader();

        reader.onload = function (e) {

          picUploader.style.backgroundImage = `url(${e.target.result})`;
          picUploader.style.backgroundSize = "cover";
          picUploader.textContent = "";

        };

        reader.readAsDataURL(file);

      }

    });
    popupForm.appendChild(picUploader);
    popupForm.appendChild(picInput);

    // Additional fields
    const fields = [

      { label: "Guest Name:", type: "text", id: "guest-name-input" },
      { label: "Guest Description:", type: "text", id: "guest-description-input" },
      { label: "Tags (comma separated):", type: "text", id: "guest-tags-input" },
      { label: "Areas of Interest (comma separated):", type: "text", id: "guest-areas-input" },
      { label: "Email:", type: "email", id: "guest-email-input" },
      { label: "LinkedIn:", type: "text", id: "guest-linkedin-input" },
      { label: "Twitter:", type: "text", id: "guest-twitter-input" }

    ];

    fields.forEach(field => {

      const label = document.createElement("label");
      label.textContent = field.label;
      const input = document.createElement("input");
      input.type = field.type;
      input.id = field.id;
      popupForm.appendChild(label);
      popupForm.appendChild(input);

    });

    const submitButton = document.createElement("button");
    submitButton.type = "submit";
    submitButton.textContent = "Add Guest";
    popupForm.appendChild(submitButton);

  }

  function closePopup() {

    const popup = document.getElementById("popup");
    popup.style.display = "none";
    popup.classList.add("hidden");
    const popupForm = document.getElementById("popup-form");

    if (popupForm.reset) popupForm.reset();

  }

  const closeButton = document.querySelector(".close-button");

  if (closeButton) {

    closeButton.addEventListener("click", closePopup);

  }

  // ---------------------------
  // INDEX PAGE CODE
  // ---------------------------
  const guestListEl = document.getElementById("guest-list");

  if (guestListEl) {

    function renderGuestList(filterText = "") {

      const guests = loadGuests();
      guestListEl.innerHTML = "";

      // Split search input by commas for multi-tag search
      const searchTerms = filterText
        .split(",")
        .map(term => term.trim().toLowerCase())
        .filter(Boolean);

      guests
        .filter(guest => {

          // Combine guest fields into one searchable string
          const combinedText = (

            guest.name + " " +
            guest.description + " " +
            guest.tags.join(" ") + " " +
            (guest.areasOfInterest ? guest.areasOfInterest.join(" ") : "")

          ).toLowerCase();

          if (searchTerms.length === 0) return true;

          // All search terms must appear (AND logic)
          return searchTerms.every(term => combinedText.includes(term));

        })
        .forEach(guest => {

          const card = document.createElement("div");
          card.classList.add("guest-card");
          card.innerHTML = `
            <img src="${guest.image}" alt="${guest.name}" />
            <h3>${guest.name}</h3>
            <div class="tags">
              ${guest.tags.map(tag => `<span>${tag}</span>`).join("")}
            </div>
            <div class="guest-hover">
              <p>${guest.description}</p>
              <a href="profile.html?id=${guest.id}" class="view-profile">View Profile</a>
            </div>
          `;
          guestListEl.appendChild(card);

        });

      const addCard = document.createElement("div");
      addCard.classList.add("guest-card", "add-guest-card");
      addCard.innerHTML = `
        <div style="font-size:48px; color:var(--accent-color);">+</div>
        <h3>Add Guest</h3>
      `;
      addCard.addEventListener("click", openAddGuestPopup);
      guestListEl.appendChild(addCard);

    }

    const searchBar = document.getElementById("search-bar");

    if (searchBar) {

      searchBar.addEventListener("input", (e) => {

        renderGuestList(e.target.value);

      });

    }

    renderGuestList();

    const popupFormEl = document.getElementById("popup-form");

    if (popupFormEl) {

      popupFormEl.addEventListener("submit", function (e) {

        e.preventDefault();
        const name = document.getElementById("guest-name-input").value;
        const description = document.getElementById("guest-description-input").value;
        const tags = document.getElementById("guest-tags-input").value
          .split(",")
          .map(tag => tag.trim())
          .filter(Boolean);
        const areasText = document.getElementById("guest-areas-input").value;
        const areasOfInterest = areasText
          ? areasText.split(",").map(s => s.trim()).filter(Boolean)
          : [];
        const email = document.getElementById("guest-email-input").value;
        const linkedin = document.getElementById("guest-linkedin-input").value;
        const twitter = document.getElementById("guest-twitter-input").value;

        const picUploader = document.getElementById("popup-profile-pic");
        let image;

        if (picUploader && picUploader.style.backgroundImage) {

          image = picUploader.style.backgroundImage.slice(5, -2);

        } else {

          image = "default-profile.png";

        }

        const id = generateId();
        const profileLink = `profile.html?id=${id}`;
        const guests = loadGuests();

        // Default status is now "scheduled" with zeroed calendar counts.
        guests.push({

          id,
          name,
          image,
          tags,
          description,
          areasOfInterest,
          email,
          linkedin,
          twitter,
          profileLink,
          status: "scheduled",
          scheduled: "0",
          completed: "0",
          bio: description

        });
        saveGuests(guests);
        renderGuestList(document.getElementById("search-bar").value);
        popupFormEl.reset();

        if (picUploader) {

          picUploader.style.backgroundImage = "";
          picUploader.textContent = "Upload";

        }

        closePopup();

      });
    }
  }

  // ---------------------------
  // PROFILE PAGE CODE
  // ---------------------------
  const profileEl = document.getElementById("profile");

  if (profileEl) {

    const urlParams = new URLSearchParams(window.location.search);
    const guestId = urlParams.get("id");
    const guests = loadGuests();
    const data = guests.find(g => g.id === guestId) || {

      name: "Default Guest",
      bio: "No bio available.",
      image: "default-profile.png",
      tags: [],
      areasOfInterest: [],
      email: "guest@example.com",
      linkedin: "#",
      twitter: "#",
      status: "scheduled",
      scheduled: "0",
      completed: "0",
      profileLink: "profile.html?id=default"

    };

    // Immediately hide engagement section if guest not in calendar
    if (!data.inCalendar) {

      const engagementSection = document.querySelector(".engagement");
      if (engagementSection) {
        engagementSection.style.display = "none";

      }

    }

    document.getElementById("guest-name").textContent = data.name;
    document.getElementById("guest-bio").textContent = data.description;
    document.getElementById("profile-pic").src = data.image;
    document.getElementById("guest-email").innerHTML = `Email: <a href="mailto:${data.email}" id="email-link">${data.email}</a>`;
    document.getElementById("linkedin-link").href = data.linkedin;
    document.getElementById("twitter-link").href = data.twitter;

    const tagsContainer = document.getElementById("guest-tags");
    tagsContainer.innerHTML = "";
    data.tags.forEach(tag => {

      const span = document.createElement("span");
      span.textContent = tag;
      tagsContainer.appendChild(span);

    });

    let areasContainer = document.getElementById("areas-of-interest");
    if (areasContainer) {

      const areas = data.areasOfInterest || [];
      areasContainer.textContent = areas.length ? "Areas of Interest: " + areas.join(", ") : "";

    }

    // Bio Section with inline editing
    const bioTextElement = document.getElementById("guest-bio-text");
    bioTextElement.textContent = data.bio || "No bio available.";
    const editBioIcon = document.getElementById("edit-bio-icon");

    if (editBioIcon) {

      editBioIcon.addEventListener("click", function () {
        bioTextElement.contentEditable = true;
        bioTextElement.style.border = "1px dashed #ccc";
        bioTextElement.focus();

      });

      bioTextElement.addEventListener("blur", function () {

        bioTextElement.contentEditable = false;
        bioTextElement.style.border = "none";
        const updatedBio = bioTextElement.textContent;
        const guests = loadGuests();
        const updatedGuests = guests.map(g => {

          if (g.id === data.id) {

            return { ...g, bio: updatedBio };

          }

          return g;

        });

        saveGuests(updatedGuests);

      });
    }

    // Communication Status Badge (using a safe fallback)
    const statusBadge = document.getElementById("status-badge");
    let status = data.status;

    if (status === "pending") { // default pending to scheduled

      status = "scheduled";

    }

    const statusSelectEl = document.getElementById("edit-guest-status");
    const updatedStatus = statusSelectEl && statusSelectEl.value ? statusSelectEl.value : "scheduled";
    statusBadge.textContent = updatedStatus.charAt(0).toUpperCase() + updatedStatus.slice(1);

    // Profile Actions
    const editProfileBtn = document.getElementById("edit-profile-btn");
    const removeProfileBtn = document.getElementById("remove-profile-btn");

    if (editProfileBtn) {

      editProfileBtn.addEventListener("click", openEditProfilePopup);

    }
    if (removeProfileBtn) {

      removeProfileBtn.addEventListener("click", function () {

        if (confirm("Are you sure you want to remove your profile?")) {

          const guests = loadGuests();
          const updatedGuests = guests.filter(g => g.id !== data.id);
          saveGuests(updatedGuests);
          window.location.href = "index.html";

        }

      });
    }

    function openEditProfilePopup() {

      const popup = document.getElementById("popup");
      const popupTitle = document.getElementById("popup-title");
      const popupForm = document.getElementById("popup-form");
      popupTitle.textContent = "Edit Profile";
      popupForm.innerHTML = "";
      popup.style.display = "flex";
      popup.classList.remove("hidden");

      // Profile Pic Uploader for Editing
      const picUploader = document.createElement("div");
      picUploader.id = "popup-edit-profile-pic";
      picUploader.className = "profile-pic-uploader";
      picUploader.style.backgroundImage = `url(${data.image})`;
      picUploader.textContent = "";

      const picInput = document.createElement("input");
      picInput.type = "file";
      picInput.accept = "image/*";
      picInput.id = "popup-edit-profile-pic-input";
      picInput.style.display = "none";

      picUploader.addEventListener("click", function () {

        picInput.click();

      });

      picInput.addEventListener("change", function () {

        const file = this.files[0];

        if (file) {

          const reader = new FileReader();
          reader.onload = function (e) {

            picUploader.style.backgroundImage = `url(${e.target.result})`;

          };

          reader.readAsDataURL(file);

        }
      });

      popupForm.appendChild(picUploader);
      popupForm.appendChild(picInput);

      // Add the remaining editable fields only.
      const fields = [

        { label: "Guest Name:", type: "text", id: "edit-guest-name", value: data.name },
        { label: "Guest Description:", type: "text", id: "edit-guest-description", value: data.description },
        { label: "Tags (comma separated):", type: "text", id: "edit-guest-tags", value: data.tags.join(", ") },
        { label: "Areas of Interest (comma separated):", type: "text", id: "edit-guest-areas", value: data.areasOfInterest ? data.areasOfInterest.join(", ") : "" },
        { label: "Email:", type: "email", id: "edit-guest-email", value: data.email },
        { label: "LinkedIn:", type: "text", id: "edit-guest-linkedin", value: data.linkedin },
        { label: "Twitter:", type: "text", id: "edit-guest-twitter", value: data.twitter }

      ];

      fields.forEach(field => {

        const label = document.createElement("label");
        label.textContent = field.label;
        const input = document.createElement("input");
        input.type = field.type;
        input.id = field.id;
        input.value = field.value;
        popupForm.appendChild(label);
        popupForm.appendChild(input);

      });

      // Do NOT add the schedule/completed select since these values are managed via calendar integration.
      const submitButton = document.createElement("button");
      submitButton.type = "submit";
      submitButton.textContent = "Save Changes";
      popupForm.appendChild(submitButton);

      popupForm.onsubmit = function (e) {

        e.preventDefault();
        const updatedName = document.getElementById("edit-guest-name").value;
        const updatedDescription = document.getElementById("edit-guest-description").value;
        const updatedTags = document.getElementById("edit-guest-tags").value
          .split(",")
          .map(t => t.trim())
          .filter(Boolean);

        const updatedAreasText = document.getElementById("edit-guest-areas").value;
        const updatedAreas = updatedAreasText
          ? updatedAreasText.split(",").map(s => s.trim()).filter(Boolean)
          : [];

        const updatedEmail = document.getElementById("edit-guest-email").value;
        const updatedLinkedin = document.getElementById("edit-guest-linkedin").value;
        const updatedTwitter = document.getElementById("edit-guest-twitter").value;
        let updatedImage;

        if (picUploader && picUploader.style.backgroundImage) {

          updatedImage = picUploader.style.backgroundImage.slice(5, -2);

        } else {

          updatedImage = data.image;

        }

        const guests = loadGuests();
        const updatedGuests = guests.map(g => {

          if (g.id === data.id) {

            return {

              ...g,
              name: updatedName,
              description: updatedDescription,
              tags: updatedTags,
              areasOfInterest: updatedAreas,
              image: updatedImage,
              email: updatedEmail,
              linkedin: updatedLinkedin,
              twitter: updatedTwitter,
              // Do not change schedule/completed values here.
              profileLink: `profile.html?id=${g.id}`,
              bio: updatedDescription

            };

          }

          return g;
        });

        saveGuests(updatedGuests);

        // Update displayed fields on the profile page.
        document.getElementById("guest-name").textContent = updatedName;
        document.getElementById("guest-bio").textContent = updatedDescription;
        document.getElementById("profile-pic").src = updatedImage;
        document.getElementById("guest-email").innerHTML = `Email: <a href="mailto:${updatedEmail}" id="email-link">${updatedEmail}</a>`;
        document.getElementById("linkedin-link").href = updatedLinkedin;
        document.getElementById("twitter-link").href = updatedTwitter;

        const tagsContainer = document.getElementById("guest-tags");
        tagsContainer.innerHTML = "";
        updatedTags.forEach(tag => {

          const span = document.createElement("span");
          span.textContent = tag;
          tagsContainer.appendChild(span);

        });

        let areasContainer = document.getElementById("areas-of-interest");
        if (areasContainer) {

          areasContainer.textContent = updatedAreas.length ? "Areas of Interest: " + updatedAreas.join(", ") : "";

        }
        closePopup();

      }

    }

    // ---------------------------
    // Azure Calendar Placeholder
    // ---------------------------
    function updateCalendarMetrics() {

      // Placeholder: simulate fetching scheduled & completed counts from Azure Calendar.
      const scheduledCount = Math.floor(Math.random() * 10) + 1;
      const completedCount = Math.floor(Math.random() * 10);
      const scheduledEl = document.getElementById("scheduled-count");
      const completedEl = document.getElementById("completed-count");
      if (scheduledEl) scheduledEl.textContent = scheduledCount;
      if (completedEl) completedEl.textContent = completedCount;

    }

    // Initial call and periodic update (every 60 seconds)
    updateCalendarMetrics();
    setInterval(updateCalendarMetrics, 60000);
  }

  // ---------------------------
  // Additional Common Event Listeners
  // ---------------------------
  const exportDataEl = document.getElementById("export-data");

  if (exportDataEl) {

    exportDataEl.addEventListener("click", function () {

      alert("Exporting data...");

    });

  }

  const trackEngagementEl = document.getElementById("track-engagement");

  if (trackEngagementEl) {

    trackEngagementEl.addEventListener("click", function () {

      alert("Tracking engagement metrics...");

    });

  }

  async function sendEmail(to, subject, body) {

    await fetch("https://api.sendgrid.com/v3/mail/send", {

      method: "POST",
      headers: {

        "Authorization": "Bearer YOUR_SENDGRID_API_KEY",
        "Content-Type": "application/json"

      },

      body: JSON.stringify({

        personalizations: [{ to: [{ email: to }] }],
        from: { email: "your@email.com" },
        subject: subject,
        content: [{ type: "text/plain", value: body }]

      })

    });

    const openRate = Math.floor(Math.random() * 100) + "%";
    emailHistory.push({ to, subject, body, date: new Date(), openRate });

  }

  const viewEmailHistoryEl = document.getElementById("view-email-history");

  if (viewEmailHistoryEl) {

    viewEmailHistoryEl.addEventListener("click", function () {

      if (emailHistory.length === 0) {

        alert("No emails sent yet.");

      } else {

        let historyText = emailHistory
          .map(email => `${email.date.toLocaleString()}: To ${email.to} – ${email.subject} (Open Rate: ${email.openRate})`)
          .join("\n");
        alert(historyText);

      }

    });

  }

});
