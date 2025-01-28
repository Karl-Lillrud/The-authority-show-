// main.js

// Initialize i18n
initializeI18n();

// DOM Elements
const copyGuestFormBtn = document.getElementById('copyGuestForm');
const guestFormInput = document.getElementById('guestForm');
const calendarToggle = document.getElementById('googleCalendarToggle');
const inviteButton = document.getElementById('inviteButton');
const blockButton = document.getElementById('blockButton');
const podProfileForm = document.getElementById('podProfileForm');
const languageSelector = document.getElementById('language-selector');
const toast = document.getElementById('toast');

// Debounce Function to Prevent Rapid Submissions
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Copy to Clipboard Functionality for Guest Form URL
copyGuestFormBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(guestFormInput.value);
        showToast(getTranslation('notifications.guestFormCopied'));
    } catch (err) {
        showToast(getTranslation('notifications.copyFailed'));
        console.error('Copy failed:', err);
    }
});

// Google Calendar Integration Toggle
calendarToggle.addEventListener('change', async () => {
    try {
        if (calendarToggle.checked) {
            // Activate Integration
            // TODO: Implement API call to integrate Google Calendar
            showToast(getTranslation('notifications.calendarActivated'));
        } else {
            // Deactivate Integration
            // TODO: Implement API call to remove Google Calendar integration
            showToast(getTranslation('notifications.calendarDeactivated'));
        }
    } catch (err) {
        showToast(getTranslation('notifications.operationFailed'));
        console.error('Calendar toggle failed:', err);
    }
});

// Invite Button Functionality
inviteButton.addEventListener('click', async () => {
    const teamName = document.getElementById('teamName').value.trim();
    const teamEmail = document.getElementById('teamEmail').value.trim();
    const teamRole = document.getElementById('teamRole').value;

    if (!teamName || !teamEmail || !teamRole) {
        showToast(getTranslation('notifications.fillAllFields'));
        return;
    }

    try {
        // TODO: Implement invite functionality (e.g., send invite via API)
        // Example:
        // await api.sendInvite({ name: teamName, email: teamEmail, role: teamRole });

        showToast(`${getTranslation('notifications.invitationSent')} ${teamName} (${teamEmail}) as ${getTranslation(`options.${teamRole}`)}.`);
        
        // Reset form fields
        document.getElementById('teamName').value = '';
        document.getElementById('teamEmail').value = '';
        document.getElementById('teamRole').value = '';
    } catch (err) {
        showToast(getTranslation('notifications.invitationFailed'));
        console.error('Invite failed:', err);
    }
});

// Block Button Functionality
blockButton.addEventListener('click', async () => {
    const teamEmail = document.getElementById('teamEmail').value.trim();

    if (!teamEmail) {
        showToast(getTranslation('notifications.enterEmailToBlock'));
        return;
    }

    try {
        // TODO: Implement block functionality (e.g., block user via API)
        // Example:
        // await api.blockUser({ email: teamEmail });

        showToast(`${getTranslation('notifications.blocked')} ${teamEmail}.`);
        
        // Reset email field
        document.getElementById('teamEmail').value = '';
    } catch (err) {
        showToast(getTranslation('notifications.blockFailed'));
        console.error('Block failed:', err);
    }
});

