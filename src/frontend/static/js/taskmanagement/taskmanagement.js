// Initialize SortableJS for drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Sortable for task list
  const taskList = document.getElementById('task-list');
  if (taskList) {
    new Sortable(taskList, {
      animation: 150,
      ghostClass: 'drag-ghost',
      onEnd: function(evt) {
        // Handle task reordering here
        console.log('Task reordered:', evt.oldIndex, 'to', evt.newIndex);
        // You can add code to update the task order in your database  'to', evt.newIndex);
        // You can add code to update the task order in your database
      }
    });
  }
  
  // Add event listener for task type selection
  const taskTypeSelect = document.getElementById('task-type');
  if (taskTypeSelect) {
    taskTypeSelect.addEventListener('change', function() {
      const actionDetails = document.getElementById('action-details');
      if (this.value !== 'manual') {
        actionDetails.classList.remove('hidden');
      } else {
        actionDetails.classList.add('hidden');
      }
    });
  }

  // Fetch tasks on page load
  fetchTasks();
});

// Fetch tasks from the server
async function fetchTasks() {
  try {
    const response = await fetch('/api/tasks');
    if (!response.ok) {
      throw new Error('Failed to fetch tasks');
    }
    
    const tasks = await response.json();
    renderTasks(tasks);
  } catch (error) {
    console.error('Error fetching tasks:', error);
    // Show some sample tasks for demonstration
    renderSampleTasks();
  }
}

// Render tasks to the task list
function renderTasks(tasks) {
  const taskList = document.getElementById('task-list');
  if (!taskList) return;
  
  taskList.innerHTML = ''; // Clear existing tasks
  
  if (tasks.length === 0) {
    taskList.innerHTML = '<li class="empty-message">No tasks found. Add some tasks to get started.</li>';
    return;
  }
  
  tasks.forEach(task => {
    const li = document.createElement('li');
    li.innerHTML = `
      <div class="task-details">
        <span class="task-name">${task.taskname || task.name}</span>
        <div class="task-actions">
          <button class="edit-btn" onclick="editTask('${task._id || task.id}')">Edit</button>
          <button class="delete-btn" onclick="deleteTask('${task._id || task.id}')">Delete</button>
        </div>
      </div>
    `;
    
    taskList.appendChild(li);
  });
}

// Render sample tasks for demonstration
function renderSampleTasks() {
  const sampleTasks = [
    { id: 'task1', name: 'Send guest confirmation email' },
    { id: 'task2', name: 'Prepare interview questions' },
    { id: 'task3', name: 'Schedule recording session' },
    { id: 'task4', name: 'Send reminder 24 hours before recording' },
    { id: 'task5', name: 'Edit and process audio' }
  ];
  
  renderTasks(sampleTasks);
}

// Modal functions
function openTaskModal() {
  document.getElementById('task-modal').style.display = 'flex';
  document.getElementById('modal-title').innerText = 'Create New Task';
  // Reset form fields
  document.getElementById('task-name').value = '';
  document.getElementById('task-description').value = '';
  document.getElementById('due-time').value = '';
  document.getElementById('action-link').value = '';
  document.getElementById('action-link-desc').value = '';
  document.getElementById('submission-required').checked = false;
  
  // Set the save button to create a new task
  const saveButton = document.getElementById('save-task-btn');
  saveButton.onclick = saveTask;
}

function closeModal() {
  document.getElementById('task-modal').style.display = 'none';
}

function openDefaultTasksPopup() {
  document.getElementById('default-tasks-popup').style.display = 'flex';
  loadDefaultTasks();
}

function closeDefaultTasksPopup() {
  document.getElementById('default-tasks-popup').style.display = 'none';
}

// Load default tasks
async function loadDefaultTasks() {
  try {
    const response = await fetch('/api/default-tasks');
    if (!response.ok) {
      throw new Error('Failed to fetch default tasks');
    }
    
    const defaultTasks = await response.json();
    renderDefaultTasks(defaultTasks);
  } catch (error) {
    console.error('Error loading default tasks:', error);
    // Show some sample default tasks for demonstration
    renderSampleDefaultTasks();
  }
}

// Render default tasks
function renderDefaultTasks(tasks) {
  const defaultTasksList = document.getElementById('default-tasks-list');
  if (!defaultTasksList) return;
  
  defaultTasksList.innerHTML = ''; // Clear existing tasks
  
  tasks.forEach((task, index) => {
    const div = document.createElement('div');
    div.classList.add('default-task-item');
    div.innerHTML = `
      <span>${task.name || task}</span>
      <input type="checkbox" id="default-task-${index}" value="${task.id || 'task' + index}">
    `;
    
    defaultTasksList.appendChild(div);
  });
}

// Render sample default tasks for demonstration
function renderSampleDefaultTasks() {
  const sampleDefaultTasks = [
    'Send guest confirmation email',
    'Prepare interview questions',
    'Schedule recording session',
    'Send reminder 24 hours before recording',
    'Edit and process audio',
    'Create show notes',
    'Schedule social media posts',
    'Upload to podcast platforms'
  ];
  
  renderDefaultTasks(sampleDefaultTasks);
}

