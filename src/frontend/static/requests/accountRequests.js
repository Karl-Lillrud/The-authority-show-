// Sidebar navigation functionality
document.querySelectorAll(".sidebar-item").forEach((item) => {
  item.addEventListener("click", function () {
    // Remove active class from all items
    document
      .querySelectorAll(".sidebar-item")
      .forEach((i) => i.classList.remove("active"));
    // Add active class to selected item
    this.classList.add("active");
    // Hide all settings sections
    document
      .querySelectorAll(".settings-section")
      .forEach((section) => (section.style.display = "none"));
    // Show selected section
    const target = this.getAttribute("data-target");
    document.getElementById(target).style.display = "block";
    // Adjust the main content container's min-height to match the sidebar's height
    const sidebarHeight = document.querySelector(".sidebar").offsetHeight;
    document.querySelector(".main-content").style.minHeight =
      sidebarHeight + "px";
  });
});

// Ensure only the Profile settings are displayed when the page is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Hide all settings sections
  document
    .querySelectorAll(".settings-section")
    .forEach((section) => (section.style.display = "none"));
  // Show the Profile section
  document.getElementById("profile-section").style.display = "block";
  // Set the Profile sidebar item as active
  document
    .querySelectorAll(".sidebar-item")
    .forEach((item) => item.classList.remove("active"));
  document
    .querySelector('.sidebar-item[data-target="profile-section"]')
    .classList.add("active");
});

// Subscription functionality for adding user to mailing list
document
  .getElementById("save-subscription")
  .addEventListener("click", function (event) {
    event.preventDefault(); // Prevent page reload
    subscribeUserToMailingList();
  });

function subscribeUserToMailingList() {
  const userEmail = "{{ email }}"; // Assuming email is available in the template context

  // Check if email exists
  if (!userEmail) {
    alert("Email is not available. Please log in again.");
    return;
  }

  // Make a POST request to the backend to add the user to the mailing list and subscription
  fetch("/subscribe", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: userEmail,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);  // Log the data returned from the server
      if (data.success) {
        alert("You have been successfully subscribed to the mailing list and your subscription plan!");
      } else {
        alert("Error subscribing to the mailing list: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error subscribing:", error);
      alert("There was an error subscribing. Please try again.");
    });
}