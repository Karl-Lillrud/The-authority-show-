emailjs.init("your_user_id"); // Initializes EmailJS (If you want to use it)

const form = document.getElementById("guestForm");
const availableDates = ["2025-03-10", "2025-03-15", "2025-03-20"];

// Function for social media submission
let socialMediaCount = 0;
const maxSocialMedia = 3;

// Loads saved social media on page load
document.addEventListener("DOMContentLoaded", loadSavedSocialMedia);

function addSocialMedia(selectedPlatform = "", profileLink = "") {
    if (socialMediaCount >= maxSocialMedia) return;

    socialMediaCount++;
    const container = document.getElementById("socialMediaContainer");

    // Create wrapper div for each social media input set
    const socialDiv = document.createElement("div");
    socialDiv.classList.add("space-y-2");

    // Dropdown for selecting social media platform
    const select = document.createElement("select");
    select.classList.add("w-full", "border", "p-2", "rounded");
    select.innerHTML = `
        <option value="LinkedIn" ${selectedPlatform === "LinkedIn" ? "selected" : ""}>LinkedIn</option>
        <option value="Instagram" ${selectedPlatform === "Instagram" ? "selected" : ""}>Instagram</option>
        <option value="TikTok" ${selectedPlatform === "TikTok" ? "selected" : ""}>TikTok</option>
        <option value="Twitter" ${selectedPlatform === "Twitter" ? "selected" : ""}>Twitter</option>
        <option value="Facebook" ${selectedPlatform === "Facebook" ? "selected" : ""}>Facebook</option>
        <option value="Whatsapp" ${selectedPlatform === "Whatsapp" ? "selected" : ""}>Whatsapp</option>
    `;

    // Text input for profile link
    const input = document.createElement("input");
    input.type = "url";
    input.classList.add("w-full", "border", "p-2", "rounded");
    input.placeholder = "Enter your profile link";
    input.value = profileLink;

    // Auto-save when user types or selects a platform
    input.addEventListener("input", saveSocialMedia);
    select.addEventListener("change", saveSocialMedia);

    // Remove button
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.classList.add("bg-red-500", "text-white", "px-2", "py-1", "rounded");
    removeBtn.innerText = "Remove";
    removeBtn.onclick = function () {
        socialDiv.remove();
        socialMediaCount--;
        saveSocialMedia(); // Update storage
        document.getElementById("addSocialButton").classList.remove("hidden"); // Show button if under limit
    };

    // Append elements
    socialDiv.appendChild(select);
    socialDiv.appendChild(input);
    socialDiv.appendChild(removeBtn);
    container.appendChild(socialDiv);

    // Hide "Link Social Media" button if 3 fields exist
    if (socialMediaCount >= maxSocialMedia) {
        document.getElementById("addSocialButton").classList.add("hidden");
    }

    // Save current state
    saveSocialMedia();

    // Auto-focus on the profile link textbox
    setTimeout(() => input.focus(), 200);
}

function saveSocialMedia() {
    const socialData = [];
    document.querySelectorAll("#socialMediaContainer div").forEach((div) => {
        const selectedPlatform = div.querySelector("select").value;
        const profileLink = div.querySelector("input").value;
        socialData.push({ platform: selectedPlatform, link: profileLink });
    });

    localStorage.setItem("socialMediaData", JSON.stringify(socialData));
    localStorage.setItem("socialMediaCount", socialData.length);
}

function loadSavedSocialMedia() {
    const savedData = JSON.parse(localStorage.getItem("socialMediaData")) || [];
    socialMediaCount = savedData.length; // Restore the correct count

    savedData.forEach(({ platform, link }) => addSocialMedia(platform, link));

    // Hide button if 3 social media were already added before refresh
    if (socialMediaCount >= maxSocialMedia) {
        document.getElementById("addSocialButton").classList.add("hidden");
    }
}

// Recommend a guest function
let recommendedGuestCount = 0;
const maxRecommendedGuests = 3;

document.addEventListener("DOMContentLoaded", () => {
    loadSavedRecommendedGuests(); // Loads saved guests
});

