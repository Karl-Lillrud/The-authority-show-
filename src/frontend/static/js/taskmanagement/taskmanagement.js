<<<<<<< HEAD:src/frontend/templates/dashboard/taskmanagement.html
{% extends "dashboard/components/base.html" %} {% block title %}Podcast Task
Management{% endblock %} {% block content %}
<!-- Guest Selection Popup -->
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='css/taskmanagement.css') }}"
/>

<!-- Back Arrow -->
<a
  href="{{ url_for('dashboard_bp.dashboard') }}"
  class="back-arrow"
  id="dashboard-button"
  >&#8592; Dashboard</a
>

<div class="task-header-buttons" style="justify-content: center">
  <div class="button-group">
    <button id="load-default-btn" onclick="openDefaultTasksPopup()">
      Add Default Tasks
    </button>
    <button id="add-task-btn" onclick="openTaskModal()">
      + Add Custom Task
    </button>
  </div>

  <!-- Wrapper för att flytta Select Episode till höger -->
  <div class="dropdown-wrapper">
    <div class="dropdown view-episode-dropdown">
      <button class="dropbtn" onclick="viewEpisodes()">
        View Episodes
      </button>
    </div>
  </div>
</div>

<!-- Add the selected-guest element here -->
<div id="selected-guest" data-guest-id="" style="display: none;"></div>

<div class="task-list-container">
  <!-- Current Tasks Header -->
  <h3 class="current-tasks-header">Pod Tasks</h3>

  <!-- Ordered Task List -->
  <ol id="task-list" class="sortable responsive-task-list">
    <!-- Dynamically injected tasks will appear here -->
  </ol>

  <!-- Add Tasks to Episode and Back Button Container -->
  <div class="add-tasks-button-container">
    <div class="dropdown add-tasks-dropdown">
      <button class="dropbtn" onclick="openAddTasksEpisodePopup()">
        Add Tasks To Episode
      </button>
      <div class="dropdown-content" id="add-tasks-episode-dropdown"></div>
      <!-- Episodes will be dynamically populated here -->
    </div>
  </div>
</div>

<!-- Task Modal -->
<div id="task-modal" class="popup" style="display: none">
  <div class="popup-content">
    <span class="close-btn" onclick="closeModal()">&times;</span>
    <h2 id="modal-title">Create New Task</h2>

    <label for="task-name">Task Name:</label>
    <input type="text" id="task-name" placeholder="Enter task name" />

    <label for="task-dependencies">Dependent on Other Task(s):</label>
    <select id="task-dependencies" multiple>
      <!-- Options dynamically populated -->
    </select>

    <label for="task-type">Task Type & Action:</label>
    <select id="task-type">
      <option value="manual">Manual</option>
      <option value="email">Automated - Email</option>
      <option value="system">Automated - System Action</option>
      <option value="ai">Automated - AI Script</option>
    </select>

    <div id="action-details" class="hidden">
      <label for="action-details-input">Action Details:</label>
      <input
        type="text"
        id="action-details-input"
        placeholder="Enter details"
      />
    </div>

    <label for="due-time">Due Time Since Recording Date:</label>
    <input type="text" id="due-time" placeholder="Enter days" />

    <label for="task-description">Task Description:</label>
    <textarea id="task-description" placeholder="Enter task details"></textarea>

    <label for="action-link">Action Link:</label>
    <input type="text" id="action-link" placeholder="Enter external link" />
    <input type="text" id="action-link-desc" placeholder="Describe the link" />

    <label>
      <input type="checkbox" id="submission-required" /> Require Information
      Submission
    </label>

    <div class="modal-buttons">
      <button id="save-task-btn">Save Task</button>
      <button class="cancel-btn" onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Default Tasks Popup -->
<div id="default-tasks-popup" class="popup" style="display: none">
  <div class="popup-content">
    <span class="close-btn" onclick="closeDefaultTasksPopup()">&times;</span>
    <h2>Select Default Tasks</h2>
    <button id="select-all-default-btn" onclick="selectAllDefaultTasks()">
      Select All
    </button>
    <div id="default-tasks-list">
      <!-- Default tasks will be dynamically populated -->
    </div>
    <div class="modal-buttons">
      <button id="add-default-tasks-btn" onclick="addSelectedDefaultTasks()">
        Add Selected Tasks
      </button>
      <button class="cancel-btn" onclick="closeDefaultTasksPopup()">
        Cancel
      </button>
    </div>
  </div>
