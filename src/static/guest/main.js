document.addEventListener("DOMContentLoaded", function() {
  // ---------------------------
  // Utility Functions
  // ---------------------------
  // Fallback localStorage functions if needed
  function loadGuestsFromLocalStorage() {
    const stored = localStorage.getItem("guests");
    if (stored) {
      return JSON.parse(stored);
    } else {
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
          status: "scheduled",
          scheduled: 0,
          completed: 0,
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
          status: "scheduled",
          scheduled: 0,
          completed: 0,
          profileLink: "profile.html?id=sardor"
        }
      ];
      localStorage.setItem("guests", JSON.stringify(initialGuests));
      return initialGuests;
    }
  }

  function openPopup() {
    const popup = document.getElementById("popup");
    popup.style.display = "flex";
    popup.classList.remove("hidden");
  }

  function closePopup() {
    const popup = document.getElementById("popup");
    popup.style.display = "none";
    popup.classList.add("hidden");
    document.getElementById("popup-form").innerHTML = "";
    document.getElementById("popup-body").innerHTML = "";
  }

  const closeButton = document.querySelector(".close-button");
  if (closeButton) {
    closeButton.addEventListener("click", closePopup);
  }

  // ---------------------------
  // Dynamic Guest Profile Popup
  // ---------------------------
  function openProfilePopup(guest) {
    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupBody = document.getElementById("popup-body");

    popupTitle.textContent = guest.name + "'s Profile";
    popupBody.innerHTML = `
      <div style="text-align:center;">
        <img src="${guest.image}" alt="${guest.name}" style="width:100px;height:100px;border-radius:50%;">
        <h2>${guest.name}</h2>
        <p>${guest.bio}</p>
        <div>
          ${guest.tags.map(tag => `<span style="margin:2px;padding:4px;background:#007BFF;color:#fff;border-radius:4px;">${tag}</span>`).join(" ")}
        </div>
        <p>Email: <a href="mailto:${guest.email}">${guest.email}</a></p>
        <p>LinkedIn: <a href="${guest.linkedin}" target="_blank">${guest.linkedin}</a></p>
        <p>Twitter: <a href="${guest.twitter}" target="_blank">${guest.twitter}</a></p>
        <p>Areas of Interest: ${guest.areasOfInterest.join(", ")}</p>
        <p>Status: ${guest.status}</p>
        <p>Scheduled: ${guest.scheduled} | Completed: ${guest.completed}</p>
      </div>
      <button id="close-profile-popup" style="margin-top:10px;">Close</button>
    `;
    openPopup();
    document.getElementById("close-profile-popup").addEventListener("click", closePopup);
  }

  // ---------------------------
  // Add Guest Popup & Submission
  // ---------------------------
  function openAddGuestPopup() {
    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupForm = document.getElementById("popup-form");
    const popupBody = document.getElementById("popup-body");

    popupTitle.textContent = "Add Guest";
    popupForm.innerHTML = "";
    popupBody.innerHTML = "";
    openPopup();

    const formHtml = `
      <div id="popup-profile-pic" class="profile-pic-uploader" style="cursor:pointer;text-align:center;padding:10px;border:1px dashed #ccc;">
        Upload
      </div>
      <input type="file" id="popup-profile-pic-input" accept="image/*" style="display:none;">
      <label>Guest Name:</label>
      <input type="text" id="guest-name-input">
      <label>Guest Description:</label>
      <input type="text" id="guest-description-input">
      <label>Tags (comma separated):</label>
      <input type="text" id="guest-tags-input">
      <label>Areas of Interest (comma separated):</label>
      <input type="text" id="guest-areas-input">
      <label>Email:</label>
      <input type="email" id="guest-email-input">
      <label>LinkedIn:</label>
      <input type="text" id="guest-linkedin-input">
      <label>Twitter:</label>
      <input type="text" id="guest-twitter-input">
      <button type="submit">Add Guest</button>
    `;
    popupForm.innerHTML = formHtml;

    const picUploader = document.getElementById("popup-profile-pic");
    const picInput = document.getElementById("popup-profile-pic-input");
    picUploader.addEventListener("click", function() {
      picInput.click();
    });
    picInput.addEventListener("change", function() {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          picUploader.style.backgroundImage = `url(${e.target.result})`;
          picUploader.style.backgroundSize = "cover";
          picUploader.textContent = "";
        };
        reader.readAsDataURL(file);
      }
    });

    popupForm.onsubmit = function(e) {
      e.preventDefault();
      const name = document.getElementById("guest-name-input").value;
      const description = document.getElementById("guest-description-input").value;
      const tags = document.getElementById("guest-tags-input").value.split(",").map(tag => tag.trim()).filter(Boolean);
      const areasText = document.getElementById("guest-areas-input").value;
      const areasOfInterest = areasText ? areasText.split(",").map(s => s.trim()).filter(Boolean) : [];
      const email = document.getElementById("guest-email-input").value;
      const linkedin = document.getElementById("guest-linkedin-input").value;
      const twitter = document.getElementById("guest-twitter-input").value;

      let image;
      if (picUploader && picUploader.style.backgroundImage) {
        image = picUploader.style.backgroundImage.slice(5, -2);
      } else {
        image = "default-profile.png";
      }

      const payload = {
        name: name,
        image: image,
        tags: tags,
        description: description,
        bio: description,
        areasOfInterest: areasOfInterest,
        email: email,
        linkedin: linkedin,
        twitter: twitter
      };

      fetch("/guest/add_guest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
      .then(response => response.json())
      .then(data => {
        if (data.guest_id) {
          alert("Guest added successfully");
          renderGuestList();
        } else {
          alert("Error adding guest: " + data.error);
        }
        closePopup();
      })
      .catch(err => {
        console.error(err);
        alert("Error adding guest");
        closePopup();
      });
    }
  }

  // ---------------------------
  // Fetch Guests from Server
  // ---------------------------
  function fetchGuestsFromServer() {
    return fetch("/guest/get_guests")
      .then(response => response.json())
      .then(data => {
        if (data.guests) {
          return data.guests;
        }
        return [];
      })
      .catch(err => {
        console.error(err);
        // Fallback to localStorage if server fails
        return loadGuestsFromLocalStorage();
      });
  }

  // ---------------------------
  // Render Guest List
  // ---------------------------
  function renderGuestList(filterText = "") {
    const guestListEl = document.getElementById("guest-list");
    if (!guestListEl) return;
    guestListEl.innerHTML = "";
    fetchGuestsFromServer().then(guests => {
      const searchTerms = filterText.split(",").map(term => term.trim().toLowerCase()).filter(Boolean);
      guests.filter(guest => {
        const combinedText = (guest.name + " " + guest.description + " " + guest.tags.join(" ") + " " + (guest.areasOfInterest ? guest.areasOfInterest.join(" ") : "")).toLowerCase();
        if (searchTerms.length === 0) return true;
        return searchTerms.every(term => combinedText.includes(term));
      }).forEach(guest => {
        const card = document.createElement("div");
        card.classList.add("guest-card");
        card.innerHTML = `
          <img src="${guest.image}" alt="${guest.name}">
          <h3>${guest.name}</h3>
          <div class="tags">
            ${guest.tags.map(tag => `<span>${tag}</span>`).join("")}
          </div>
        `;
        card.addEventListener("click", function() {
          openProfilePopup(guest);
        });
        guestListEl.appendChild(card);
      });

      // Add card to trigger Add Guest popup.
      const addCard = document.createElement("div");
      addCard.classList.add("guest-card", "add-guest-card");
      addCard.innerHTML = `
        <div style="font-size:48px; color:var(--accent-color);">+</div>
        <h3>Add Guest</h3>
      `;
      addCard.addEventListener("click", openAddGuestPopup);
      guestListEl.appendChild(addCard);
    });
  }

  const searchBar = document.getElementById("search-bar");
  if (searchBar) {
    searchBar.addEventListener("input", function(e) {
      renderGuestList(e.target.value);
    });
  }
  renderGuestList();
});