// Form Submission with Validation and API Call
const handleFormSubmit = async (event) => {
    event.preventDefault();

    const form = event.target;
    let isValid = true;

    // Validate Pod Name
    const podName = document.getElementById('podName');
    if (!podName.value.trim()) {
        showValidationError('podName');
        isValid = false;
    } else {
        hideValidationError('podName');
    }

    // Validate Pod RSS
    const podRss = document.getElementById('podRss');
    if (!validateURL(podRss.value.trim())) {
        showValidationError('podRss');
        isValid = false;
    } else {
        hideValidationError('podRss');
    }

    // Validate Host Name
    const hostName = document.getElementById('hostName');
    if (!hostName.value.trim()) {
        showValidationError('hostName');
        isValid = false;
    } else {
        hideValidationError('hostName');
    }

    // Validate Calendar URL
    const calendarUrl = document.getElementById('calendarUrl');
    if (!validateURL(calendarUrl.value.trim())) {
        showValidationError('calendarUrl');
        isValid = false;
    } else {
        hideValidationError('calendarUrl');
    }

    // Validate Podcast Email
    const email = document.getElementById('email');
    if (!validateEmail(email.value.trim())) {
        showValidationError('email');
        isValid = false;
    } else {
        hideValidationError('email');
    }

    // Validate Social Media URLs
    const socialMediaFields = ['facebook', 'instagram', 'linkedin', 'twitter', 'tiktok', 'pinterest', 'website'];
    socialMediaFields.forEach(field => {
        const input = document.getElementById(field);
        if (input.value.trim() && !validateURL(input.value.trim())) {
            showValidationError(field);
            isValid = false;
        } else {
            hideValidationError(field);
        }
    });

    // Validate Guest Form URL
    const guestFormUrl = document.getElementById('guestForm');
    if (guestFormUrl.value.trim() && !validateURL(guestFormUrl.value.trim())) {
        showValidationError('guestForm');
        isValid = false;
    } else {
        hideValidationError('guestForm');
    }

    // Validate Team Section
    const teamName = document.getElementById('teamName').value.trim();
    const teamEmail = document.getElementById('teamEmail').value.trim();
    const teamRole = document.getElementById('teamRole').value;
    if (teamName || teamEmail || teamRole) {
        if (!teamName || !teamEmail || !teamRole) {
            showToast(getTranslation('notifications.fillAllTeamFields'));
            isValid = false;
        }
    }

    // If all validations pass
    if (isValid) {
        showToast(getTranslation('notifications.submitting'));

        try {
            // TODO: Implement API call to submit form data
            // Example:
            // await api.submitPodProfile(new FormData(form));

            // Simulate API call with timeout
            await new Promise(resolve => setTimeout(resolve, 2000));

            showToast(getTranslation('notifications.submissionSuccess'));
            form.reset();
            // Optionally, reset dark mode based on user preference
        } catch (err) {
            showToast(getTranslation('notifications.submissionFailed'));
            console.error('Form submission failed:', err);
        }
    } else {
        showToast(getTranslation('notifications.correctErrors'));
    }
};

// Attach Debounced Form Submission Handler
podProfileForm.addEventListener('submit', debounce(handleFormSubmit, 500));

// Language Selector Functionality
languageSelector.addEventListener('change', (event) => {
    const selectedLang = event.target.value;
    setLanguage(selectedLang);
});

// Utility Functions

function showValidationError(fieldId) {
    const input = document.getElementById(fieldId);
    input.classList.add('input-field--error');
    document.getElementById(`${fieldId}-error`).classList.remove('sr-only');
}

function hideValidationError(fieldId) {
    const input = document.getElementById(fieldId);
    input.classList.remove('input-field--error');
    document.getElementById(`${fieldId}-error`).classList.add('sr-only');
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch (_) {
        return false;  
    }
}

function showToast(message) {
    const toastContent = toast.querySelector('span');
    toastContent.textContent = message;
    toast.classList.add('show');
    toast.setAttribute('aria-label', message);

    // Hide toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Dark Mode Toggle Persistence
document.getElementById('dark-mode-toggle').addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
});

// On page load, set the theme based on localStorage
document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme');
    const toggle = document.getElementById('dark-mode-toggle');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        toggle.textContent = '☀️'; // Change icon to sun
    } else {
        toggle.textContent = '🌙'; // Change icon to moon
    }
});

// Internationalization - Language Switching
function setLanguage(lang) {
    // Update the language in i18n.js and reinitialize translations
    initializeI18n(lang);
}

// Accessibility: Ensure toast is announced by screen readers
toast.addEventListener('transitionend', () => {
    if (!toast.classList.contains('show')) {
        toast.removeAttribute('aria-label');
    }
});