</div>

<!-- Episodes Popup -->
<div id="episodes-popup" class="popup" style="display: none">
  <div class="popup-content">
    <h2>Select Episode</h2>
    <div id="episodes-list">
      <!-- Episodes will be dynamically populated here -->
    </div>
    <div class="modal-buttons" style="justify-content: flex-end">
      <button class="cancel-btn" onclick="closeEpisodesPopup()">Cancel</button>
    </div>
  </div>
</div>

<div id="add-tasks-episode-popup" class="popup" style="display: none">
  <div class="popup-content">
    <h2>Add tasks to</h2>
    <div id="add-tasks-episode-list">
      <!-- Episodes will be dynamically populated here -->
    </div>
    <div class="modal-buttons" style="justify-content: flex-end">
      <button class="cancel-btn" onclick="closeAddTasksEpisodePopup()">
        Cancel
      </button>
    </div>
  </div>
</div>

<!-- Add this script tag to load SortableJS library -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>

<script type="module">
  import {
    fetchTasks,
    fetchTask,
    saveTask,
    updateTask,
    deleteTask,
    fetchDefaultTasks,
    deleteDefaultTask,
    addSelectedDefaultTasks,
    addTasksToEpisode,
    fetchLocalDefaultTasks
  } from "{{ url_for('static', filename='requests/podtaskRequest.js') }}";
  import {
    fetchEpisodes,
    viewEpisodeTasks,
  } from "{{ url_for('static', filename='requests/episodeRequest.js') }}";

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("add-task-form");

    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent the form from submitting the traditional way

        // Collect form data
        const taskName = document.getElementById("task-name").value.trim();
        const taskDescription = document
          .getElementById("task-description")
          .value.trim();
        const dueTime = document.getElementById("due-time").value.trim();
        const actionLink = document.getElementById("action-link").value.trim();
        const actionLinkDesc = document
          .getElementById("action-link-desc")
          .value.trim();
        const submissionRequired = document.getElementById(
          "submission-required"
        ).checked;

        const data = {
          taskName,
          taskDescription,
          dueTime,
          actionLink,
          actionLinkDesc,
          submissionRequired
        };

        saveTask(data)
          .then((response) => {
            if (response.error) {
              alert(`Error: ${response.error}`);
            } else {
              alert("Task added successfully!");
              window.location.href = response.redirect_url;
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("There was an error with the registration process.");
          });
      });
    }

    // Fetch tasks on page load
    fetchTasks()
      .then((tasks) => {
        const taskList = document.getElementById("task-list");
        taskList.innerHTML = ""; // Clear existing tasks

        tasks.forEach((task) => {
          let li = document.createElement("li");
          li.classList.add("task-item");
          li.innerHTML = `
            <div class="task-details">
              <span class="task-name">${task.taskname}</span>
              <div class="task-actions">
                <button class="edit-btn" onclick="editTask('${task._id}')">Edit</button>
                <button class="delete-btn" onclick="deleteTask('${task._id}')">Delete</button>
              </div>
            </div>
          `;
          taskList.appendChild(li);
        });
      })
      .catch((error) => {
        console.error("Error fetching tasks:", error);
        alert("Failed to fetch tasks.");
      });

  });

  window.editTask = async function (taskId) {
    const task = await fetchTask(taskId);

    // Pre-fill the modal fields with fetched task data
    document.getElementById("task-name").value =
      task.taskname || task.task_name;
    document.getElementById("task-description").value = task.Description || "";
    document.getElementById("due-time").value = task.DayCount || "";
    document.getElementById("action-link").value = task.ActionUrl || "";
    document.getElementById("action-link-desc").value = task.UrlDescribe || "";
    document.getElementById("submission-required").checked =
      task.SubimissionReq || false;

    // Set modal title and update button action
    document.getElementById("modal-title").innerText = "Edit Task";
    document.getElementById("task-modal").style.display = "flex";
    document
      .getElementById("save-task-btn")
      .setAttribute("onclick", `updateTask('${task._id}')`);
  };

  window.updateTask = async function (taskId) {
    const taskName = document.getElementById("task-name").value.trim();
    const taskDescription = document
      .getElementById("task-description")
      .value.trim();
    const dueTime = document.getElementById("due-time").value.trim();
    const actionLink = document.getElementById("action-link").value.trim();
    const actionLinkDesc = document
      .getElementById("action-link-desc")
      .value.trim();
    const submissionRequired = document.getElementById(
      "submission-required"
    ).checked;

    const updatedTask = {
      taskname: taskName,
      Description: taskDescription,
      DayCount: parseInt(dueTime) || 0,
      actionurl: actionLink,
      externalurl: actionLinkDesc,
      submission: submissionRequired ? "Required" : "Optional"
    };

    await updateTask(taskId, updatedTask);
    closeModal();
    fetchTasks(); // Refresh the task list to reflect changes
  };

  window.deleteTask = async function (taskId) {
    await deleteTask(taskId);
    fetchTasks(); // Refresh tasks
  };

  function closeModal() {
    document.getElementById("task-modal").style.display = "none";
  }

  // Define the selectGuest function
  window.selectGuest = function (guestId, guestName, guestImage) {
    document.getElementById("selected-guest").textContent = guestName;
    document.getElementById("selected-guest").dataset.guestId = guestId; // Set guestId
    const guestImageElement = document.getElementById("selected-guest-image");
    guestImageElement.src = guestImage;
    guestImageElement.style.display = "block";
    document.getElementById("guest-popup").style.display = "none";
    document.getElementById("task-management").style.display = "block";

    // Load and display default tasks
    fetch(
      "{{ url_for('static', filename='defaulttaskdata/default_tasks.json') }}"
    )
      .then((response) => response.json())
      .then((defaultTasks) => {
        const taskList = document.getElementById("task-list");
        taskList.innerHTML = ""; // Clear existing tasks

        defaultTasks.forEach((task) => {
          let li = document.createElement("li");
          li.classList.add("task-item");
          li.innerHTML = `
            <div class="task-details">
              <span class="task-name">${task}</span>
              <div class="task-actions">
                <button class="edit-btn" onclick="editTask('${task._id}')">Edit</button>
                <button class="delete-btn" onclick="deleteTask('${task._id}')">Delete</button>
              </div>
            </div>
          `;
          taskList.appendChild(li);
        });
      })
      .catch((error) => {
        console.error("Error loading default tasks:", error);
        alert("Failed to load default tasks.");
      });
  };

  window.viewEpisodes = async function () {
    const guestId = document.getElementById("selected-guest").dataset.guestId;
    const episodes = await fetchEpisodes(guestId);
    const episodesList = document.getElementById("episodes-list");
    episodesList.innerHTML = ""; // Clear existing episodes

    if (episodes.length === 0) {
      let noEpisodesItem = document.createElement("p");
      noEpisodesItem.textContent = "No episodes found";
      episodesList.appendChild(noEpisodesItem);
    } else {
      episodes.forEach((episode) => {
        let episodeItem = document.createElement("a");
        episodeItem.href = "#";
        episodeItem.textContent = episode.title;
        episodeItem.onclick = async (event) => {
          event.preventDefault();
          await viewEpisodeTasks(episode._id);
        };
        episodesList.appendChild(episodeItem);
      });
    }

    document.getElementById("episodes-popup").style.display = "flex";
  };

  window.viewEpisodeTasks = async function (episodeId) {
    const tasks = await fetchEpisodeTasks(episodeId);
    const taskList = document.getElementById("task-list");
    taskList.innerHTML = ""; // Clear existing tasks

    if (tasks.length === 0) {
      let noTasksItem = document.createElement("li");
      noTasksItem.classList.add("task-item");
      noTasksItem.textContent = "No tasks found";
      taskList.appendChild(noTasksItem);
    } else {
      tasks.forEach((task) => {
        let li = document.createElement("li");
        li.classList.add("task-item");
        li.innerHTML = `
          <div class="task-details">
            <span class="task-name">${task.taskname}</span>
            <div class="task-actions">
              <button class="edit-btn" onclick="editTask('${task._id}')">Edit</button>
              <button class="delete-btn" onclick="deleteTask('${task._id}')">Delete</button>
            </div>
          </div>
        `;
        taskList.appendChild(li);
      });
    }

    document.getElementById("episodes-popup").style.display = "none";
  };

  window.openTaskModal = function () {
    document.getElementById("task-modal").style.display = "flex";
  };

  window.closeModal = function () {
    document.getElementById("task-modal").style.display = "none";
  };

  window.openDefaultTasksPopup = async function () {
    document.getElementById("default-tasks-popup").style.display = "flex";

    const defaultTasks = await fetchLocalDefaultTasks();
    const defaultTasksList = document.getElementById("default-tasks-list");
    defaultTasksList.innerHTML = ""; // Clear existing tasks

    defaultTasks.forEach((task, index) => {
      let div = document.createElement("div");
      div.classList.add("default-task-item");
      div.innerHTML = `
        <span>${task}</span>
        <input type="checkbox" id="default-task-${index}" value="${task}">
      `;
      defaultTasksList.appendChild(div);
    });
  };

  window.closeDefaultTasksPopup = function () {
    document.getElementById("default-tasks-popup").style.display = "none";
  };

  window.closeEpisodesPopup = function () {
    document.getElementById("episodes-popup").style.display = "none";
  };

  window.openAddTasksEpisodePopup = async function () {
    const guestId = document.getElementById("selected-guest").dataset.guestId;
    const episodes = await fetchEpisodes(guestId);
    const episodesList = document.getElementById("add-tasks-episode-list");
    episodesList.innerHTML = ""; // Clear existing episodes

    if (episodes.length === 0) {
      let noEpisodesItem = document.createElement("p");
      noEpisodesItem.textContent = "No episodes found";
      episodesList.appendChild(noEpisodesItem);
    } else {
      episodes.forEach((episode) => {
        let episodeItem = document.createElement("a");
        episodeItem.href = "#";
        episodeItem.textContent = episode.title;
        episodeItem.onclick = async (event) => {
          event.preventDefault();
          await addTasksToEpisode(episode._id, guestId, []); // Pass an empty array for tasks for now
        };
        episodesList.appendChild(episodeItem);
      });
    }

    document.getElementById("add-tasks-episode-popup").style.display = "flex";
  };

  window.closeAddTasksEpisodePopup = function () {
    document.getElementById("add-tasks-episode-popup").style.display = "none";
  };
