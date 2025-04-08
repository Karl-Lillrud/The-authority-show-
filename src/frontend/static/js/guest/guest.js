import {
  addGuestRequest,
  editGuestRequest,
  deleteGuestRequest,
  fetchGuestsRequest,
} from "/static/requests/guestRequests.js";

document.addEventListener("DOMContentLoaded", function() {
  // Utility Functions
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

  // Dynamic Guest Profile Popup
  function openProfilePopup(guest) {
    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupBody = document.getElementById("popup-body");

    popupTitle.textContent = guest.name + "'s Profile";
    popupBody.innerHTML = `
      <div style="text-align:center;">
        <img src="${guest.image}" alt="${guest.name}" style="width:100px; height:100px; border-radius:50%; display:block; margin: 0 auto;">
        <p>${guest.bio}</p>
        <div>
          ${guest.tags.map(tag => `<span style="margin:2px;padding:4px;background:#007BFF;color:#fff;border-radius:4px;">${tag}</span>`).join(" ")}
        </div>
        <p>Email: <a href="mailto:${guest.email}">${guest.email}</a></p>
        <p>LinkedIn: <a href="${guest.linkedin}" target="_blank">${guest.linkedin}</a></p>
        <p>Twitter: <a href="${guest.twitter}" target="_blank">${guest.twitter}</a></p>
        <p>Areas of Interest: ${guest.areasOfInterest.join(", ")}</p>
      </div>
      <div class="popup-actions">
        <button id="edit-guest">Edit</button>
        <button id="delete-guest" class="delete">Delete</button>
      </div>
    `;
    openPopup();

    document.getElementById("edit-guest").addEventListener("click", function(e) {
      e.stopPropagation();
      closePopup();
      openEditGuestPopup(guest);
    });

    document.getElementById("delete-guest").addEventListener("click", function(e) {
      e.stopPropagation();
      // Call deleteGuestRequest from guestRequests.js
      deleteGuestRequest(guest.id)
        .then(data => {
          if (data.message) {
            alert("Guest deleted successfully");
            renderGuestList();
          } else {
            alert("Error deleting guest: " + data.error);
          }
          closePopup();
        })
        .catch(err => {
          console.error(err);
          alert("Error deleting guest");
          closePopup();
        });
    });
  }

  // Add Guest Popup & Submission
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
      <div id="popup-profile-pic" class="profile-pic-uploader" style="cursor:pointer; display:flex; align-items:center; justify-content:center; text-align:center; padding:10px; border:1px dashed #ccc; width:120px; height:120px; margin: 0 auto; border-radius:50%;">
        Upload
      </div>
      <input type="file" id="popup-profile-pic-input" accept="image/*" style="display:none;">
      <label>Podcast ID:</label>
      <input type="text" id="guest-podcastid-input">
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

    popupForm.onsubmit = async function (e) {
      e.preventDefault();
      const name = document.getElementById("guest-name-input").value.trim();
      const email = document.getElementById("guest-email-input").value.trim();
      const description = document.getElementById("guest-description-input").value.trim();
      const tags = document.getElementById("guest-tags-input").value.split(",").map(tag => tag.trim()).filter(Boolean);
      const areasOfInterest = document.getElementById("guest-areas-input").value.split(",").map(area => area.trim()).filter(Boolean);

      if (!name || !email) {
        alert("Name and Email are required fields.");
        return;
      }

      const payload = {
        name,
        email,
        description,
        tags,
        areasOfInterest,
        googleCal: sessionStorage.getItem("googleCal") || "", // Include googleCal token if available
      };

      try {
        const response = await fetch("/add_guest", { // Corrected endpoint
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Failed to add guest: ${response.statusText}`);
        }

        const result = await response.json();
        alert(result.message);
        renderGuestList();
        closePopup();
      } catch (error) {
        console.error("Error adding guest:", error);
        alert("An error occurred while adding the guest.");
      }
    };
  }

  // Edit Guest Popup & Submission
  function openEditGuestPopup(guest) {
    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupForm = document.getElementById("popup-form");
    const popupBody = document.getElementById("popup-body");

    popupTitle.textContent = "Edit Guest";
    popupForm.innerHTML = "";
    popupBody.innerHTML = "";
    openPopup();

    const formHtml = `
      <div id="popup-profile-pic" class="profile-pic-uploader" style="cursor:pointer; display:flex; align-items:center; justify-content:center; text-align:center; padding:10px; border:1px dashed #ccc; width:120px; height:120px; margin: 0 auto; border-radius:50%;">
        ${guest.image ? `<img src="${guest.image}" alt="${guest.name}" style="width:100%; height:100%; border-radius:50%;">` : "Upload"}
      </div>
      <input type="file" id="popup-profile-pic-input" accept="image/*" style="display:none;">
      <label>Guest Name:</label>
      <input type="text" id="guest-name-input" value="${guest.name}">
      <label>Guest Description:</label>
      <input type="text" id="guest-description-input" value="${guest.description || guest.bio}">
      <label>Tags (comma separated):</label>
      <input type="text" id="guest-tags-input" value="${guest.tags.join(", ")}">
      <label>Areas of Interest (comma separated):</label>
      <input type="text" id="guest-areas-input" value="${guest.areasOfInterest.join(", ")}">
      <label>Email:</label>
      <input type="email" id="guest-email-input" value="${guest.email}">
      <label>LinkedIn:</label>
      <input type="text" id="guest-linkedin-input" value="${guest.linkedin}">
      <label>Twitter:</label>
      <input type="text" id="guest-twitter-input" value="${guest.twitter}">
      <button type="submit">Update Guest</button>
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
          picUploader.innerHTML = `<img src="${e.target.result}" alt="${guest.name}" style="width:100%; height:100%; border-radius:50%;">`;
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
      const imgEl = picUploader.querySelector("img");
      if (imgEl) {
        image = imgEl.src;
      } else {
        image = guest.image || "default-profile.png";
      }

      const payload = {
        id: guest.id,
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

      // Call editGuestRequest from guestRequests.js
      editGuestRequest(guest.id, payload)
        .then(data => {
          if (data.message) {
            alert("Guest updated successfully");
            renderGuestList();
          } else {
            alert("Error updating guest: " + data.error);
          }
          closePopup();
        })
        .catch(err => {
          console.error(err);
          alert("Error updating guest");
          closePopup();
        });
    }
  }

  // Render Guest List
  function renderGuestList(filterText = "") {
    const guestListEl = document.getElementById("guest-list");
    if (!guestListEl) return;
    guestListEl.innerHTML = "";
    // Call fetchGuestsRequest from guestRequests.js
    fetchGuestsRequest().then(guests => {
      const searchTerms = filterText.split(",").map(term => term.trim().toLowerCase()).filter(Boolean);
      guests.filter(guest => {
        const combinedText = (guest.name + " " + guest.description + " " + guest.tags.join(" ") + " " + (guest.areasOfInterest ? guest.areasOfInterest.join(" ") : "")).toLowerCase();
        return searchTerms.length === 0 || searchTerms.every(term => combinedText.includes(term));
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