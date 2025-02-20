// Initialize Localization with i18next
function initializeLocalization() {

    i18next
      .use(i18nextHttpBackend)
      .init({
        lng: 'en', // Default language
        fallbackLng: 'en',
        backend: {
          loadPath: '/locales/{{lng}}/translation.json'
        }
      }, function(err, t) {

        if (err) return console.error(err);
        updateContent();

      });
  }
  
  // Function to update content based on selected language
  function updateContent() {

    document.querySelectorAll('[data-i18n]').forEach(function(element) {

      const key = element.getAttribute('data-i18n');

      element.textContent = i18next.t(key);

    });
  
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function(element) {

      const key = element.getAttribute('data-i18n-placeholder');

      element.setAttribute('placeholder', i18next.t(key));

    });

  }
  
  // Function to change language
  function changeLanguage(lng) {

    i18next.changeLanguage(lng, (err, t) => {

      if (err) return console.error(err);

      updateContent();

    });

  }
  
  // Event listeners for language switch buttons
  function setupLanguageSwitcher() {

    document.querySelectorAll('.language-switcher button').forEach(button => {

      button.addEventListener('click', () => {

        const lang = button.id.replace('lang-', '');

        changeLanguage(lang);

      });

    });

  }
  
  // Modal Toggle Functionality
  const addMemberBtn = document.querySelector('.add-member');
  const addMemberModal = document.getElementById('addMemberModal');
  const closeModalBtn = document.querySelector('.close-btn');
  
  // Close modal when clicking outside the modal content
  window.addEventListener('click', (event) => {

    if (event.target === addMemberModal) {

      addMemberModal.classList.remove('show');
      addMemberModal.setAttribute('aria-hidden', 'true');

    }

  });
  
  addMemberBtn.addEventListener('click', () => {

    addMemberModal.classList.add('show');
    addMemberModal.setAttribute('aria-hidden', 'false');

  });
  
  closeModalBtn.addEventListener('click', () => {

    addMemberModal.classList.remove('show');
    addMemberModal.setAttribute('aria-hidden', 'true');

  });
  
  // Dark Mode Toggle Functionality
  const themeToggle = document.getElementById('theme-toggle');
  
  themeToggle.addEventListener('change', function() {

    if(this.checked) {

      document.body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');

    } else {

      document.body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');

    }

  });
  
  // On page load, set the theme based on localStorage
  document.addEventListener('DOMContentLoaded', () => {

    initializeLocalization();
    setupLanguageSwitcher();
  
    const savedTheme = localStorage.getItem('theme');

    if(savedTheme === 'dark') {

      document.body.classList.add('dark-mode');
      themeToggle.checked = true;

    }

  });
  
  // Form Submission with Validation
  document.getElementById('addMemberForm').addEventListener('submit', function(event) {

    event.preventDefault();
  
    const name = document.getElementById('memberName');
    const role = document.getElementById('memberRole');
    const email = document.getElementById('memberEmail');
    const phone = document.getElementById('memberPhone');
  
    let isValid = true;
  
    // Name Validation
    if (!validateName(name.value)) {

      name.classList.add('input-field--error');
      document.getElementById('name-error').classList.remove('sr-only');
      isValid = false;

    } else {

      name.classList.remove('input-field--error');
      document.getElementById('name-error').classList.add('sr-only');

    }
  
    // Role Validation
    if (!validateRole(role.value)) {

      role.classList.add('input-field--error');
      document.getElementById('role-error').classList.remove('sr-only');
      isValid = false;

    } else {

      role.classList.remove('input-field--error');
      document.getElementById('role-error').classList.add('sr-only');

    }
  
    // Email Validation
    if (!validateEmail(email.value)) {

      email.classList.add('input-field--error');
      document.getElementById('email-error').classList.remove('sr-only');
      isValid = false;

    } else {

      email.classList.remove('input-field--error');
      document.getElementById('email-error').classList.add('sr-only');

    }
  
    // Phone Validation
    if (phone.value && !validatePhone(phone.value)) {

      phone.classList.add('input-field--error');
      document.getElementById('phone-error').classList.remove('sr-only');
      isValid = false;

    } else {

      phone.classList.remove('input-field--error');
      document.getElementById('phone-error').classList.add('sr-only');

    }
  
    if (isValid) {

      // Show loading state (optional)
      const submitButton = this.querySelector('.submit-btn');
      submitButton.textContent = i18next.t('buttons.submitting');
  
      // Simulate API call
      setTimeout(() => {

        submitButton.textContent = i18next.t('buttons.submit');
        showToast(i18next.t('notifications.memberAdded'));
        this.reset();
        addMemberModal.classList.remove('show');
        addMemberModal.setAttribute('aria-hidden', 'true');
        // TODO: Add member to the table dynamically or refresh data

      }, 2000);

    }

  });
  
  // Validation Functions
  function validateEmail(email) {

    const re = /\S+@\S+\.\S+/;
    return re.test(email);

  }
  
  function validateName(name) {

    return name.trim().length > 0;

  }
  
  function validateRole(role) {

    return role.trim().length > 0;

  }
  
  function validatePhone(phone) {

    const re = /^\+?[0-9]{7,15}$/;
    return re.test(phone);

  }
  
  // Toast Notification Function
  function showToast(message) {

    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
  
    setTimeout(() => {

      toast.classList.remove('show');

    }, 3000);

  }
  
  // Example Function to Add Member to Table (to be implemented)
  function addMemberToTable(member) {

    const tbody = document.querySelector('.team-table tbody');
    const row = document.createElement('tr');
  
    row.innerHTML = `
      <td>${sanitize(member.name)}</td>
      <td>${sanitize(member.role)}</td>
      <td>${sanitize(member.email)}</td>
      <td>${sanitize(member.phone) || '-'}</td>
      <td>${sanitize(member.tasks)}</td>
      <td>
        <span class="status ${member.status.toLowerCase()}" data-i18n="status.${member.status.toLowerCase()}">${member.status}</span>
      </td>
      <td>
        <button class="action-btn edit" aria-label="Edit Member">
          <i class="fas fa-edit"></i>
        </button>
        <button class="action-btn disable" aria-label="Disable Member">
          <i class="fas fa-user-slash"></i>
        </button>
        <button class="action-btn view-tasks" aria-label="View Tasks">
          <i class="fas fa-tasks"></i>
        </button>
      </td>
    `;
  
    tbody.appendChild(row);

  }
  
  // Sanitize Function to Prevent XSS
  function sanitize(str) {

    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;

  }
  document.addEventListener('DOMContentLoaded', () => {

    const tableRows = document.querySelectorAll('.team-table tbody tr');
    const searchInput = document.getElementById('search');
  
    // Search functionality
    searchInput.addEventListener('input', (event) => {

      const searchValue = event.target.value.toLowerCase();
      tableRows.forEach((row) => {

        const rowText = row.textContent.toLowerCase();
        row.style.display = rowText.includes(searchValue) ? '' : 'none';

      });

    });
  
    // Action buttons
    tableRows.forEach((row) => {

      const editButton = row.querySelector('.edit');
      const disableButton = row.querySelector('.disable');
      const viewTasksButton = row.querySelector('.view-tasks');
  
      // Edit button functionality
      editButton.addEventListener('click', () => {

        alert('Edit functionality not implemented yet.');

      });
  
      // Disable button functionality
      disableButton.addEventListener('click', () => {

        const statusSpan = row.querySelector('.status');
        if (statusSpan.textContent.trim() === 'Active') {

          statusSpan.textContent = 'Inactive';
          statusSpan.classList.remove('active');
          statusSpan.classList.add('inactive');

        } else {

          statusSpan.textContent = 'Active';
          statusSpan.classList.remove('inactive');
          statusSpan.classList.add('active');

        }

      });
  
      // View tasks button functionality
      viewTasksButton.addEventListener('click', () => {

        alert('View tasks functionality not implemented yet.');

      });

    });

  });
  document.addEventListener('DOMContentLoaded', () => {

  const tableRows = document.querySelectorAll('.team-table tbody tr');
  const searchInput = document.getElementById('search');
  const filterButton = document.getElementById('filter');
  let filterMenu;

  // Create and append filter dropdown menu
  filterButton.addEventListener('click', () => {

    if (!filterMenu) {

      filterMenu = document.createElement('div');
      filterMenu.innerHTML = `
      <div class="filters">
        <label for="filter-role">Role:</label>
        <select id="filter-role">
          <option value="">All</option>
          <option value="Admin">Admin</option>
          <option value="Editor">Editor</option>
          <option value="Team Member">Team Member</option>
        </select>
        <label for="filter-status">Status:</label>
        <select id="filter-status">
          <option value="">All</option>
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
        </select>
        <label for="filter-task">Task Count:</label>
        <select id="filter-task">
          <option value="">All</option>
          <option value="most">Most Tasks</option>
          <option value="least">Least Tasks</option>
        </select>
      </div>
    `;

      filterMenu.classList.add('filter-menu-wrapper');
      filterButton.parentNode.appendChild(filterMenu);

      // Add event listeners for filter logic
      const roleFilter = document.getElementById('filter-role');
      const statusFilter = document.getElementById('filter-status');
      const taskFilter = document.getElementById('filter-task');

      function filterRows() {

        const selectedRole = roleFilter.value;
        const selectedStatus = statusFilter.value;
        const selectedTaskFilter = taskFilter.value;
        

        tableRows.forEach(row => {

          const role = row.querySelector('td:nth-child(2)').textContent.trim();
          const status = row.querySelector('.status').textContent.trim();
          const taskCount = parseInt(row.querySelector('td:nth-child(5)').textContent.trim());

          const matchesRole = !selectedRole || role === selectedRole;
          const matchesStatus = !selectedStatus || status === selectedStatus;
          const matchesTask = !selectedTaskFilter ||
            (selectedTaskFilter === 'most' && taskCount >= 5) ||
            (selectedTaskFilter === 'least' && taskCount < 5);

          if (matchesRole && matchesStatus && matchesTask) {

            row.style.display = '';

          } else {

            row.style.display = 'none';

          }

        });

      }

      // Attach filter change event
      roleFilter.addEventListener('change', filterRows);
      statusFilter.addEventListener('change', filterRows);
      taskFilter.addEventListener('change', filterRows);

    } else {

      // Toggle visibility of the menu
      filterMenu.classList.toggle('hidden');

    }

  });

  // Search functionality
  searchInput.addEventListener('input', () => {

    const searchTerm = searchInput.value.toLowerCase();
    tableRows.forEach(row => {

      const rowText = row.textContent.toLowerCase();
      row.style.display = rowText.includes(searchTerm) ? '' : 'none';

    });

  });

});