</script>

<script type="module" src="{{ url_for('static', filename='requests/episodeRequest.js') }}"></script>
<script type="module" src="{{ url_for('static', filename='js/taskManagement.js') }}"></script>

{% endblock %}
=======
import {
    fetchTasks,
    fetchTask,
    saveTask,
    updateTask,
    deleteTask,
    fetchDefaultTasks,
    deleteDefaultTask,
    addSelectedDefaultTasks,
    addTasksToEpisode,
    fetchLocalDefaultTasks
  } from "/static/requests/podtaskRequest.js";
  import {
    fetchEpisodes,
    viewEpisodeTasks,
  } from "/static/requests/episodeRequest.js";

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("add-task-form");

    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent the form from submitting the traditional way

        // Collect form data
        const taskName = document.getElementById("task-name").value.trim();
        const taskDescription = document
          .getElementById("task-description")
          .value.trim();
        const dueTime = document.getElementById("due-time").value.trim();
        const actionLink = document.getElementById("action-link").value.trim();
        const actionLinkDesc = document
          .getElementById("action-link-desc")
          .value.trim();
        const submissionRequired = document.getElementById(
          "submission-required"
        ).checked;

        const data = {
          taskName,
          taskDescription,
          dueTime,
          actionLink,
          actionLinkDesc,
          submissionRequired
        };

        saveTask(data)
          .then((response) => {
            if (response.error) {
              alert(`Error: ${response.error}`);
            } else {
              alert("Task added successfully!");
              window.location.href = response.redirect_url;
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("There was an error with the registration process.");
          });
      });
    }

  // Fetch tasks on page load
  fetchTasks();
  document.title = "To-Do Workflow";
});

