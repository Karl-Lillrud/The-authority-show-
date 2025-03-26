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