function addRecommendedGuest(name = "", email = "", reason = "") {
    if (recommendedGuestCount >= maxRecommendedGuests) return;

    recommendedGuestCount++;
    const container = document.getElementById("recommendedGuestContainer");

    // Create wrapper div for each recommended guest input set
    const guestDiv = document.createElement("div");
    guestDiv.classList.add("space-y-2", "border", "p-4", "rounded", "bg-gray-100");

    // Input for guest name
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.classList.add("w-full", "border", "p-2", "rounded");
    nameInput.placeholder = "Enter guest name";
    nameInput.value = name;
    nameInput.addEventListener("input", saveRecommendedGuests);

    // Input for guest email
    const emailInput = document.createElement("input");
    emailInput.type = "email";
    emailInput.classList.add("w-full", "border", "p-2", "rounded");
    emailInput.placeholder = "Enter guest email";
    emailInput.value = email;
    emailInput.addEventListener("input", saveRecommendedGuests);

    // Textarea for reasons
    const reasonInput = document.createElement("textarea");
    reasonInput.classList.add("w-full", "border", "p-2", "rounded");
    reasonInput.placeholder = "Why do you recommend this guest?";
    reasonInput.value = reason;
    reasonInput.addEventListener("input", saveRecommendedGuests);

    // Remove button
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.classList.add("bg-red-500", "text-white", "px-2", "py-1", "rounded");
    removeBtn.innerText = "Remove";
    removeBtn.onclick = function () {
        guestDiv.remove();
        recommendedGuestCount--;
        saveRecommendedGuests();
        document.getElementById("addGuestButton").classList.remove("hidden"); // Show button if under limit
    };

    // Append elements
    guestDiv.appendChild(nameInput);
    guestDiv.appendChild(emailInput);
    guestDiv.appendChild(reasonInput);
    guestDiv.appendChild(removeBtn);
    container.appendChild(guestDiv);

    // Hide "Add Guest" button if 3 guests exist
    if (recommendedGuestCount >= maxRecommendedGuests) {
        document.getElementById("addGuestButton").classList.add("hidden");
    }

    // Save current state
    saveRecommendedGuests();

    // Auto-focus on the guest name input
    setTimeout(() => nameInput.focus(), 200);
}

function saveRecommendedGuests() {
    const guestData = [];
    document.querySelectorAll("#recommendedGuestContainer div").forEach((div) => {
        const name = div.querySelector("input[type='text']").value;
        const email = div.querySelector("input[type='email']").value;
        const reason = div.querySelector("textarea").value;
        guestData.push({ name, email, reason });
    });

    localStorage.setItem("recommendedGuestData", JSON.stringify(guestData));
    localStorage.setItem("recommendedGuestCount", guestData.length);
}

function loadSavedRecommendedGuests() {
    const savedData = JSON.parse(localStorage.getItem("recommendedGuestData")) || [];
    recommendedGuestCount = savedData.length; // Restore the correct count

    savedData.forEach(({ name, email, reason }) => addRecommendedGuest(name, email, reason));

    // Hide button if 3 guests were already added before refresh
    if (recommendedGuestCount >= maxRecommendedGuests) {
        document.getElementById("addGuestButton").classList.add("hidden");
    }
}