// Fetch tasks from the server
async function fetchTasks() {
  try {
    const response = await fetch("/api/tasks");
    if (!response.ok) {
      throw new Error("Failed to fetch tasks");
    }

    const tasks = await response.json();
    renderTasks(tasks);
  } catch (error) {
    console.error("Error fetching tasks:", error);
    // Show some sample tasks for demonstration
    renderSampleTasks();
  }
}

// Render tasks to the task list
function renderTasks(tasks) {
  const taskList = document.getElementById("task-list");
  if (!taskList) return;

  taskList.innerHTML = ""; // Clear existing tasks

  if (tasks.length === 0) {
    taskList.innerHTML =
      '<li class="empty-message">No tasks found. Add some tasks to get started.</li>';
    return;
  }

  tasks.forEach((task) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="task-details">
        <span class="task-name">${task.taskname || task.name}</span>
        <div class="task-actions">
          <button class="edit-btn" onclick="editTask('${
            task._id || task.id
          }')">Edit</button>
          <button class="delete-btn" onclick="deleteTask('${
            task._id || task.id
          }')">Delete</button>
        </div>
      </div>
    `;

    taskList.appendChild(li);
  });
}

// Render sample tasks for demonstration
function renderSampleTasks() {
  const sampleTasks = [
    { id: "task1", name: "Send guest confirmation email" },
    { id: "task2", name: "Prepare interview questions" },
    { id: "task3", name: "Schedule recording session" },
    { id: "task4", name: "Send reminder 24 hours before recording" },
    { id: "task5", name: "Edit and process audio" }
  ];
  console.log("Welcome to the To-Do Workflow");
  renderTasks(sampleTasks);
}

// Modal functions
function openTaskModal() {
  document.getElementById("task-modal").style.display = "flex";
  document.getElementById("modal-title").innerText = "Create New To-Do";
  // Reset form fields
  document.getElementById("task-name").value = "";
  document.getElementById("task-description").value = "";
  document.getElementById("due-time").value = "";
  document.getElementById("action-link").value = "";
  document.getElementById("action-link-desc").value = "";
  document.getElementById("submission-required").checked = false;

  // Set the save button to create a new task
  const saveButton = document.getElementById("save-task-btn");
  saveButton.onclick = saveTask;
}

function closeModal() {
  document.getElementById("task-modal").style.display = "none";
}

function openDefaultTasksPopup() {
  document.getElementById("default-tasks-popup").style.display = "flex";
  loadDefaultTasks();
}

function closeDefaultTasksPopup() {
  document.getElementById("default-tasks-popup").style.display = "none";
}

// Load default tasks
async function loadDefaultTasks() {
  try {
    const response = await fetch("/api/default-tasks");
    if (!response.ok) {
      throw new Error("Failed to fetch default tasks");
    }

    const defaultTasks = await response.json();
    renderDefaultTasks(defaultTasks);
  } catch (error) {
    console.error("Error loading default tasks:", error);
    // Show some sample default tasks for demonstration
    renderSampleDefaultTasks();
  }
}

// Render default tasks
function renderDefaultTasks(tasks) {
  const defaultTasksList = document.getElementById("default-tasks-list");
  if (!defaultTasksList) return;

  defaultTasksList.innerHTML = ""; // Clear existing tasks

  tasks.forEach((task, index) => {
    const div = document.createElement("div");
    div.classList.add("default-task-item");
    div.innerHTML = `
      <span>${task.name || task}</span>
      <input type="checkbox" id="default-task-${index}" value="${
      task.id || "task" + index
    }">
    `;

    defaultTasksList.appendChild(div);
  });
}

// Render sample default tasks for demonstration
function renderSampleDefaultTasks() {
  const sampleDefaultTasks = [
    "Send guest confirmation email",
    "Prepare interview questions",
    "Schedule recording session",
    "Send reminder 24 hours before recording",
    "Edit and process audio",
    "Create show notes",
    "Schedule social media posts",
    "Upload to podcast platforms"
  ];

  renderDefaultTasks(sampleDefaultTasks);
}

function selectAllDefaultTasks() {
  const checkboxes = document.querySelectorAll(
    '#default-tasks-list input[type="checkbox"]'
  );
  checkboxes.forEach((checkbox) => {
    checkbox.checked = true;
  });
}

function addSelectedDefaultTasks() {
  const checkboxes = document.querySelectorAll(
    '#default-tasks-list input[type="checkbox"]:checked'
  );
  const taskList = document.getElementById("task-list");

  checkboxes.forEach((checkbox) => {
    const taskName = checkbox.parentElement.querySelector("span").textContent;

    // Create new task item
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="task-details">
        <span class="task-name">${taskName}</span>
        <div class="task-actions">
          <button class="edit-btn" onclick="editTask('${checkbox.value}')">Edit</button>
          <button class="delete-btn" onclick="deleteTask('${checkbox.value}')">Delete</button>
        </div>
      </div>
    `;

    taskList.appendChild(li);
  });

  closeDefaultTasksPopup();
}