function selectAllDefaultTasks() {
  const checkboxes = document.querySelectorAll('#default-tasks-list input[type="checkbox"]');
  checkboxes.forEach(checkbox => {
    checkbox.checked = true;
  });
}

function addSelectedDefaultTasks() {
  const checkboxes = document.querySelectorAll('#default-tasks-list input[type="checkbox"]:checked');
  const taskList = document.getElementById('task-list');
  
  checkboxes.forEach(checkbox => {
    const taskName = checkbox.parentElement.querySelector('span').textContent;
    
    // Create new task item
    const li = document.createElement('li');
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
  document.getElementById('episodes-popup').style.display = 'flex';
  loadEpisodes();
}

function closeEpisodesPopup() {
  document.getElementById('episodes-popup').style.display = 'none';
}

// Load episodes
async function loadEpisodes() {
  try {
    const response = await fetch('/api/episodes');
    if (!response.ok) {
      throw new Error('Failed to fetch episodes');
    }
    
    const episodes = await response.json();
    renderEpisodes(episodes);
  } catch (error) {
    console.error('Error loading episodes:', error);
    // Show some sample episodes for demonstration
    renderSampleEpisodes();
  }
}

// Render episodes
function renderEpisodes(episodes) {
  const episodesList = document.getElementById('episodes-list');
  if (!episodesList) return;
  
  episodesList.innerHTML = ''; // Clear existing episodes
  
  if (episodes.length === 0) {
    episodesList.innerHTML = '<p class="empty-message">No episodes found.</p>';
    return;
  }
  
  episodes.forEach(episode => {
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = episode.title;
    a.onclick = function(event) {
      event.preventDefault();
      viewEpisodeTasks(episode._id || episode.id);
    };
    
    episodesList.appendChild(a);
  });
}

// Render sample episodes for demonstration
function renderSampleEpisodes() {
  const sampleEpisodes = [
    { id: 'episode1', title: 'Episode 1: Getting Started with Podcasting' },
    { id: 'episode2', title: 'Episode 2: Finding Your Niche' },
    { id: 'episode3', title: 'Episode 3: Growing Your Audience' }
  ];
  
  renderEpisodes(sampleEpisodes);
}

function viewEpisodeTasks(episodeId) {
  // Here you would fetch tasks for the selected episode
  console.log('Viewing tasks for episode:', episodeId);
  
  // For demo purposes, let's just show some dummy tasks
  const dummyTasks = [
    { id: 'task1', name: 'Prepare show notes for ' + episodeId },
    { id: 'task2', name: 'Schedule social media posts for ' + episodeId },
    { id: 'task3', name: 'Upload audio file for ' + episodeId }
  ];
  
  renderTasks(dummyTasks);
  
  closeEpisodesPopup();
}

function openAddTasksEpisodePopup() {
  document.getElementById('add-tasks-episode-popup').style.display = 'flex';
  loadEpisodesForAddTasks();
}

function closeAddTasksEpisodePopup() {
  document.getElementById('add-tasks-episode-popup').style.display = 'none';
}

// Load episodes for adding tasks
function loadEpisodesForAddTasks() {
  // Reuse the same episodes data
  try {
    const episodesList = document.getElementById('add-tasks-episode-list');
    if (!episodesList) return;
    
    // Clone the episodes from the episodes list if it exists
    const originalEpisodesList = document.getElementById('episodes-list');
    if (originalEpisodesList && originalEpisodesList.children.length > 0) {
      episodesList.innerHTML = '';
      
      Array.from(originalEpisodesList.children).forEach(child => {
        if (child.tagName === 'A') {
          const a = child.cloneNode(true);
          a.onclick = function(event) {
            event.preventDefault();
            const episodeId = a.getAttribute('onclick').match(/'([^']+)'/)[1];
            addTasksToEpisode(episodeId);
          };
          
          episodesList.appendChild(a);
        }
      });
    } else {
      // If no episodes are loaded yet, load sample episodes
      renderSampleEpisodesForAddTasks();
    }
  } catch (error) {
    console.error('Error loading episodes for adding tasks:', error);
    renderSampleEpisodesForAddTasks();
  }
}

// Render sample episodes for adding tasks
function renderSampleEpisodesForAddTasks() {
  const sampleEpisodes = [
    { id: 'episode1', title: 'Episode 1: Getting Started with Podcasting' },
    { id: 'episode2', title: 'Episode 2: Finding Your Niche' },
    { id: 'episode3', title: 'Episode 3: Growing Your Audience' }
  ];
  
  const episodesList = document.getElementById('add-tasks-episode-list');
  if (!episodesList) return;
  
  episodesList.innerHTML = ''; // Clear existing episodes
  
  sampleEpisodes.forEach(episode => {
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = episode.title;
    a.onclick = function(event) {
      event.preventDefault();
      addTasksToEpisode(episode.id);
    };
    
    episodesList.appendChild(a);
  });
}

function addTasksToEpisode(episodeId) {
  // Here you would add the current tasks to the selected episode
  console.log('Adding tasks to episode:', episodeId);
  
  // Show a success message
  alert('Tasks successfully added to ' + episodeId);
  
  closeAddTasksEpisodePopup();
}

// Task CRUD operations
function editTask(taskId) {
  // Here you would fetch the task details and populate the form
  console.log('Editing task:', taskId);
  
  // For demo purposes, let's just show the modal with some dummy data
  document.getElementById('task-modal').style.display = 'flex';
  document.getElementById('modal-title').innerText = 'Edit Task';
  document.getElementById('task-name').value = 'Task ' + taskId;
  document.getElementById('task-description').value = 'Description for task ' + taskId;
  document.getElementById('due-time').value = '7';
  document.getElementById('action-link').value = 'https://example.com';
  document.getElementById('action-link-desc').value = 'Example link';
  document.getElementById('submission-required').checked = true;
  
  // Set the save button to update instead of create
  const saveButton = document.getElementById('save-task-btn');
  saveButton.onclick = function() {
    updateTask(taskId);
  };
}

function saveTask() {
  // Get form values
  const taskName = document.getElementById('task-name').value;
  const taskDescription = document.getElementById('task-description').value;
  const dueTime = document.getElementById('due-time').value;
  const actionLink = document.getElementById('action-link').value;
  const actionLinkDesc = document.getElementById('action-link-desc').value;
  const submissionRequired = document.getElementById('submission-required').checked;
  
  // Validate form
  if (!taskName) {
    alert('Please enter a task name');
    return;
  }
  
  // Create task object
  const task = {
    name: taskName,
    description: taskDescription,
    dueTime: dueTime,
    actionLink: actionLink,
    actionLinkDesc: actionLinkDesc,
    submissionRequired: submissionRequired
  };
  
  // Here you would send the task to your server
  console.log('Saving task:', task);
  
  // For demo purposes, let's just add it to the list
  const taskList = document.getElementById('task-list');
  const li = document.createElement('li');
  const taskId = 'new-task-' + Date.now();
  
  li.innerHTML = `
    <div class="task-details">
      <span class="task-name">${task.name}</span>
      <div class="task-actions">
        <button class="edit-btn" onclick="editTask('${taskId}')">Edit</button>
        <button class="delete-btn" onclick="deleteTask('${taskId}')">Delete</button>
      </div>
    </div>
  `;
  
  taskList.appendChild(li);
  
  closeModal();
}

function updateTask(taskId) {
  // Get form values
  const taskName = document.getElementById('task-name').value;
  const taskDescription = document.getElementById('task-description').value;
  const dueTime = document.getElementById('due-time').value;
  const actionLink = document.getElementById('action-link').value;
  const actionLinkDesc = document.getElementById('action-link-desc').value;
  const submissionRequired = document.getElementById('submission-required').checked;
  
  // Validate form
  if (!taskName) {
    alert('Please enter a task name');
    return;
  }
  
  // Create task object
  const task = {
    name: taskName,
    description: taskDescription,
    dueTime: dueTime,
    actionLink: actionLink,
    actionLinkDesc: actionLinkDesc,
    submissionRequired: submissionRequired
  };
  
  // Here you would update the task in your database
  console.log('Updating task:', taskId, task);
  
  // For demo purposes, let's just update the task in the list
  const taskItems = document.querySelectorAll('#task-list li');
  
  taskItems.forEach(item => {
    if (item.querySelector('.edit-btn').getAttribute('onclick').includes(taskId)) {
      item.querySelector('.task-name').textContent = taskName;
    }
  });
  
  closeModal();
}

function deleteTask(taskId) {
  // Confirm deletion
  if (!confirm('Are you sure you want to delete this task?')) {
    return;
  }
  
  // Here you would delete the task from your database
  console.log('Deleting task:', taskId);
  
  // For demo purposes, let's just remove the task from the list
  const taskItems = document.querySelectorAll('#task-list li');
  
  taskItems.forEach(item => {
    if (item.querySelector('.delete-btn').getAttribute('onclick').includes(taskId)) {
      item.remove();
    }
  });
}

// Make functions available globally
window.openTaskModal = openTaskModal;
window.closeModal = closeModal;
window.openDefaultTasksPopup = openDefaultTasksPopup;
window.closeDefaultTasksPopup = closeDefaultTasksPopup;
window.selectAllDefaultTasks = selectAllDefaultTasks;
window.addSelectedDefaultTasks = addSelectedDefaultTasks;
window.viewEpisodes = viewEpisodes;
window.closeEpisodesPopup = closeEpisodesPopup;
window.viewEpisodeTasks = viewEpisodeTasks;
window.openAddTasksEpisodePopup = openAddTasksEpisodePopup;
window.closeAddTasksEpisodePopup = closeAddTasksEpisodePopup;
window.addTasksToEpisode = addTasksToEpisode;
window.editTask = editTask;
window.saveTask = saveTask;
window.updateTask = updateTask;
window.deleteTask = deleteTask;