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