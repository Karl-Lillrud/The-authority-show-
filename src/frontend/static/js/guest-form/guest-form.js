// emailjs.init("your_user_id") // Initializes EmailJS (If you want to use it) - Removed initialization as per instructions .

const form = document.getElementById("guestForm")
const availableDates = ["2025-03-10", "2025-03-15", "2025-03-20"]

// Function for social media submission
let socialMediaCount = 0
const maxSocialMedia = 3

// Loads saved social media on page load
document.addEventListener("DOMContentLoaded", loadSavedSocialMedia)

function addSocialMedia(selectedPlatform = "", profileLink = "") {
  if (socialMediaCount >= maxSocialMedia) return

  socialMediaCount++
  const container = document.getElementById("socialMediaContainer")

  // Create wrapper div for each social media input set
  const socialDiv = document.createElement("div")
  socialDiv.classList.add("space-y-2")

  // Dropdown for selecting social media platform
  const select = document.createElement("select")
  select.classList.add("w-full", "border", "p-2", "rounded")
  select.innerHTML = `
        <option value="LinkedIn" ${selectedPlatform === "LinkedIn" ? "selected" : ""}>LinkedIn</option>
        <option value="Instagram" ${selectedPlatform === "Instagram" ? "selected" : ""}>Instagram</option>
        <option value="TikTok" ${selectedPlatform === "TikTok" ? "selected" : ""}>TikTok</option>
        <option value="Twitter" ${selectedPlatform === "Twitter" ? "selected" : ""}>Twitter</option>
        <option value="Facebook" ${selectedPlatform === "Facebook" ? "selected" : ""}>Facebook</option>
        <option value="Whatsapp" ${selectedPlatform === "Whatsapp" ? "selected" : ""}>Whatsapp</option>
    `

  // Text input for profile link
  const input = document.createElement("input")
  input.type = "url"
  input.classList.add("w-full", "border", "p-2", "rounded")
  input.placeholder = "Enter your profile link"
  input.value = profileLink

  // Auto-save when user types or selects a platform
  input.addEventListener("input", saveSocialMedia)
  select.addEventListener("change", saveSocialMedia)

  // Remove button
  const removeBtn = document.createElement("button")
  removeBtn.type = "button"
  removeBtn.classList.add("bg-red-500", "text-white", "px-2", "py-1", "rounded")
  removeBtn.innerText = "Remove"
  removeBtn.onclick = () => {
    socialDiv.remove()
    socialMediaCount--
    saveSocialMedia() // Update storage
    document.getElementById("addSocialButton").classList.remove("hidden") // Show button if under limit
  }

  // Append elements
  socialDiv.appendChild(select)
  socialDiv.appendChild(input)
  socialDiv.appendChild(removeBtn)
  container.appendChild(socialDiv)

  // Hide "Link Social Media" button if 3 fields exist
  if (socialMediaCount >= maxSocialMedia) {
    document.getElementById("addSocialButton").classList.add("hidden")
  }

  // Save current state
  saveSocialMedia()

  // Auto-focus on the profile link textbox
  setTimeout(() => input.focus(), 200)
}

function saveSocialMedia() {
  const socialData = []
  document.querySelectorAll("#socialMediaContainer div").forEach((div) => {
    const selectedPlatform = div.querySelector("select").value
    const profileLink = div.querySelector("input").value
    socialData.push({ platform: selectedPlatform, link: profileLink })
  })

  localStorage.setItem("socialMediaData", JSON.stringify(socialData))
  localStorage.setItem("socialMediaCount", socialData.length)
}

function loadSavedSocialMedia() {
  const savedData = JSON.parse(localStorage.getItem("socialMediaData")) || []
  socialMediaCount = savedData.length // Restore the correct count

  savedData.forEach(({ platform, link }) => addSocialMedia(platform, link))

  // Hide button if 3 social media were already added before refresh
  if (socialMediaCount >= maxSocialMedia) {
    document.getElementById("addSocialButton").classList.add("hidden")
  }
}

// Recommend a guest function
let recommendedGuestCount = 0
const maxRecommendedGuests = 3

document.addEventListener("DOMContentLoaded", () => {
  loadSavedRecommendedGuests() // Loads saved guests
})

