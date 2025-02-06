document.addEventListener("DOMContentLoaded", function() {
    const popup = document.getElementById("popup");
    const popupTitle = document.getElementById("popup-title");
    const popupForm = document.getElementById("popup-form");
    const closeButton = document.querySelector(".close-button");

    function openPopup(title, fields, callback) {
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
            popupForm.appendChild(label);
            popupForm.appendChild(input);
        });

        const submitButton = document.createElement("button");
        submitButton.textContent = "Submit";
        submitButton.type = "button";
        submitButton.addEventListener("click", function(e) {
            e.preventDefault();
            callback();
            popup.style.display = "none";
            popup.classList.add("hidden");
        });
        popupForm.appendChild(submitButton);
    }

    closeButton.addEventListener("click", function() {
        popup.style.display = "none";
        popup.classList.add("hidden");
    });

    document.getElementById("add-guest").addEventListener("click", function() {
        openPopup("Add Guest", [
            { label: "Guest Name:", type: "text", id: "guest-name-input" },
            { label: "Guest Bio:", type: "text", id: "guest-bio-input" },
            { label: "Email:", type: "email", id: "guest-email-input" },
            { label: "LinkedIn:", type: "text", id: "guest-linkedin-input" },
            { label: "Twitter:", type: "text", id: "guest-twitter-input" }
        ], function() {
            document.getElementById("guest-name").textContent = document.getElementById("guest-name-input").value;
            document.getElementById("guest-bio").textContent = document.getElementById("guest-bio-input").value;
            document.getElementById("email-link").href = `mailto:${document.getElementById("guest-email-input").value}`;
            document.getElementById("linkedin-link").href = document.getElementById("guest-linkedin-input").value;
            document.getElementById("twitter-link").href = document.getElementById("guest-twitter-input").value;
        });
    });

    document.getElementById("edit-profile").addEventListener("click", function() {
        openPopup("Edit Profile", [
            { label: "Edit Name:", type: "text", id: "edit-name" },
            { label: "Edit Bio:", type: "text", id: "edit-bio" }
        ], function() {
            document.getElementById("guest-name").textContent = document.getElementById("edit-name").value;
            document.getElementById("guest-bio").textContent = document.getElementById("edit-bio").value;
        });
    });

    document.getElementById("remove-guest").addEventListener("click", function() {
        openPopup("Remove Guest", [], function() {
            document.getElementById("guest-name").textContent = "Guest Name";
            document.getElementById("guest-bio").textContent = "Short Bio of the Guest";
            document.getElementById("email-link").textContent = "guest@example.com";
            document.getElementById("linkedin-link").href = "#";
            document.getElementById("twitter-link").href = "#";
        });
    });

    document.getElementById("track-engagement").addEventListener("click", function() {
        alert("Tracking engagement metrics...");
    });

    document.getElementById("search-guest").addEventListener("click", function() {
        openPopup("Search Guest", [
            { label: "Search by Name:", type: "text", id: "search-name" }
        ], function() {
            alert("Searching guest: " + document.getElementById("search-name").value);
        });
    });

    document.getElementById("export-data").addEventListener("click", function() {
        alert("Exporting data...");
    });
});

