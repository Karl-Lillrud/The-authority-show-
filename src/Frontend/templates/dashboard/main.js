
// Function to load HTML components
function loadComponent(containerId, componentPath) {
    fetch(componentPath)
        .then(response => response.text())
        .then(data => {
            document.getElementById(containerId).innerHTML = data;
        })
        .catch(error => console.error(`Error loading ${componentPath}:`, error));
}

// Load Navbar and Footer
document.addEventListener('DOMContentLoaded', () => {
    loadComponent('navbar-container', 'components/navbar.html');
    loadComponent('footer-container', 'components/footer.html');
});

// Initialize i18next with HTTP Backend
import i18nextHttpBackend from 'i18next-http-backend';
i18next
    .use(i18nextHttpBackend)
    .init({
        lng: 'en', // Default language
        fallbackLng: 'en',
        debug: false,
        backend: {
            loadPath: '/locales/{{lng}}/translation.json'
        }
    }, function(err, t) {
        if (err) return console.error(err);
        updateContent();
        fetchLeaderboard();
    });

// Function to update content based on selected language
function updateContent() {
    document.querySelectorAll('[data-i18n]').forEach(function(element) {
        const key = element.getAttribute('data-i18n');
        element.textContent = i18next.t(key);
    });
}

// Function to change language
function changeLanguage(lng) {
    i18next.changeLanguage(lng, (err, t) => {
        if (err) return console.error(err);
        updateContent();
    });
}

// Event delegation for language switch buttons (since navbar is loaded dynamically)
document.addEventListener('click', function(event) {
    if (event.target.matches('.language-switcher button')) {
        const lang = event.target.id.replace('lang-', '');
        changeLanguage(lang);
    }
});

// Dark Mode Toggle Functionality
document.addEventListener('click', function(event) {
    if (event.target.matches('#dark-mode-toggle')) {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    }
});

// Persist Dark Mode Preference
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
});

// Function to fetch leaderboard data from backend
const API_GATEWAY_URL = 'https://<YOUR_API_GATEWAY_URL>'; // Replace with your actual API Gateway URL

let currentLastKey = null;
let isLoading = false;

function fetchLeaderboard() {
    if (isLoading) return; // Prevent multiple simultaneous requests
    isLoading = true;

    const tbody = document.querySelector('.leaderboard-table tbody');
    if (!currentLastKey) {
        tbody.innerHTML = '<tr><td colspan="6" class="skeleton"></td></tr>'; // Show skeleton loader
    } else {
        // Show loading indicator for pagination
        const loadingRow = document.createElement('tr');
        loadingRow.innerHTML = '<td colspan="6">Loading...</td>';
        tbody.appendChild(loadingRow);
    }

    const url = new URL(`${API_GATEWAY_URL}/leaderboard`);
    if (currentLastKey) {
        url.searchParams.append('lastKey', currentLastKey);
    }
    url.searchParams.append('limit', 10); // Adjust limit as needed

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            // 'Authorization': 'Bearer ' + localStorage.getItem('jwt_token') // Uncomment if using JWT for auth
        }
    })
    .then(response => {
        isLoading = false;
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        populateLeaderboard(data.leaderboard);
        currentLastKey = data.lastKey;
    })
    .catch(error => {
        isLoading = false;
        console.error('There was a problem with the fetch operation:', error);
        if (!currentLastKey) {
            tbody.innerHTML = '<tr><td colspan="6">Failed to load data.</td></tr>';
        } else {
            const loadingRow = tbody.querySelector('tr:last-child');
            if (loadingRow) {
                loadingRow.innerHTML = '<td colspan="6">Failed to load data.</td>';
            }
        }
    });
    
}