function addRecommendedGuest(name = "", email = "", reason = "") {
  if (recommendedGuestCount >= maxRecommendedGuests) return

  recommendedGuestCount++
  const container = document.getElementById("recommendedGuestContainer")

  // Create wrapper div for each recommended guest input set
  const guestDiv = document.createElement("div")
  guestDiv.classList.add("space-y-2", "border", "p-4", "rounded", "bg-gray-100")

  // Input for guest name
  const nameInput = document.createElement("input")
  nameInput.type = "text"
  nameInput.classList.add("w-full", "border", "p-2", "rounded")
  nameInput.placeholder = "Enter guest name"
  nameInput.value = name
  nameInput.addEventListener("input", saveRecommendedGuests)

  // Input for guest email
  const emailInput = document.createElement("input")
  emailInput.type = "email"
  emailInput.classList.add("w-full", "border", "p-2", "rounded")
  emailInput.placeholder = "Enter guest email"
  emailInput.value = email
  emailInput.addEventListener("input", saveRecommendedGuests)

  // Textarea for reasons
  const reasonInput = document.createElement("textarea")
  reasonInput.classList.add("w-full", "border", "p-2", "rounded")
  reasonInput.placeholder = "Why do you recommend this guest?"
  reasonInput.value = reason
  reasonInput.addEventListener("input", saveRecommendedGuests)

  // Remove button
  const removeBtn = document.createElement("button")
  removeBtn.type = "button"
  removeBtn.classList.add("bg-red-500", "text-white", "px-2", "py-1", "rounded")
  removeBtn.innerText = "Remove"
  removeBtn.onclick = () => {
    guestDiv.remove()
    recommendedGuestCount--
    saveRecommendedGuests()
    document.getElementById("addGuestButton").classList.remove("hidden") // Show button if under limit
  }

  // Append elements
  guestDiv.appendChild(nameInput)
  guestDiv.appendChild(emailInput)
  guestDiv.appendChild(reasonInput)
  guestDiv.appendChild(removeBtn)
  container.appendChild(guestDiv)

  // Hide "Add Guest" button if 3 guests exist
  if (recommendedGuestCount >= maxRecommendedGuests) {
    document.getElementById("addGuestButton").classList.add("hidden")
  }

  // Save current state
  saveRecommendedGuests()

  // Auto-focus on the guest name input
  setTimeout(() => nameInput.focus(), 200)
}

function saveRecommendedGuests() {
  const guestData = []
  document.querySelectorAll("#recommendedGuestContainer div").forEach((div) => {
    const name = div.querySelector("input[type='text']").value
    const email = div.querySelector("input[type='email']").value
    const reason = div.querySelector("textarea").value
    guestData.push({ name, email, reason })
  })

  localStorage.setItem("recommendedGuestData", JSON.stringify(guestData))
  localStorage.setItem("recommendedGuestCount", guestData.length)
}

function loadSavedRecommendedGuests() {
  const savedData = JSON.parse(localStorage.getItem("recommendedGuestData")) || []
  recommendedGuestCount = savedData.length // Restore the correct count

  savedData.forEach(({ name, email, reason }) => addRecommendedGuest(name, email, reason))

  // Hide button if 3 guests were already added before refresh
  if (recommendedGuestCount >= maxRecommendedGuests) {
    document.getElementById("addGuestButton").classList.add("hidden")
  }
}

