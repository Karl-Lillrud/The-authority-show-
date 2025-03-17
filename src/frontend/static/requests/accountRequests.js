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

// SECURITY (2FA) Functionality
document.addEventListener("DOMContentLoaded", function () {
  const twoFAToggle = document.getElementById("2fa-toggle");
  const twoFAOptions = document.getElementById("2fa-options");
  const authAppRadio = document.getElementById("2fa-auth");
  const smsRadio = document.getElementById("2fa-sms");
  const qrCodeContainer = document.getElementById("qr-code-container");
  const qrCodeCanvas = document.getElementById("qr-code");

  if (
    !twoFAToggle ||
    !twoFAOptions ||
    !authAppRadio ||
    !smsRadio ||
    !qrCodeContainer ||
    !qrCodeCanvas
  ) {
    console.error("One or more 2FA elements not found.");
    return;
  }

  twoFAToggle.addEventListener("change", function () {
    if (twoFAToggle.checked) {
      twoFAOptions.style.display = "block";
    } else {
      twoFAOptions.style.display = "none";
      qrCodeContainer.style.display = "none";
    }
  });

  function generateQRCode() {
    qrCodeContainer.style.display = "block";
    // Clear any existing QR code
    qrCodeCanvas.innerHTML = "";
    new QRCode(qrCodeCanvas, {
      text: "otpauth://totp/MyApp?secret=JBSWY3DPEHPK3PXP&issuer=MyApp",
      width: 128,
      height: 128
    });
  }

  authAppRadio.addEventListener("change", function () {
    if (authAppRadio.checked) {
      generateQRCode();
    }
  });

  smsRadio.addEventListener("change", function () {
    if (smsRadio.checked) {
      qrCodeContainer.style.display = "none";
    }
  });
});

// SUBSCRIPTIONS Functionality (Payment Methods)
document
  .getElementById("subscription-form")
  .addEventListener("submit", function (event) {
    event.preventDefault();
    alert("Subscription updated successfully.");
  });

let paymentMethods = [];
function updatePaymentMethodsDisplay() {
  const dropdown = document.getElementById("payment-methods-dropdown");
  dropdown.innerHTML = "";
  if (paymentMethods.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No payment methods added";
    dropdown.appendChild(opt);
    dropdown.disabled = true;
  } else {
    dropdown.disabled = false;
    paymentMethods.forEach((pm, index) => {
      const opt = document.createElement("option");
      opt.value = index;
      const cardInfo = pm.cardNumber
        ? `Card ending in ${pm.cardNumber.slice(-4)}`
        : "Unknown Card";
      opt.textContent = `${index + 1}. ${cardInfo} | Exp: ${pm.expiry
        } | Holder: ${pm.holderName}`;
      dropdown.appendChild(opt);
    });
  }
}
function showPaymentMethodForm(mode, paymentMethodIndex = null) {
  const formOverlay = document.createElement("div");
  formOverlay.id = "payment-method-form-overlay";
  Object.assign(formOverlay.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: "1000"
  });
  const formDiv = document.createElement("div");
  Object.assign(formDiv.style, {
    backgroundColor: "#fff",
    padding: "20px",
    borderRadius: "5px",
    width: "300px"
  });
  formDiv.innerHTML = `
      <h3>${mode === "add" ? "Add" : "Update"} Payment Method</h3>
      <form id="payment-method-form">
        <div class="form-group">
          <label for="card-number">Card Number</label>
          <input type="text" id="card-number" class="input-field" placeholder="Enter card number" required>
        </div>
        <div class="form-group">
          <label for="expiry">Expiry Date</label>
          <input type="text" id="expiry" class="input-field" placeholder="MM/YY" required>
        </div>
        <div class="form-group">
          <label for="holder-name">Card Holder Name</label>
          <input type="text" id="holder-name" class="input-field" placeholder="Enter card holder name" required>
        </div>
        <button type="submit" class="button button-primary">${mode === "add" ? "Add" : "Update"
    }</button>
        <button type="button" id="cancel-payment-form" class="button">Cancel</button>
      </form>
    `;
  formOverlay.appendChild(formDiv);
  document.body.appendChild(formOverlay);
  if (mode === "update" && paymentMethodIndex !== null) {
    const pm = paymentMethods[paymentMethodIndex];
    document.getElementById("card-number").value = pm.cardNumber || "";
    document.getElementById("expiry").value = pm.expiry || "";
    document.getElementById("holder-name").value = pm.holderName || "";
  }
  document
    .getElementById("payment-method-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      const cardNumber = document.getElementById("card-number").value.trim();
      const expiry = document.getElementById("expiry").value.trim();
      const holderName = document.getElementById("holder-name").value.trim();
      if (mode === "add") {
        paymentMethods.push({ cardNumber, expiry, holderName });
      } else if (mode === "update" && paymentMethodIndex !== null) {
        paymentMethods[paymentMethodIndex] = {
          cardNumber,
          expiry,
          holderName
        };
      }
      updatePaymentMethodsDisplay();
      document.body.removeChild(formOverlay);
    });
  document
    .getElementById("cancel-payment-form")
    .addEventListener("click", function () {
      document.body.removeChild(formOverlay);
    });
}
document
  .getElementById("btn-add-payment")
  .addEventListener("click", function () {
    showPaymentMethodForm("add");
  });
