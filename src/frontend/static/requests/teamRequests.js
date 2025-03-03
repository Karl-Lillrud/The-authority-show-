document.addEventListener('DOMContentLoaded', function() {
  // === Insert CSS for Filter, Modal, Dropdown, etc. ===
  if (!document.getElementById('custom-styles')) {
    var styleEl = document.createElement('style');
    styleEl.id = 'custom-styles';
    styleEl.innerHTML = `
      .filters {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
        margin-top: var(--spacing-lg);
      }
      .filters label {
        font-weight: bold;
      }
      .filters select {
        padding: var(--spacing-sm);
        border-radius: 10px;
        border: none;
        background-color: var(--background-light);
        color: var(--text-color-light);
        box-shadow: -5px -5px 10px var(--light-shadow-light),
                    5px 5px 10px var(--dark-shadow-light);
        transition: box-shadow 0.3s ease;
      }
      .filters select:focus {
        outline: none;
        box-shadow: inset 3px 3px 6px var(--highlight-color),
                    inset -3px -3px 6px var(--highlight-color);
      }
      .hidden {
        display: none !important;
      }
      /* Modal common styles */
      .modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--background-light);
        padding: var(--spacing-lg);
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        display: none;
      }
      .modal.show {
        display: block;
      }
      .modal .form-group {
        margin-bottom: var(--spacing-md);
      }
      .modal .modal-actions {
        display: flex;
        gap: var(--spacing-md);
        justify-content: flex-end;
      }
      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
        display: none;
      }
      .modal-overlay.show {
        display: block;
      }
      /* Dropdown styles */
      .actions-dropdown {
        position: relative;
        display: inline-block;
      }
      .actions-dropdown .dropdown-menu {
        position: absolute;
        top: 100%;
        right: 0;
        background: var(--background-light);
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        border-radius: 5px;
        padding: 5px 0;
        z-index: 100;
        min-width: 120px;
      }
      .actions-dropdown .dropdown-menu button {
        background: none;
        border: none;
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        cursor: pointer;
      }
      .actions-dropdown .dropdown-menu button:hover {
        background-color: var(--background-dark);
      }
      /* Ensure dropdown isn't clipped by container */
      .team-table .actions-cell {
        position: relative;
        overflow: visible;
      }
    `;
    document.head.appendChild(styleEl);
  }

  // === Localization Setup ===
  function initializeLocalization() {
    i18next
      .use(i18nextHttpBackend)
      .init({
        lng: 'en',
        fallbackLng: 'en',
        backend: {
          loadPath: '/locales/{{lng}}/translation.json'
        }
      }, function(err, t) {
        if (err) return console.error(err);
        updateContent();
      });
  }
  function updateContent() {
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      const key = el.getAttribute('data-i18n');
      el.textContent = i18next.t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function(el) {
      const key = el.getAttribute('data-i18n-placeholder');
      el.setAttribute('placeholder', i18next.t(key));
    });
  }

  // === Modal Elements for Adding and Editing ===
  const addMemberBtn = document.querySelector('.add-member');
  const addMemberModal = document.getElementById('addMemberModal');
  const addCloseModalBtn = addMemberModal.querySelector('.close-btn');
  const modalOverlay = document.getElementById('modalOverlay');
  const editModal = document.getElementById('editModal'); // New Edit Member Modal
  const editMemberForm = document.getElementById('editMemberForm');
  let currentEditingRow = null;

  addMemberBtn.addEventListener('click', function() {
    addMemberModal.classList.add('show');
    addMemberModal.setAttribute('aria-hidden', 'false');
    modalOverlay.classList.add('show');
    // Clear validation errors if present
    ['name-error', 'role-error', 'email-error', 'phone-error'].forEach(function(id) {
      const el = document.getElementById(id);
      if(el) {
        el.textContent = "";
        el.classList.add('sr-only');
      }
    });
  });
  addCloseModalBtn.addEventListener('click', function() {
    addMemberModal.classList.remove('show');
    addMemberModal.setAttribute('aria-hidden', 'true');
    modalOverlay.classList.remove('show');
  });
 

  // === Add New Team Member ===
  document.getElementById('addMemberForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const member = {
      name: document.getElementById('memberName').value,
      role: document.getElementById('memberRole').value,
      email: document.getElementById('memberEmail').value,
      phone: document.getElementById('memberPhone').value
    };

    const isNameValid = validateName(member.name);
    const isRoleValid = validateRole(member.role);
    const isEmailValid = validateEmail(member.email);
    const isPhoneValid = validatePhone(member.phone);

    if (isNameValid && isRoleValid && isEmailValid && isPhoneValid) {
      fetch('/add_team', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(member)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        showToast(data.message);
        fetchTeamMembers();
        document.getElementById('addMemberForm').reset();
        addMemberModal.classList.remove('show');
        addMemberModal.setAttribute('aria-hidden', 'true');
        modalOverlay.classList.remove('show');
      })
      .catch(error => console.error('Error adding team member:', error));
    }
  });

  // === Fetch and Display Team Members ===
  function fetchTeamMembers() {
    fetch('/get_team')
      .then(response => response.json())
      .then(data => {
        const tbody = document.querySelector('.team-table tbody');
        tbody.innerHTML = '';
        data.forEach(member => {
          const newRow = document.createElement('tr');
          newRow.setAttribute('data-id', member._id); // Store member's unique ID
          newRow.innerHTML = `
            <td>${member.Name}</td>
            <td>${member.Role}</td>
            <td><a href="mailto:${member.Email}" class="email-link">${member.Email}</a></td>
            <td>${member.Phone || ''}</td>
            <td>0</td>
            <td>
              <span class="status active" data-i18n="status.active">Active</span>
            </td>
            <td class="actions-cell">
              <div class="actions-dropdown">
                <button class="icon-button action-btn cog" aria-label="Member Actions">⚙️</button>
                <div class="dropdown-menu hidden">
                  <button class="dropdown-item edit-member">Edit Member</button>
                  <button class="dropdown-item delete-member">Delete Member</button>
                </div>
              </div>
            </td>
          `;
          tbody.appendChild(newRow);
          attachRowActions(newRow);
        });
      })
      .catch(error => console.error('Error fetching team members:', error));
  }
  fetchTeamMembers();

  // === Validation Functions ===
  function validateName(nameValue) {
    const valid = nameValue.trim().length > 0;
    const errorEl = document.getElementById('name-error');
    if (valid) {
      errorEl.classList.add('sr-only');
    } else {
      errorEl.textContent = "Please put in a valid name.";
      errorEl.classList.remove('sr-only');
    }
    return valid;
  }
  function validateRole(roleValue) {
    const valid = roleValue.trim().length > 0;
    const errorEl = document.getElementById('role-error');
    if (valid) {
      errorEl.classList.add('sr-only');
    } else {
      errorEl.textContent = "Please put in a valid role.";
      errorEl.classList.remove('sr-only');
    }
    return valid;
  }
  function validateEmail(emailValue) {
    const re = /\S+@\S+\.\S+/;
    const valid = re.test(emailValue);
    const errorEl = document.getElementById('email-error');
    if (valid) {
      errorEl.classList.add('sr-only');
    } else {
      errorEl.textContent = "Please put in a valid email.";
      errorEl.classList.remove('sr-only');
    }
    return valid;
  }
  function validatePhone(phoneValue) {
    const re = /^\+?[0-9]{7,15}$/;
    const valid = phoneValue === "" || re.test(phoneValue);
    const errorEl = document.getElementById('phone-error');
    if (valid) {
      errorEl.classList.add('sr-only');
    } else {
      errorEl.textContent = "Please put in a valid phone.";
      errorEl.classList.remove('sr-only');
    }
    return valid;
  }
  function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(function() {
      toast.classList.remove('show');
    }, 3000);
  }

  // === Search Functionality ===
  const searchInput = document.getElementById('search');
  searchInput.addEventListener('input', function(event) {
    const searchValue = event.target.value.toLowerCase();
    const currentRows = document.querySelectorAll('.team-table tbody tr');
    currentRows.forEach(function(row) {
      row.style.display = row.textContent.toLowerCase().includes(searchValue) ? '' : 'none';
    });
  });

  // === Attach Row Actions (Edit & Delete) ===
  function attachRowActions(row) {
    const dropdown = row.querySelector('.actions-dropdown');
    const cogButton = dropdown.querySelector('.action-btn.cog');
    const dropdownMenu = dropdown.querySelector('.dropdown-menu');
    const editBtn = dropdown.querySelector('.dropdown-item.edit-member');
    const deleteBtn = dropdown.querySelector('.dropdown-item.delete-member');

    cogButton.addEventListener('click', function(event) {
      event.stopPropagation();
      dropdownMenu.classList.toggle('hidden');
    });
    document.addEventListener('click', function() {
      dropdownMenu.classList.add('hidden');
    });
    dropdownMenu.addEventListener('click', function(event) {
      event.stopPropagation();
    });

    // Edit Member – Open edit modal with pre-filled info
    editBtn.addEventListener('click', function() {
      currentEditingRow = row;
      document.getElementById('editMemberName').value = row.children[0].textContent.trim();
      document.getElementById('editMemberRole').value = row.children[1].textContent.trim();
      const emailText = row.children[2].querySelector('a').textContent.trim();
      document.getElementById('editMemberEmail').value = emailText;
      document.getElementById('editMemberPhone').value = row.children[3].textContent.trim();
      editModal.classList.add('show');
      editModal.setAttribute('aria-hidden', 'false');
      modalOverlay.classList.add('show');
      dropdownMenu.classList.add('hidden');
    });

    // Delete Member – Call DELETE endpoint and remove row
    deleteBtn.addEventListener('click', function() {
      const teamId = row.getAttribute('data-id');
      if (confirm("Are you sure you want to delete this team member?")) {
        fetch(`/delete_team/${teamId}`, { method: 'DELETE' })
          .then(response => response.json())
          .then(data => {
            showToast(data.message);
            row.remove();
          })
          .catch(error => console.error("Error deleting team member:", error));
      }
      dropdownMenu.classList.add('hidden');
    });
  }

  // === Edit Member Form Submission (PUT) ===
  editMemberForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const updatedMember = {
      name: document.getElementById('editMemberName').value,
      role: document.getElementById('editMemberRole').value,
      email: document.getElementById('editMemberEmail').value,
      phone: document.getElementById('editMemberPhone').value
    };
    const teamId = currentEditingRow.getAttribute('data-id');
    fetch(`/update_team/${teamId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(updatedMember)
    })
    .then(response => response.json())
    .then(data => {
      showToast(data.message);
      // Update row with new information
      currentEditingRow.children[0].textContent = updatedMember.name;
      currentEditingRow.children[1].textContent = updatedMember.role;
      currentEditingRow.children[2].innerHTML = `<a href="mailto:${updatedMember.email}" class="email-link">${updatedMember.email}</a>`;
      currentEditingRow.children[3].textContent = updatedMember.phone;
      editModal.classList.remove('show');
      editModal.setAttribute('aria-hidden', 'true');
      modalOverlay.classList.remove('show');
      currentEditingRow = null;
    })
    .catch(error => console.error("Error updating team member:", error));
  });

  // === Close Button for Edit Modal ===
  const editModalCloseBtn = document.getElementById('editModalClose');
  editModalCloseBtn.addEventListener('click', function() {
    editModal.classList.remove('show');
    editModal.setAttribute('aria-hidden', 'true');
    modalOverlay.classList.remove('show');
    currentEditingRow = null;
  });

  // === Filter Menu Handler ===
  const filterButton = document.getElementById('filter');
  let filterMenu;
  filterButton.addEventListener('click', function() {
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
      filterButton.parentNode.appendChild(filterMenu);
      const roleFilter = document.getElementById('filter-role');
      const statusFilter = document.getElementById('filter-status');
      const taskFilter = document.getElementById('filter-task');

      roleFilter.addEventListener('change', filterRows);
      statusFilter.addEventListener('change', filterRows);
      taskFilter.addEventListener('change', filterRows);

      function filterRows() {
        const selectedRole = roleFilter.value;
        const selectedStatus = statusFilter.value;
        const selectedTaskFilter = taskFilter.value;
        const rows = Array.from(document.querySelectorAll('.team-table tbody tr'));

        let filteredRows = rows.filter(row => {
          const role = row.querySelector('td:nth-child(2)').textContent.trim();
          const status = row.querySelector('.status').textContent.trim();
          return (!selectedRole || role === selectedRole) &&
                 (!selectedStatus || status === selectedStatus);
        });

        if (selectedTaskFilter === 'most') {
          filteredRows.sort((a, b) => {
            const aCount = parseInt(a.querySelector('td:nth-child(5)').textContent.trim(), 10);
            const bCount = parseInt(b.querySelector('td:nth-child(5)').textContent.trim(), 10);
            return bCount - aCount;
          });
        } else if (selectedTaskFilter === 'least') {
          filteredRows.sort((a, b) => {
            const aCount = parseInt(a.querySelector('td:nth-child(5)').textContent.trim(), 10);
            const bCount = parseInt(b.querySelector('td:nth-child(5)').textContent.trim(), 10);
            return aCount - bCount;
          });
        }

        const tbody = document.querySelector('.team-table tbody');
        rows.forEach(row => {
          row.style.display = filteredRows.includes(row) ? '' : 'none';
        });
        filteredRows.forEach(row => {
          tbody.appendChild(row);
        });
      }
    } else {
      filterMenu.classList.toggle('hidden');
    }
  });

  initializeLocalization();
});