// Function to display the file name
function displayFileName() {
  const fileInput = document.getElementById("profilePhoto")
  const fileNameDisplay = document.getElementById("fileName")

  if (fileInput.files.length > 0) {
    fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name}`
  } else {
    fileNameDisplay.textContent = ""
  }
}

// Function to preview the image
function previewImage() {
  const fileInput = document.getElementById("profilePhoto")
  const fileNameDisplay = document.getElementById("fileName")
  const imagePreview = document.getElementById("imagePreview")
  const previewContainer = document.getElementById("imagePreviewContainer")
  const photoError = document.getElementById("photoError")

  if (fileInput.files.length > 0) {
    const file = fileInput.files[0]

    // Validates file type
    if (!file.type.startsWith("image/")) {
      photoError.textContent = "Please upload a valid image file."
      fileInput.value = "" // Clear the input
      fileNameDisplay.textContent = ""
      previewContainer.classList.add("hidden")
      return
    }

    // Validate file size (Max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      photoError.textContent = "File size exceeds 10MB limit."
      fileInput.value = "" // Clear the input
      fileNameDisplay.textContent = ""
      previewContainer.classList.add("hidden")
      return
    }

    // Clears error message
    photoError.textContent = ""

    // Display files name
    fileNameDisplay.textContent = `Selected file: ${file.name}`

    // Show image preview
    const reader = new FileReader()
    reader.onload = (e) => {
      const imageData = e.target.result
      imagePreview.src = imageData
      previewContainer.classList.remove("hidden")

      // Save the image to localStorage
      localStorage.setItem("imageData", imageData)
    }
    reader.readAsDataURL(file)
  } else {
    fileNameDisplay.textContent = ""
    previewContainer.classList.add("hidden")

    // Clear image data from localStorage if no file is selected
    localStorage.removeItem("imageData")
  }
}

// Function to remove the image
function removeImage() {
  const fileInput = document.getElementById("profilePhoto")
  const fileNameDisplay = document.getElementById("fileName")
  const previewContainer = document.getElementById("imagePreviewContainer")
  const imagePreview = document.getElementById("imagePreview")

  fileInput.value = "" // Clear the files input
  fileNameDisplay.textContent = ""
  previewContainer.classList.add("hidden")

  // Remove image from localStorage
  localStorage.removeItem("imageData")

  imagePreview.src = ""
}

// Load the image from localStorage on page load (if it exists)
window.onload = () => {
  const imageData = localStorage.getItem("imageData")
  const imagePreview = document.getElementById("imagePreview")
  const previewContainer = document.getElementById("imagePreviewContainer")

  if (imageData) {
    imagePreview.src = imageData
    previewContainer.classList.remove("hidden")
  }
}

// Calendar
document.addEventListener("DOMContentLoaded", () => {
  const openDatePickerBtn = document.getElementById("openDatePicker")
  const dateTimeContainer = document.getElementById("dateTimeContainer")
  const confirmDateTimeBtn = document.getElementById("confirmDateTime")
  const selectedDateTime = document.getElementById("selectedDateTime")
  const timePickerContainer = document.getElementById("timePickerContainer")
  const calendarPicker = document.getElementById("calendarPicker")

  const prevMonthBtn = document.getElementById("prevMonth")
  const nextMonthBtn = document.getElementById("nextMonth")
  const currentMonthYear = document.getElementById("currentMonthYear")
  const yearSelector = document.getElementById("yearSelector")

  let selectedDate = null
  let currentMonth = new Date().getMonth()
  let currentYear = new Date().getFullYear()

  // Global variables to store calendar data
  let globalBusyDates = []
  let globalBusyTimes = {}
  let globalWorkingHours = { start: "09:00:00", end: "17:00:00" }

  // Fetch available dates and working hours from the backend
  async function fetchAvailableDates() {
    try {
      // First, try to get the token from URL parameters
      const urlParams = new URLSearchParams(window.location.search)
      let googleCalToken = urlParams.get("googleCal")

      // If not in URL, try localStorage or sessionStorage
      if (!googleCalToken) {
        googleCalToken = localStorage.getItem("googleCalToken") || sessionStorage.getItem("googleCalToken")
      }

      // If still no token, try to get it from the server
      if (!googleCalToken) {
        try {
          const tokenResponse = await fetch("/get_google_cal_token")
          if (tokenResponse.ok) {
            const tokenData = await tokenResponse.json()
            googleCalToken = tokenData.token
            if (googleCalToken) {
              localStorage.setItem("googleCalToken", googleCalToken)
            }
          }
        } catch (tokenError) {
          console.error("Error fetching token from server:", tokenError)
        }
      }

      // If we still don't have a token, show a connect button
      if (!googleCalToken) {
        console.error("No Google Calendar token available")
        showConnectCalendarButton()
        return
      }

      // Make the request to the backend
      const response = await fetch(`/guest-form/available_dates?googleCal=${googleCalToken}`)

      if (!response.ok) {
        const errorData = await response.json()
        // If unauthorized or token expired, clear stored token and show connect button
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem("googleCalToken")
          sessionStorage.removeItem("googleCalToken")
          showConnectCalendarButton()
        }
        throw new Error(errorData.error || "Failed to fetch available dates")
      }

      const data = await response.json()
      console.log("Available dates data:", data)

      // Update the calendar with the fetched data
      updateCalendarWithAvailability(data)

      // Hide connect button if it was shown
      hideConnectCalendarButton()
    } catch (error) {
      console.error("Error fetching available dates:", error)
      // Display error message to user
      const errorContainer = document.getElementById("calendarError")
      if (errorContainer) {
        errorContainer.textContent = `Error: ${error.message}`
        errorContainer.classList.remove("hidden")
      }
    }
  }

  // Function to show the connect calendar button
  function showConnectCalendarButton() {
    const calendarContainer = document.getElementById("dateTimeContainer")
    const connectButtonContainer = document.getElementById("connectCalendarContainer")

    if (calendarContainer) {
      calendarContainer.classList.add("hidden")
    }

    if (!connectButtonContainer) {
      // Create the connect button container if it doesn't exist
      const container = document.createElement("div")
      container.id = "connectCalendarContainer"
      container.className = "text-center p-4 border rounded bg-gray-100 my-4"
      container.innerHTML = `
            <p class="mb-2">Please connect your Google Calendar to view available dates.</p>
            <button id="connectCalendarBtn" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Connect Google Calendar
            </button>
          `

      // Insert the container before the calendar
      const formElement = document.getElementById("guestForm")
      if (formElement) {
        const recordingDateField = document.getElementById("recordingDateField")
        if (recordingDateField) {
          recordingDateField.parentNode.insertBefore(container, recordingDateField.nextSibling)
        } else {
          formElement.insertBefore(container, formElement.firstChild)
        }
      }

      // Add event listener to the connect button
      document.getElementById("connectCalendarBtn").addEventListener("click", connectGoogleCalendar)
    } else {
      connectButtonContainer.classList.remove("hidden")
    }
  }

  // Function to hide the connect calendar button
  function hideConnectCalendarButton() {
    const connectButtonContainer = document.getElementById("connectCalendarContainer")
    const calendarContainer = document.getElementById("dateTimeContainer")

    if (connectButtonContainer) {
      connectButtonContainer.classList.add("hidden")
    }

    if (calendarContainer) {
      calendarContainer.classList.remove("hidden")
    }
  }

  // Function to connect to Google Calendar
  function connectGoogleCalendar() {
    window.location.href = "/connect_google_calendar"
  }

  // Function to update the calendar with availability data
  function updateCalendarWithAvailability(data) {
    // Store the data in our module-level variables
    globalBusyDates = data.busy_dates || []
    globalBusyTimes = data.busy_times || {}
    globalWorkingHours = data.working_hours || { start: "09:00:00", end: "17:00:00" }

    // Log the data we received to help with debugging
    console.log("Calendar data received:", {
      busyDates: globalBusyDates,
      busyTimes: globalBusyTimes,
      workingHours: globalWorkingHours,
    })

    // For testing purposes, if no busy times were provided, create some sample data
    if (Object.keys(globalBusyTimes).length === 0) {
      // Create sample busy times for today
      const today = new Date()
      const todayStr = today.toISOString().split("T")[0]

      globalBusyTimes[todayStr] = [
        { start: "10:00:00", end: "11:30:00" },
        { start: "14:00:00", end: "15:00:00" },
      ]

      console.log("Added sample busy times for testing:", globalBusyTimes)
    }

    // Generate the calendar with the new data
    generateCalendar()
  }

  // Load saved selection from localStorage
  loadSavedDateTime()

  // Open/Close the inline date & time picker
  openDatePickerBtn.addEventListener("click", (e) => {
    e.preventDefault()
    dateTimeContainer.classList.toggle("hidden")
    generateCalendar()
    populateYearDropdown()
  })

  // Save selected date & time
  function saveDateTime() {
    if (selectedDate) {
      localStorage.setItem("recordingDate", selectedDate.toISOString().split("T")[0])
      localStorage.setItem("selectedDateText", selectedDate.toDateString())
    }
    localStorage.setItem("recordingTime", document.querySelector(".time-slot.selected")?.dataset.time || "")
  }

  // Load saved date & time from localStorage
  function loadSavedDateTime() {
    const savedDate = localStorage.getItem("recordingDate")
    const savedTime = localStorage.getItem("recordingTime")
    const savedDateText = localStorage.getItem("selectedDateText")

    if (savedDate) {
      selectedDate = new Date(savedDate)
      document.getElementById("recordingDate").value = savedDate

      if (savedTime) {
        selectedDateTime.textContent = `Selected: ${savedDateText} at ${savedTime}`
        document.getElementById("recordingTime").value = savedTime
      }

      generateCalendar() // Refresh calendar with the selected date
    }
  }

  // Populate the year dropdown (10 years forward & back)
  function populateYearDropdown() {
    yearSelector.innerHTML = ""
    for (let i = currentYear - 10; i <= currentYear + 10; i++) {
      const option = document.createElement("option")
      option.value = i
      option.textContent = i
      if (i === currentYear) option.selected = true
      yearSelector.appendChild(option)
    }
  }

  // Handle month navigation
  prevMonthBtn.addEventListener("click", (e) => {
    e.preventDefault()
    currentMonth--
    if (currentMonth < 0) {
      currentMonth = 11
      currentYear--
    }
    generateCalendar()
  })

  nextMonthBtn.addEventListener("click", (e) => {
    e.preventDefault()
    currentMonth++
    if (currentMonth > 11) {
      currentMonth = 0
      currentYear++
    }
    generateCalendar()
  })

  // Handle year change
  yearSelector.addEventListener("change", (e) => {
    e.preventDefault()
    currentYear = Number.parseInt(yearSelector.value)
    generateCalendar()
  })

  // Generate a simple inline calendar with unavailable dates
  function generateCalendar() {
    calendarPicker.innerHTML = ""
    const firstDay = new Date(currentYear, currentMonth, 1).getDay()
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()
    const today = new Date() // Get today's date
    today.setHours(0, 0, 0, 0) // Normalize to midnight for comparison

    currentMonthYear.textContent = `${new Date(currentYear, currentMonth).toLocaleString("default", { month: "long" })} ${currentYear}`

    const daysOfWeek = ["S", "M", "T", "W", "T", "F", "S"]

    // Display days of the week
    daysOfWeek.forEach((day, index) => {
      const dayEl = document.createElement("div")
      dayEl.classList.add("text-center", "font-bold")
      // Highlight weekend headers
      if (index === 0 || index === 6) {
        dayEl.classList.add("text-red-500")
      }
      dayEl.textContent = day
      calendarPicker.appendChild(dayEl)
    })

    // Fill in empty days at start of month
    for (let i = 0; i < firstDay; i++) {
      const emptyDiv = document.createElement("div")
      calendarPicker.appendChild(emptyDiv)
    }

    // Fill in days
    for (let day = 1; day <= daysInMonth; day++) {
      const dayEl = document.createElement("button")
      dayEl.type = "button" // Prevent it from submitting
      dayEl.textContent = day
      dayEl.classList.add("p-2", "text-center", "rounded")

      const fullDate = new Date(currentYear, currentMonth, day)
      const formattedDate = formatDate(fullDate) // Format as YYYY-MM-DD
      const dayOfWeek = fullDate.getDay() // 0 = Sunday, 6 = Saturday

      // Check if the date is unavailable (past, weekend, or busy)
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
      const isBusy = globalBusyDates.includes(formattedDate)
      const isPast = fullDate < today
      const isUnavailable = isPast || isBusy || isWeekend

      if (isUnavailable) {
        // Apply styling for unavailable dates
        dayEl.classList.add("text-gray-400", "cursor-not-allowed", "line-through", "bg-red-100")

        // Add tooltip to show why it's unavailable
        if (isWeekend) {
          dayEl.title = "Weekend - Unavailable"
        } else if (isBusy) {
          dayEl.title = "Busy - Unavailable"
        } else if (isPast) {
          dayEl.title = "Past date - Unavailable"
        }
      } else {
        dayEl.classList.add("bg-blue-100", "cursor-pointer", "hover:bg-blue-200")

        // Restore selected date after refresh
        if (selectedDate && formattedDate === formatDate(selectedDate)) {
          dayEl.classList.add("bg-blue-500", "text-white")
        }

        dayEl.addEventListener("click", (e) => {
          e.preventDefault()
          selectedDate = fullDate
          document
            .querySelectorAll("#calendarPicker button")
            .forEach((btn) => btn.classList.remove("bg-blue-500", "text-white"))
          dayEl.classList.add("bg-blue-500", "text-white")
          populateTimeSlots()
        })
      }
      calendarPicker.appendChild(dayEl)
    }
  }

  // Helper function to format date as YYYY-MM-DD
  function formatDate(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, "0")
    const day = String(date.getDate()).padStart(2, "0")
    return `${year}-${month}-${day}`
  }

  // Populate time slots based on working hours and busy times
  function populateTimeSlots() {
    timePickerContainer.innerHTML = "" // Clear existing content
    timePickerContainer.classList.remove("hidden")

    if (!selectedDate) return

    const dateStr = formatDate(selectedDate)
    console.log(`Populating time slots for date: ${dateStr}`)

    // Get busy slots for the selected date
    const busySlots = globalBusyTimes[dateStr] || []
    console.log(`Busy slots for ${dateStr}:`, busySlots)

    const workingStart = parseTime(globalWorkingHours.start)
    const workingEnd = parseTime(globalWorkingHours.end)

    // Create a time slots container
    const timeSlotsContainer = document.createElement("div")
    timeSlotsContainer.className = "time-slots-container"

    // Create a heading
    const heading = document.createElement("h3")
    heading.className = "text-lg font-semibold mb-3"
    heading.textContent = "Available Times"
    timePickerContainer.appendChild(heading)

    // Track if we have any available times
    let hasAvailableTimes = false

    // Create time slots in 1-hour increments
    for (let hour = workingStart.hour; hour <= workingEnd.hour; hour++) {
      // Skip if we're at the end time
      if (hour === workingEnd.hour) continue

      const timeStr = `${hour.toString().padStart(2, "0")}:00`
      const fullTimeStr = `${timeStr}:00` // Add seconds for comparison

      // Check if this time is busy
      const isBusy = isTimeBusy(timeStr, busySlots)

      // Only add available time slots
      if (!isBusy) {
        hasAvailableTimes = true

        const timeSlot = document.createElement("div")
        timeSlot.className = "time-slot available"
        timeSlot.dataset.time = timeStr
        timeSlot.textContent = timeStr

        timeSlot.addEventListener("click", () => {
          // Remove selected class from all time slots
          document.querySelectorAll(".time-slot").forEach((slot) => {
            slot.classList.remove("selected")
          })

          // Add selected class to this time slot
          timeSlot.classList.add("selected")

          // Show confirm button
          confirmDateTimeBtn.classList.remove("hidden")
        })

        timeSlotsContainer.appendChild(timeSlot)
      }
    }

    timePickerContainer.appendChild(timeSlotsContainer)

    // Show message if no available times
    if (!hasAvailableTimes) {
      const noTimesMessage = document.createElement("p")
      noTimesMessage.className = "text-center text-gray-500 my-4"
      noTimesMessage.textContent = "No available times for this date"
      timePickerContainer.appendChild(noTimesMessage)
    }

    confirmDateTimeBtn.classList.remove("hidden")

    // Restore the selected time after refresh
    const savedTime = localStorage.getItem("recordingTime")
    if (savedTime) {
      const savedTimeSlot = document.querySelector(`.time-slot[data-time="${savedTime}"]`)
      if (savedTimeSlot) {
        savedTimeSlot.classList.add("selected")
      }
    }
  }

  // Helper function to check if a time is busy
  function isTimeBusy(time, busySlots) {
    // Convert the time (e.g., "13:00") into a Date object for the selected date
    const [hours, minutes] = time.split(":").map(Number)
    const selectedDateTime = new Date(selectedDate) // Use the globally selected date
    selectedDateTime.setHours(hours, minutes, 0, 0) // Set the time on the selected date

    // Loop over each busy slot and compare with the selected time
    for (const slot of busySlots) {
      const startTime = new Date(slot.start) // Convert the start time of the busy slot to a Date object
      const endTime = new Date(slot.end) // Convert the end time of the busy slot to a Date object

      // Check if the selected time falls within the busy slot
      if (selectedDateTime >= startTime && selectedDateTime < endTime) {
        return true // The time is busy
      }
    }

    return false // The time is available
  }

  // Helper function to parse time strings (HH:mm:ss)
  function parseTime(timeStr) {
    const parts = timeStr.split(":")
    return {
      hour: Number(parts[0]),
      minute: Number(parts[1]),
      second: parts.length > 2 ? Number(parts[2]) : 0,
    }
  }

  // Confirm selection & prevent unwanted validation
  confirmDateTimeBtn.addEventListener("click", (e) => {
    e.preventDefault()
    const selectedTimeSlot = document.querySelector(".time-slot.selected")
    const selectedTime = selectedTimeSlot ? selectedTimeSlot.dataset.time : null

    if (selectedDate && selectedTime) {
      document.getElementById("recordingDate").value = formatDate(selectedDate)
      document.getElementById("recordingTime").value = selectedTime
      selectedDateTime.textContent = `Selected: ${selectedDate.toDateString()} at ${selectedTime}`
      dateTimeContainer.classList.add("hidden")

      saveDateTime() // Save selection to localStorage
    } else {
      alert("Please select both a date and time.")
    }
  })

  // Fetch available dates on page load
  fetchAvailableDates()
})

// Add a function to explicitly delete a Google Calendar event
// Add this function after the other calendar-related functions:

function deleteGoogleCalendarEvent(eventId, googleCalToken) {
  if (!eventId || !googleCalToken) {
    console.error("Missing event ID or Google Calendar token for deletion")
    return Promise.reject("Missing event ID or token")
  }

  console.log(`Attempting to delete calendar event: ${eventId}`)

  return fetch("/guest-form/delete-calendar-event", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      eventId: eventId,
      googleCalToken: googleCalToken,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => Promise.reject(data.error || "Failed to delete event"))
      }
      return response.json()
    })
    .then((data) => {
      console.log("Successfully deleted calendar event:", eventId)
      return data
    })
}

// Existing logic or functions here...
document.addEventListener("DOMContentLoaded", () => {
  const guestId = new URLSearchParams(window.location.search).get("guestId") // Get guestId from URL
  let currentGuestData = null // Store the current guest data for reference
  let currentCalendarEventId = null // Store the current calendar event ID

  // Create a hidden field for the calendar event ID
  const calendarEventIdField = document.createElement("input")
  calendarEventIdField.type = "hidden"
  calendarEventIdField.id = "calendarEventId"
  calendarEventIdField.name = "calendarEventId" // Add name attribute for form submission
  document.getElementById("guestForm").appendChild(calendarEventIdField)

  // Fetch guest details if guestId is available
  if (guestId) {
    fetch(`/get_guests_by_id/${guestId}`, { method: "GET" })
      .then((response) => response.json())
      .then((data) => {
        if (data.guest) {
          // Store the current guest data
          currentGuestData = data.guest
          currentCalendarEventId = data.guest.calendarEventId // Store the calendar event ID if it exists

          console.log("Retrieved guest data:", data.guest)
          console.log("Calendar Event ID:", currentCalendarEventId)

          if (currentCalendarEventId) {
            calendarEventIdField.value = currentCalendarEventId
            console.log("Set calendar event ID field to:", calendarEventIdField.value)
          }

          // Populate the form with the guest data - map to schema fields
          document.getElementById("firstName").value = data.guest.name || ""
          document.getElementById("email").value = data.guest.email || ""
          document.getElementById("bio").value = data.guest.bio || ""
          document.getElementById("interest").value = data.guest.areasOfInterest
            ? data.guest.areasOfInterest.join(", ")
            : ""
          document.getElementById("recordingDate").value = data.guest.scheduled
            ? new Date(data.guest.scheduled).toISOString().split("T")[0]
            : ""
          document.getElementById("recordingTime").value = data.guest.scheduled
            ? new Date(data.guest.scheduled).toTimeString().slice(0, 5)
            : ""
          document.getElementById("company").value = data.guest.company || ""
          document.getElementById("phone").value = data.guest.phone || ""
          document.getElementById("list").value = data.guest.tags ? data.guest.tags.join(", ") : ""
          document.getElementById("notes").value = data.guest.notes || ""

          // Handle social media links
          if (data.guest.linkedin) {
            addSocialMedia("LinkedIn", data.guest.linkedin)
          }
          if (data.guest.twitter) {
            addSocialMedia("Twitter", data.guest.twitter)
          }

          // If there's an image, display it
          if (data.guest.image) {
            const imagePreview = document.getElementById("imagePreview")
            const previewContainer = document.getElementById("imagePreviewContainer")
            imagePreview.src = data.guest.image
            previewContainer.classList.remove("hidden")
            localStorage.setItem("imageData", data.guest.image)
          }
        } else {
          alert("Guest not found")
        }
      })
      .catch((error) => {
        console.error("Error fetching guest details:", error)
        alert("An error occurred while fetching guest details.")
      })
  }
})

// Add this at the end of the file or inside the DOMContentLoaded listener
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("guestForm")

  form.addEventListener("submit", (event) => {
    event.preventDefault()

    // Replace the guestId generation code with this:
    const urlParams = new URLSearchParams(window.location.search)
    const guestId = urlParams.get("guestId")

    if (!guestId) {
      console.error("No guestId found in URL parameters")
      alert("Error: No guest ID provided")
      return // Exit the submit handler if no guestId is available
    }

    const profilePhotoData = localStorage.getItem("imageData")
    const socialMediaData = JSON.parse(localStorage.getItem("socialMediaData") || "[]")
    const recommendedGuestData = JSON.parse(localStorage.getItem("recommendedGuestData") || "[]")

    // Extract interest tags from comma-separated list
    const interestTags = document
      .getElementById("interest")
      .value.split(",")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0)

    // Extract list tags from comma-separated list
    const listTags = document
      .getElementById("list")
      .value.split(",")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0)

    // Create a timestamp for the scheduled date/time
    const recordingDate = document.getElementById("recordingDate").value
    const recordingTime = document.getElementById("recordingTime").value
    const scheduledTimestamp =
      recordingDate && recordingTime ? new Date(`${recordingDate}T${recordingTime}:00`).getTime() : null

    // Extract LinkedIn and Twitter from social media data
    let linkedinUrl = ""
    let twitterUrl = ""
    socialMediaData.forEach((item) => {
      if (item.platform === "LinkedIn") linkedinUrl = item.link
      if (item.platform === "Twitter") twitterUrl = item.link
    })

    // Get the calendar event ID if it exists
    const calendarEventId = document.getElementById("calendarEventId")?.value || null
    console.log("Calendar Event ID at form submission:", calendarEventId)

    // Map form data to match the database schema
    const formData = {
      id: guestId, // Use the existing ID
      name: document.getElementById("firstName").value,
      email: document.getElementById("email").value,
      bio: document.getElementById("bio").value,
      areasOfInterest: interestTags,
      scheduled: scheduledTimestamp,
      company: document.getElementById("company").value,
      phone: document.getElementById("phone").value,
      linkedin: linkedinUrl,
      twitter: twitterUrl,
      tags: listTags,
      notes: document.getElementById("notes").value,
      image: profilePhotoData,
      // Include additional fields that might not be in the form but are in the schema
      status: "pending", // Default status
      // Store the recommended guests in a custom field
      recommendedGuests: recommendedGuestData,
      // Store the Google Calendar token for event creation
      googleCalToken:
        new URLSearchParams(window.location.search).get("googleCal") || localStorage.getItem("googleCalToken") || "",
      // Store the current calendar event ID if it exists
      calendarEventId: calendarEventId,
    }

    // Send the form data to update the guest
    fetch(`/edit_guests/${guestId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message === "Guest updated successfully") {
          alert("Guest information updated successfully!")

          // Update Google Calendar event if the recording date or time changed
          const googleCalToken = formData.googleCalToken
          if (googleCalToken && recordingDate && recordingTime) {
            console.log("Updating calendar event with ID:", calendarEventId)

            // First delete the existing event if there is one
            let deletePromise = Promise.resolve()
            if (calendarEventId) {
              console.log("Deleting existing calendar event:", calendarEventId)
              deletePromise = deleteGoogleCalendarEvent(calendarEventId, googleCalToken).catch((error) => {
                console.warn("Error deleting calendar event, continuing with creation:", error)
                // Continue even if deletion fails
                return Promise.resolve()
              })
            }

            // After deletion (or if no deletion needed), create the new event
            deletePromise.then(() => {
              const eventData = {
                summary: `Podcast Recording: ${formData.name}`,
                description: `Recording with ${formData.name} from ${formData.company || "N/A"}`,
                start: {
                  dateTime: `${recordingDate}T${recordingTime}:00`,
                  timeZone: "Europe/Stockholm",
                },
                end: {
                  dateTime: `${recordingDate}T${recordingTime}:30`,
                  timeZone: "Europe/Stockholm", // Adjust duration as necessary
                },
                attendees: [{ email: formData.email }],
                googleCalToken: googleCalToken, // Add the token to the request body
                guestId: guestId, // Include the guest ID for updating the record
              }

              // Send the event data to create a new calendar event
              fetch("/guest-form/create-google-calendar-event", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(eventData),
              })
                .then((calendarResponse) => calendarResponse.json())
                .then((calendarData) => {
                  console.log("Google Calendar event created:", calendarData)

                  // If we got a new event ID, store it in the hidden field
                  if (calendarData.eventId) {
                    document.getElementById("calendarEventId").value = calendarData.eventId
                  }
                })
                .catch((calendarError) => {
                  console.error("Error creating Google Calendar event:", calendarError)
                })
            })
          }

          // Don't reset the form after successful submission to allow for additional edits
          // form.reset();
        }
      })
      .catch((error) => {
        console.error("Error during form submission:", error)
        alert("An error occurred while updating the guest.")
      })
  })
})