// script.js

document.addEventListener('DOMContentLoaded', () => {

    const editButtons = document.querySelectorAll('.action-btn.edit');

    editButtons.forEach(button => {

        button.addEventListener('click', (event) => {

            const row = event.target.closest('tr');

            if (!row) return;

            const nameCell = row.querySelector('td:nth-child(1)');
            const roleCell = row.querySelector('td:nth-child(2)');
            const emailCell = row.querySelector('td:nth-child(3)');
            const phoneCell = row.querySelector('td:nth-child(4)');

            const currentName = nameCell.textContent;
            const currentRole = roleCell.textContent;
            const currentEmail = emailCell.textContent;
            const currentPhone = phoneCell.textContent;

            const modal = document.getElementById('addMemberModal');
            const form = document.getElementById('addMemberForm');

            modal.classList.add('show');

            form.querySelector('#memberName').value = currentName;
            form.querySelector('#memberRole').value = currentRole;
            form.querySelector('#memberEmail').value = currentEmail;
            form.querySelector('#memberPhone').value = currentPhone;

            form.addEventListener('submit', (e) => {

                e.preventDefault();

                nameCell.textContent = form.querySelector('#memberName').value;
                roleCell.textContent = form.querySelector('#memberRole').value;
                emailCell.textContent = form.querySelector('#memberEmail').value;
                phoneCell.textContent = form.querySelector('#memberPhone').value;

                modal.classList.remove('show');
                form.reset();

            });

            const closeButton = form.querySelector('.close-btn');
            closeButton.addEventListener('click', () => {

                modal.classList.remove('show');
                form.reset();

            });

        });

    });

});

// script.js

document.addEventListener('DOMContentLoaded', () => {

    const disableButtons = document.querySelectorAll('.action-btn.disable');

    disableButtons.forEach(button => {

        button.addEventListener('click', (event) => {

            const row = event.target.closest('tr');

            if (!row) return;

            const confirmation = confirm("Are you sure you want to remove this member?");

            if (confirmation) {

                row.remove();

            }

        });

    });
    
});

  
  // Optional: Fetch and Populate Team Members from API
  /*
  function fetchTeamMembers() {
    fetch('/api/team-members')
      .then(response => response.json())
      .then(data => {
        data.forEach(member => addMemberToTable(member));
      })
      .catch(error => console.error('Error fetching team members:', error));
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    // Existing initialization code...
    fetchTeamMembers();
  });
  */
  