function viewEpisodes() {
  document.getElementById("episodes-popup").style.display = "flex";
  loadEpisodes();
}

function closeEpisodesPopup() {
  document.getElementById("episodes-popup").style.display = "none";
}

// Load episodes
async function loadEpisodes() {
  try {
    const response = await fetch("/api/episodes");
    if (!response.ok) {
      throw new Error("Failed to fetch episodes");
    }

    const episodes = await response.json();
    renderEpisodes(episodes);
  } catch (error) {
    console.error("Error loading episodes:", error);
    // Show some sample episodes for demonstration
    renderSampleEpisodes();
  }
}

// Render episodes
function renderEpisodes(episodes) {
  const episodesList = document.getElementById("episodes-list");
  if (!episodesList) return;

  episodesList.innerHTML = ""; // Clear existing episodes

    if (episodes.length === 0) {
      let noEpisodesItem = document.createElement("p");
      noEpisodesItem.textContent = "No episodes found";
      episodesList.appendChild(noEpisodesItem);
    } else {
      episodes.forEach((episode) => {
        let episodeItem = document.createElement("a");
        episodeItem.href = "#";
        episodeItem.textContent = episode.title;
        episodeItem.onclick = async (event) => {
          event.preventDefault();
          await viewEpisodeTasks(episode._id);
        };
        episodesList.appendChild(episodeItem);
      });
    }

    document.getElementById("episodes-popup").style.display = "flex";
  };

  window.viewEpisodeTasks = async function (episodeId) {
    const tasks = await fetchEpisodeTasks(episodeId);
    const taskList = document.getElementById("task-list");
    taskList.innerHTML = ""; // Clear existing tasks

    if (tasks.length === 0) {
      let noTasksItem = document.createElement("li");
      noTasksItem.classList.add("task-item");
      noTasksItem.textContent = "No tasks found";
      taskList.appendChild(noTasksItem);
    } else {
      tasks.forEach((task) => {
        let li = document.createElement("li");
        li.classList.add("task-item");
        li.innerHTML = `
          <div class="task-details">
            <span class="task-name">${task.taskname}</span>
            <div class="task-actions">
              <button class="edit-btn" onclick="editTask('${task._id}')">Edit</button>
              <button class="delete-btn" onclick="deleteTask('${task._id}')">Delete</button>
            </div>
          </div>
        `;
        taskList.appendChild(li);
      });
    }

    document.getElementById("episodes-popup").style.display = "none";
  };

  window.openTaskModal = function () {
    document.getElementById("task-modal").style.display = "flex";
  };

  window.closeModal = function () {
    document.getElementById("task-modal").style.display = "none";
  };

  window.openDefaultTasksPopup = async function () {
    document.getElementById("default-tasks-popup").style.display = "flex";

    const defaultTasks = await fetchLocalDefaultTasks();
    const defaultTasksList = document.getElementById("default-tasks-list");
    defaultTasksList.innerHTML = ""; // Clear existing tasks

    defaultTasks.forEach((task, index) => {
      let div = document.createElement("div");
      div.classList.add("default-task-item");
      div.innerHTML = `
        <span>${task}</span>
        <input type="checkbox" id="default-task-${index}" value="${task}">
      `;
      defaultTasksList.appendChild(div);
    });
  };

  window.closeDefaultTasksPopup = function () {
    document.getElementById("default-tasks-popup").style.display = "none";
  };

  window.closeEpisodesPopup = function () {
    document.getElementById("episodes-popup").style.display = "none";
  };

  window.openAddTasksEpisodePopup = async function () {
    const guestId = document.getElementById("selected-guest").dataset.guestId;
    const episodes = await fetchEpisodes(guestId);
    const episodesList = document.getElementById("add-tasks-episode-list");
    episodesList.innerHTML = ""; // Clear existing episodes

    if (episodes.length === 0) {
      let noEpisodesItem = document.createElement("p");
      noEpisodesItem.textContent = "No episodes found";
      episodesList.appendChild(noEpisodesItem);
    } else {
      episodes.forEach((episode) => {
        let episodeItem = document.createElement("a");
        episodeItem.href = "#";
        episodeItem.textContent = episode.title;
        episodeItem.onclick = async (event) => {
          event.preventDefault();
          await addTasksToEpisode(episode._id, guestId, []); // Pass an empty array for tasks for now
        };
        episodesList.appendChild(episodeItem);
      });
    }

    document.getElementById("add-tasks-episode-popup").style.display = "flex";
  };

  window.closeAddTasksEpisodePopup = function () {
    document.getElementById("add-tasks-episode-popup").style.display = "none";
  };
>>>>>>> 69c2325670bcb7ce9e73d39f49227887426af2db:src/frontend/static/js/taskmanagement/taskmanagement.js