// Function to populate the leaderboard table
function populateLeaderboard(leaderboard) {
    const tbody = document.querySelector('.leaderboard-table tbody');
    if (!currentLastKey) {
        tbody.innerHTML = ''; // Clear existing rows if first page
    } else {
        // Remove the loading row
        const loadingRow = tbody.querySelector('tr:last-child');
        if (loadingRow) {
            loadingRow.remove();
        }
    }

    leaderboard.forEach(member => {
        const tr = document.createElement('tr');

        // Badge
        const badgeTd = document.createElement('td');
        const badgeSpan = document.createElement('span');
        badgeSpan.classList.add('badge');
        switch(member.badge) {
            case '🥇':
                badgeSpan.classList.add('gold');
                break;
            case '🥈':
                badgeSpan.classList.add('silver');
                break;
            case '🥉':
                badgeSpan.classList.add('bronze');
                break;
            default:
                badgeSpan.classList.add('clear');
        }
        badgeSpan.textContent = member.badge;
        badgeTd.appendChild(badgeSpan);
        tr.appendChild(badgeTd);

        // Name
        const nameTd = document.createElement('td');
        nameTd.textContent = member.name;
        tr.appendChild(nameTd);

        // Tasks Completed
        const tasksTd = document.createElement('td');
        tasksTd.textContent = member.tasksCompleted;
        tr.appendChild(tasksTd);

        // Total Points
        const pointsTd = document.createElement('td');
        pointsTd.textContent = member.totalPoints.toLocaleString();
        tr.appendChild(pointsTd);

        // Months Won
        const monthsTd = document.createElement('td');
        monthsTd.textContent = member.monthsWon;
        tr.appendChild(monthsTd);

        // Shadow Goal
        const shadowGoalTd = document.createElement('td');
        shadowGoalTd.textContent = member.shadowGoal;
        shadowGoalTd.classList.add('shadow-goal');
        tr.appendChild(shadowGoalTd);

        tbody.appendChild(tr);
    });

    // Function to load HTML components
function loadComponent(containerId, componentPath) {
    fetch(componentPath)
        .then(response => response.text())
        .then(data => {
            document.getElementById(containerId).innerHTML = data;
        })
        .catch(error => console.error(`Error loading ${componentPath}:`, error));
}

// Load Navbar and Footer
document.addEventListener('DOMContentLoaded', () => {
    loadComponent('navbar-container', 'components/navbar.html');
    loadComponent('footer-container', 'components/footer.html');
});

// Google Calendar Integration
function connectGoogleCalendar() {
    const userApiKey = prompt('Please enter your Google API Key to connect your calendar:');

    if (userApiKey) {
        // Validate and use the API key
        console.log('Google API Key provided:', userApiKey);
        // Store API key securely (example: localStorage)
        localStorage.setItem('googleApiKey', userApiKey);

        // Simulate API call to connect calendar
        fetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?key=${userApiKey}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Invalid API Key or permissions.');
                }
                return response.json();
            })
            .then(data => {
                alert('Calendar connected successfully!');
                console.log('Calendar Events:', data);
            })
            .catch(error => {
                alert('Failed to connect to Google Calendar. Please check your API Key.');
                console.error('Error:', error);
            });
    } else {
        const confirmRedirect = confirm('No API Key entered. Do you want to visit the Google Cloud Console to generate one?');
        if (confirmRedirect) {
            window.open('https://console.cloud.google.com/apis/credentials', '_blank');
        }
    }
}

// Event Listener for Button
const connectButton = document.querySelector('#connect-calendar-btn');
if (connectButton) {
    connectButton.addEventListener('click', connectGoogleCalendar);
}

// Update HTML content for language support
document.querySelectorAll('[data-i18n]').forEach(function (element) {
    const key = element.getAttribute('data-i18n');
    element.textContent = i18next.t(key);
});


    // Add Load More button if there are more items
    if (currentLastKey) {
        const loadMoreRow = document.createElement('tr');
        const loadMoreTd = document.createElement('td');
        loadMoreTd.colSpan = 6;
        const loadMoreButton = document.createElement('button');
        loadMoreButton.textContent = 'Load More';
        loadMoreButton.classList.add('button');
        loadMoreButton.addEventListener('click', fetchLeaderboard);
        loadMoreTd.appendChild(loadMoreButton);
        loadMoreRow.appendChild(loadMoreTd);
        tbody.appendChild(loadMoreRow);
    }
}
toggleButton.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    toggleButton.textContent = body.classList.contains('dark-mode') ? '☀️' : '🌙';
    console.log('Dark mode toggled:', body.classList.contains('dark-mode'));
});