// Function to display the file name
function displayFileName() {
    const fileInput = document.getElementById("profilePhoto");
    const fileNameDisplay = document.getElementById("fileName");

    if (fileInput.files.length > 0) {
      fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name}`;
    } else {
      fileNameDisplay.textContent = "";
    }
}

// Function to preview the image
function previewImage() {
    const fileInput = document.getElementById("profilePhoto");
    const fileNameDisplay = document.getElementById("fileName");
    const imagePreview = document.getElementById("imagePreview");
    const previewContainer = document.getElementById("imagePreviewContainer");
    const photoError = document.getElementById("photoError");

    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];

      // Validates file type
      if (!file.type.startsWith("image/")) {
        photoError.textContent = "Please upload a valid image file.";
        fileInput.value = ""; // Clear the input
        fileNameDisplay.textContent = "";
        previewContainer.classList.add("hidden");
        return;
      }

      // Validate file size (Max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        photoError.textContent = "File size exceeds 10MB limit.";
        fileInput.value = ""; // Clear the input
        fileNameDisplay.textContent = "";
        previewContainer.classList.add("hidden");
        return;
      }

      // Clears error message
      photoError.textContent = "";

      // Display files name
      fileNameDisplay.textContent = `Selected file: ${file.name}`;

      // Show image preview
      const reader = new FileReader();
      reader.onload = function (e) {
        const imageData = e.target.result;
        imagePreview.src = imageData;
        previewContainer.classList.remove("hidden");

        // Save the image to localStorage
        localStorage.setItem("imageData", imageData);
      };
      reader.readAsDataURL(file);
    } else {
      fileNameDisplay.textContent = "";
      previewContainer.classList.add("hidden");

      // Clear image data from localStorage if no file is selected
      localStorage.removeItem("imageData");
    }
}

// Function to remove the image
function removeImage() {
    const fileInput = document.getElementById("profilePhoto");
    const fileNameDisplay = document.getElementById("fileName");
    const previewContainer = document.getElementById("imagePreviewContainer");
    const imagePreview = document.getElementById("imagePreview");

    fileInput.value = ""; // Clear the files input
    fileNameDisplay.textContent = "";
    previewContainer.classList.add("hidden");

    // Remove image from localStorage
    localStorage.removeItem("imageData");

    imagePreview.src = "";
}

// Load the image from localStorage on page load (if it exists)
window.onload = function() {
    const imageData = localStorage.getItem("imageData");
    const imagePreview = document.getElementById("imagePreview");
    const previewContainer = document.getElementById("imagePreviewContainer");

    if (imageData) {
        imagePreview.src = imageData;
        previewContainer.classList.remove("hidden");
    }
};

// Calender
document.addEventListener("DOMContentLoaded", function () {
    const openDatePickerBtn = document.getElementById("openDatePicker");
    const dateTimeContainer = document.getElementById("dateTimeContainer");
    const confirmDateTimeBtn = document.getElementById("confirmDateTime");
    const selectedDateTime = document.getElementById("selectedDateTime");
    const timePickerContainer = document.getElementById("timePickerContainer");
    const timePicker = document.getElementById("timePicker");
    const calendarPicker = document.getElementById("calendarPicker");

    const prevMonthBtn = document.getElementById("prevMonth");
    const nextMonthBtn = document.getElementById("nextMonth");
    const currentMonthYear = document.getElementById("currentMonthYear");
    const yearSelector = document.getElementById("yearSelector");

    let selectedDate = null;
    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();

    // Define unavailable dates
    let unavailableDates = [];


    async function fetchUnavailableDates() {
        try {
            const response = await fetch("/api/creator-availability");
            const data = await response.json();
            unavailableDates = data.unavailableDates || [];


            if (data.events) {
                unavailableDates = data.events.map(event => {
                  const date = new Date(event.start).toISOString().split("T")[0];
                  return date;
                });
              }
          
              generateCalendar(); // Redraw the calendar after fetching data
            } catch (error) {
              console.error("Failed to fetch unavailable dates:", error);
            }
          }
          // Fetch unavailable dates from Google Calendar
          fetchUnavailableDates();


    // Load saved selection from localStorage
    loadSavedDateTime();

    // Open/Close the inline date & time picker
    openDatePickerBtn.addEventListener("click", (e) => {
        e.preventDefault();
        dateTimeContainer.classList.toggle("hidden");
        generateCalendar();
        populateYearDropdown();
    });

    // Save selected date & time
    function saveDateTime() {
        if (selectedDate) {
            localStorage.setItem("recordingDate", selectedDate.toISOString().split('T')[0]);
            localStorage.setItem("selectedDateText", selectedDate.toDateString());
        }
        localStorage.setItem("recordingTime", timePicker.value);
    }

    // Load saved date & time from localStorage
    function loadSavedDateTime() {
        const savedDate = localStorage.getItem("recordingDate");
        const savedTime = localStorage.getItem("recordingTime");
        const savedDateText = localStorage.getItem("selectedDateText");

        if (savedDate) {
            selectedDate = new Date(savedDate);
            document.getElementById("recordingDate").value = savedDate;
            selectedDateTime.textContent = `Selected: ${savedDateText} at ${savedTime}`;
            generateCalendar(); // Refresh calendar with the selected date
        }

        if (savedTime) {
            document.getElementById("recordingTime").value = savedTime;
        }
    }

    // Populate the year dropdown (10 years forward & back)
    function populateYearDropdown() {
        yearSelector.innerHTML = "";
        for (let i = currentYear - 10; i <= currentYear + 10; i++) {
            let option = document.createElement("option");
            option.value = i;
            option.textContent = i;
            if (i === currentYear) option.selected = true;
            yearSelector.appendChild(option);
        }
    }

    // Handle month navigation
    prevMonthBtn.addEventListener("click", (e) => {
        e.preventDefault();
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        generateCalendar();
    });

    nextMonthBtn.addEventListener("click", (e) => {
        e.preventDefault();
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        generateCalendar();
    });

    // Handle year change
    yearSelector.addEventListener("change", (e) => {
        e.preventDefault();
        currentYear = parseInt(yearSelector.value);
        generateCalendar();
    });

    // Generate a simple inline calendar with unavailable dates
    function generateCalendar() {
        calendarPicker.innerHTML = "";
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        const today = new Date(); // Get today's date
        today.setHours(0, 0, 0, 0); // Normalize to midnight for comparison

        currentMonthYear.textContent = `${new Date(currentYear, currentMonth).toLocaleString('default', { month: 'long' })} ${currentYear}`;

        const daysOfWeek = ["S", "M", "T", "W", "T", "F", "S"];

        // Display days of the week
        daysOfWeek.forEach(day => {
            const dayEl = document.createElement("div");
            dayEl.classList.add("text-center", "font-bold");
            dayEl.textContent = day;
            calendarPicker.appendChild(dayEl);
        });

        // Fill in empty days at start of month
        for (let i = 0; i < firstDay; i++) {
            const emptyDiv = document.createElement("div");
            calendarPicker.appendChild(emptyDiv);
        }

        // Fill in days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayEl = document.createElement("button");
            dayEl.type = "button"; // Prevent it from submitting
            dayEl.textContent = day;
            dayEl.classList.add("p-2", "text-center", "rounded", "hover:bg-blue-200");

            const fullDate = new Date(currentYear, currentMonth, day);
            const formattedDate = fullDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD

            // Check if the date is unavailable or in the past
            if (fullDate < today || fullDate.getDay() === 0 || fullDate.getDay() === 6 || unavailableDates.includes(formattedDate)) {
                dayEl.classList.add("text-gray-400", "cursor-not-allowed", "line-through");
            } else {
                dayEl.classList.add("bg-blue-100", "cursor-pointer");

                // Restore selected date after refresh
                if (formattedDate === localStorage.getItem("recordingDate")) {
                    dayEl.classList.add("bg-blue-500", "text-white");
                }

                dayEl.addEventListener("click", (e) => {
                    e.preventDefault();
                    selectedDate = fullDate;
                    document.querySelectorAll("#calendarPicker button").forEach(btn => btn.classList.remove("bg-blue-500", "text-white"));
                    dayEl.classList.add("bg-blue-500", "text-white");
                    populateTimeSlots();
                });
            }
            calendarPicker.appendChild(dayEl);
        }
    }

    // Populate time slots (only full hours & half hours)
    function populateTimeSlots() {
        timePicker.innerHTML = "";
        timePickerContainer.classList.remove("hidden");

        for (let hour = 9; hour <= 18; hour++) {
            ["00", "30"].forEach(minute => {
                const timeOption = document.createElement("option");
                timeOption.value = `${hour}:${minute}`;
                timeOption.textContent = `${hour}:${minute}`;
                timePicker.appendChild(timeOption);
            });
        }

        confirmDateTimeBtn.classList.remove("hidden");

        // Restore the selected time after refresh
        const savedTime = localStorage.getItem("recordingTime");
        if (savedTime) {
            timePicker.value = savedTime;
        }
    }

    // Confirm selection & prevent unwanted validation
    confirmDateTimeBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const selectedTime = timePicker.value;

        if (selectedDate && selectedTime) {
            document.getElementById("recordingDate").value = selectedDate.toISOString().split('T')[0];
            document.getElementById("recordingTime").value = selectedTime;
            selectedDateTime.textContent = `Selected: ${selectedDate.toDateString()} at ${selectedTime}`;
            dateTimeContainer.classList.add("hidden");

            saveDateTime(); // Save selection to localStorage
        }
    });
});

// Submit form data to the backend
form.addEventListener("submit", function(event) {
    event.preventDefault();

    try {
        const nameInput = document.getElementById("name");
        const emailInput = document.getElementById("email");
        const companyInput = document.getElementById("company");
        const phoneInput = document.getElementById("phone");
        const bioInput = document.getElementById("bio");
        const interestInput = document.getElementById("interest");
        const dateInput = document.getElementById("recordingDate");
        const timeInput = document.getElementById("recordingTime");
        const listInput = document.getElementById("list");
        const notesInput = document.getElementById("notes");

        if (!nameInput || !emailInput || !companyInput) {
            alert("Required fields are missing in the form.");
            return;
        }

        const formData = {
            name: nameInput.value,
            company: companyInput?.value || "",
            email: emailInput?.value || "",
            phone: phoneInput?.value || "",
            socialMedia: JSON.parse(localStorage.getItem("socialMediaData")) || [],
            bio: bioInput?.value || "",
            interest: interestInput?.value || "",
            recordingDate: dateInput?.value || "",
            recordingTime: timeInput?.value || "",
            recommendedGuests: JSON.parse(localStorage.getItem("recommendedGuestData")) || [],
            list: listInput?.value || "",
            imageData: localStorage.getItem("imageData"),
            notes: notesInput?.value || "",
            updatesOption: document.querySelector('input[name="updatesOption"]:checked')?.value || ""
        };
        console.log("Form values before sending:", formData);

        fetch('/guest-form', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            form.reset();
            localStorage.clear();
            document.getElementById("socialMediaContainer").innerHTML = "";
            document.getElementById("recommendedGuestContainer").innerHTML = "";
            document.getElementById("imagePreviewContainer").classList.add("hidden");
            document.getElementById("fileName").textContent = "";
            document.getElementById("selectedDateTime").textContent = "";
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while submitting the form.');
        });
    } catch (err) {
        console.error("Form submission error:", err);
        alert("Could not submit form due to a missing input field.");
    }
});