document
  .getElementById("btn-update-payment")
  .addEventListener("click", function () {
    const dropdown = document.getElementById("payment-methods-dropdown");
    const index = dropdown.value;
    if (index === "" || index === null) {
      alert("No payment method selected.");
      return;
    }
    showPaymentMethodForm("update", index);
  });
document
  .getElementById("btn-remove-payment")
  .addEventListener("click", function () {
    const dropdown = document.getElementById("payment-methods-dropdown");
    const index = dropdown.value;
    if (index === "" || index === null) {
      alert("No payment method selected.");
      return;
    }
    if (confirm("Are you sure you want to remove this payment method?")) {
      paymentMethods.splice(index, 1);
      updatePaymentMethodsDisplay();
    }
  });
updatePaymentMethodsDisplay();

// DELETE ACCOUNT Functionality 

// Cancel button event listener
const cancelButton = document.getElementById("cancel-delete");
if (cancelButton) {
  cancelButton.addEventListener("click", function () {
    window.location.href = "/settings";
  });
} else {
  console.error("Cancel button not found in the DOM!");
}

// Delete Account Form Submission
const deleteForm = document.getElementById("delete-account-form");
const deleteModal = document.getElementById("delete-account-modal");
const deleteModalMessage = document.getElementById("delete-modal-message");

if (!deleteForm || !deleteModal || !deleteModalMessage) {
  console.error("Error: Delete account form elements not found in the DOM.");
} else {
  deleteForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const email = document.getElementById("delete-email").value.trim();
    const password = document.getElementById("delete-password").value;
    const confirmPassword = document.getElementById("confirm-delete-password").value;
    const deleteConfirm = document.getElementById("delete-confirm").value.trim();

    // Basic client-side validation
    if (!email) {
      showDeleteModal("Email is required.", false);
      return;
    }
    if (!password) {
      showDeleteModal("Password is required.", false);
      return;
    }
    if (!confirmPassword) {
      showDeleteModal("Confirm password is required.", false);
      return;
    }
    if (password !== confirmPassword) {
      showDeleteModal("Confirm Passwords do not match.", false);
      return;
    }
    if (deleteConfirm !== "DELETE") {
      showDeleteModal("You must type DELETE exactly.", false);
      return;
    }

    // Payload for API request
    const payload = {
      deleteEmail: email,
      deletePassword: password,
      deleteConfirm: deleteConfirm
    };

    // Fetch API call to delete account
    fetch(`/delete_user`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(response => {
        // Check if response is JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          return response.json().then(data => ({ status: response.status, data }));
        } else {
          return response.text().then(() => {
            throw new Error("Unexpected response received. Possible server error.");
          });
        }
      })
      .then(result => {
        if (result.status === 200) {
          showDeleteModal("Account deleted successfully!", true, true, "/logout");
        } else if (result.data.error === "User not found") {
          showDeleteModal("User not found. Please check your email.", false);
        } else if (result.data.error === "Incorrect password") {
          showDeleteModal("Incorrect password. Please try again.", false);
        } else {
          showDeleteModal(result.data.error || "Failed to delete account.", false);
        }
      })
      .catch(error => {
        console.error("Error during deletion:", error);
        showDeleteModal("An error occurred while deleting your account. Please try again.", false);
      });
  });
}

function showDeleteModal(message, isSuccess = false, redirect = false, redirectUrl = "") {
  const deleteModal = document.getElementById("delete-account-modal");
  const deleteMessage = document.getElementById("delete-modal-message");
  const deleteContainer = document.querySelector(".delete-account-container");

  if (!deleteModal || !deleteMessage) {
    console.error("Error: Modal elements not found in DOM.");
    return;
  }

  // Set the modal message
  deleteMessage.textContent = message;

  // Set background color dynamically from container
  const computedStyle = window.getComputedStyle(deleteContainer);
  deleteModal.style.backgroundColor = computedStyle.backgroundColor;

  // Apply success/error class
  deleteModal.classList.remove("success", "error");
  deleteModal.classList.add(isSuccess ? "success" : "error");

  // Display modal
  deleteModal.style.display = "block";
  deleteModal.style.opacity = "1";

  // Auto-hide after 3 seconds if it's a success message
  if (isSuccess) {
    setTimeout(() => {
      deleteModal.style.opacity = "0";
      setTimeout(() => {
        deleteModal.style.display = "none";
        if (redirect && redirectUrl) {
          window.location.href = redirectUrl;
        }
      }, 300); // Smooth fade-out effect
    }, 3000);
  }
}