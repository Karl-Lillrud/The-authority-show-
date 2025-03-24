// Task Management functionality for podcast dashboard
import { 
  fetchTasks, 
  saveTask, 
  updateTask, 
  deleteTask, 
  fetchDefaultTasks,
  addTasksToEpisode,
  addDefaultTasksToEpisode
} from "/static/requests/podtaskRequest.js"

// Initialize task management for all episode cards
export function initTaskManagement() {
  // Add event listeners to all toggle task buttons
  const toggleButtons = document.querySelectorAll('.toggle-tasks')
  toggleButtons.forEach(button => {
    button.addEventListener('click', handleToggleTasks)
  })
}

// Handle toggle tasks button click
function handleToggleTasks(event) {
  const button = event.currentTarget
  const card = button.closest('.episode-card')
  const tasksContainer = card.querySelector('.tasks-container')
  const episodeId = card.dataset.episodeId

  if (tasksContainer.style.display === 'none') {
    tasksContainer.style.display = 'block'
    button.textContent = '-'
    
    // Load tasks for this episode
    loadTasksForEpisode(episodeId, tasksContainer)
  } else {
    tasksContainer.style.display = 'none'
    button.textContent = '+'
  }
}

// Load tasks for an episode
async function loadTasksForEpisode(episodeId, container) {
  try {
    // Show loading state
    container.innerHTML = '<p>Loading tasks...</p>'
    
    // Fetch tasks for this episode
    const tasks = await fetchTasks()
    
    // Filter tasks for this episode
    const episodeTasks = tasks ? tasks.filter(task => task.episode_id === episodeId) : []
    
    // Render tasks UI
    renderTasksUI(episodeId, episodeTasks, container)
  } catch (error) {
    console.error('Error loading tasks:', error)
    container.innerHTML = '<p class="error-message">Error loading tasks. Please try again.</p>'
  }
}

// Render tasks UI
function renderTasksUI(episodeId, tasks, container) {
  // Create task management UI
  const taskManagementHTML = `
    <div class="task-management">
      <div class="task-header">
        <h3>Tasks</h3>
        <div class="task-header-actions">
          <button class="btn import-tasks-btn" data-episode-id="${episodeId}">
            <i class="fas fa-upload"></i> Import
          </button>
          <button class="btn add-task-btn" data-episode-id="${episodeId}">
            <i class="fas fa-plus"></i> Add Task
          </button>
        </div>
      </div>
      <div class="task-list">
        ${tasks.length > 0 ? renderTaskList(tasks) : '<p class="no-tasks">No tasks yet. Add a task or import default tasks.</p>'}
      </div>
    </div>
  `
  
  // Set the HTML
  container.innerHTML = taskManagementHTML
  
  // Add event listeners
  const addTaskBtn = container.querySelector('.add-task-btn')
  addTaskBtn.addEventListener('click', () => showAddTaskPopup(episodeId))
  
  const importTasksBtn = container.querySelector('.import-tasks-btn')
  importTasksBtn.addEventListener('click', () => showImportTasksPopup(episodeId))
  
  // Add event listeners to task actions
  const taskItems = container.querySelectorAll('.task-item')
  taskItems.forEach(item => {
    const taskId = item.dataset.taskId
    
    // Checkbox for completion
    const checkbox = item.querySelector('.task-checkbox')
    checkbox.addEventListener('change', () => toggleTaskCompletion(taskId, checkbox.checked))
    
    // Edit button
    const editBtn = item.querySelector('.edit-task-btn')
    editBtn.addEventListener('click', () => showEditTaskPopup(taskId))
    
    // Delete button
    const deleteBtn = item.querySelector('.delete-task-btn')
    deleteBtn.addEventListener('click', () => confirmDeleteTask(taskId))
    
    // Assign to me button
    const assignBtn = item.querySelector('.assign-to-me-btn')
    if (assignBtn) {
      assignBtn.addEventListener('click', () => assignTaskToMe(taskId))
    }
  })
}

// Render task list
function renderTaskList(tasks) {
  return tasks.map(task => `
    <div class="task-item ${task.completed ? 'task-completed' : ''}" data-task-id="${task._id}">
      <input type="checkbox" class="task-checkbox" ${task.completed ? 'checked' : ''}>
      <div class="task-content">
        <div class="task-title">${task.title}</div>
        ${task.description ? `<div class="task-description">${task.description}</div>` : ''}
        <div class="task-meta">
          <span class="task-assigned">Assigned to: ${task.assigned_to ? task.assigned_to : 'Unassigned'}</span>
          ${!task.assigned_to ? '<button class="assign-to-me-btn">Assign to me</button>' : ''}
        </div>
      </div>
      <div class="task-actions">
        <button class="task-action-btn edit-task-btn" title="Edit Task">
          <i class="fas fa-edit"></i>
        </button>
        <button class="task-action-btn delete-task-btn delete" title="Delete Task">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
  `).join('')
}

// Show add task popup
// Updated part of task.js: Modified showAddTaskPopup to send valid data
function showAddTaskPopup(episodeId) {
const popupHTML = `
  <div id="task-popup" class="popup">
    <div class="popup-content">
      <span class="close-btn">&times;</span>
      <h2>Add New Task</h2>
      <div class="popup-body">
        <form id="task-form">
          <input type="hidden" id="task-episode-id" value="${episodeId}">
          <div class="form-group">
            <label for="task-title">Title</label>
            <input type="text" id="task-title" class="form-control" placeholder="Enter task title" required>
          </div>
          <div class="form-group">
            <label for="task-description">Description (optional)</label>
            <textarea id="task-description" class="form-control" placeholder="Enter task description"></textarea>
          </div>
          <div class="form-group">
            <label for="task-assigned">Assigned To</label>
            <select id="task-assigned" class="form-control">
              <option value="">Unassigned</option>
              <option value="John Doe">John Doe</option>
              <option value="Jane Smith">Jane Smith</option>
              <option value="Alex Johnson">Alex Johnson</option>
            </select>
          </div>
          <button type="submit" class="btn save-btn">Add Task</button>
        </form>
      </div>
    </div>
  </div>
`;

document.body.insertAdjacentHTML('beforeend', popupHTML);
const popup = document.getElementById('task-popup');
popup.style.display = 'flex';

const closeBtn = popup.querySelector('.close-btn');
closeBtn.addEventListener('click', () => {
  popup.remove();
});

popup.addEventListener('click', (e) => {
  if (e.target === popup) {
    popup.remove();
  }
});

const form = document.getElementById('task-form');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('task-title').value;
  const description = document.getElementById('task-description').value;
  const assignedTo = document.getElementById('task-assigned').value;
  // Removed the "completed" field to match the backend's expected schema.
  const taskData = {
    name: title,
    description,
    episodeId: episodeId,
    guestId: assignedTo || null  // use guestId instead of assigned_to
  };    
  
  
  try {
    await saveTask(taskData);
    popup.remove();
    const tasksContainer = document.querySelector(`.episode-card[data-episode-id="${episodeId}"] .tasks-container`);
    loadTasksForEpisode(episodeId, tasksContainer);
  } catch (error) {
    console.error('Error saving task:', error);
  }
});
}

// Show edit task popup
async function showEditTaskPopup(taskId) {
  try {
    // Fetch task details
    const task = await fetchTask(taskId)
    
    // Create popup HTML
    const popupHTML = `
      <div id="task-popup" class="popup">
        <div class="popup-content">
          <span class="close-btn">&times;</span>
          <h2>Edit Task</h2>
          <div class="popup-body">
            <form id="task-form">
              <input type="hidden" id="task-id" value="${taskId}">
              <input type="hidden" id="task-episode-id" value="${task.episode_id}">
              <div class="form-group">
                <label for="task-title">Title</label>
                <input type="text" id="task-title" class="form-control" value="${task.title}" required>
              </div>
              <div class="form-group">
                <label for="task-description">Description (optional)</label>
                <textarea id="task-description" class="form-control">${task.description || ''}</textarea>
              </div>
              <div class="form-group">
                <label for="task-assigned">Assigned To</label>
                <select id="task-assigned" class="form-control">
                  <option value="" ${!task.assigned_to ? 'selected' : ''}>Unassigned</option>
                  <option value="John Doe" ${task.assigned_to === 'John Doe' ? 'selected' : ''}>John Doe</option>
                  <option value="Jane Smith" ${task.assigned_to === 'Jane Smith' ? 'selected' : ''}>Jane Smith</option>
                  <option value="Alex Johnson" ${task.assigned_to === 'Alex Johnson' ? 'selected' : ''}>Alex Johnson</option>
                </select>
              </div>
              <button type="submit" class="btn save-btn">Update Task</button>
            </form>
          </div>
        </div>
      </div>
    `
    
    // Add popup to the DOM
    document.body.insertAdjacentHTML('beforeend', popupHTML)
    
    // Show popup
    const popup = document.getElementById('task-popup')
    popup.style.display = 'flex'
    
    // Add event listeners
    const closeBtn = popup.querySelector('.close-btn')
    closeBtn.addEventListener('click', () => {
      popup.remove()
    })
    
    // Close popup when clicking outside
    popup.addEventListener('click', (e) => {
      if (e.target === popup) {
        popup.remove()
      }
    })
    
    // Form submission
    const form = document.getElementById('task-form')
    form.addEventListener('submit', async (e) => {
      e.preventDefault()
      
      // Get form values
      const title = document.getElementById('task-title').value
      const description = document.getElementById('task-description').value
      const assignedTo = document.getElementById('task-assigned').value
      const episodeId = document.getElementById('task-episode-id').value
      
      // Create task object
      const taskData = {
        title,
        description,
        assigned_to: assignedTo || null
      }
      
      try {
        // Update task
        await updateTask(taskId, taskData)
        
        // Close popup
        popup.remove()
        
        // Reload tasks
        const tasksContainer = document.querySelector(`.episode-card[data-episode-id="${episodeId}"] .tasks-container`)
        loadTasksForEpisode(episodeId, tasksContainer)
      } catch (error) {
        console.error('Error updating task:', error)
      }
    })
  } catch (error) {
    console.error('Error fetching task details:', error)
  }
}

// Show import tasks popup
// Show import tasks popup
async function showImportTasksPopup(episodeId) {
try {
  // Fetch default tasks (array of strings) from your JSON file
  const defaultTasks = await fetchLocalDefaultTasks()
  
  const popupHTML = `
    <div id="import-tasks-popup" class="popup">
      <div class="popup-content">
        <span class="close-btn">&times;</span>
        <h2>Import Default Tasks</h2>
        <div class="popup-body">
          <p>Select the default tasks you want to import:</p>
          <div class="import-tasks-container">
            ${defaultTasks.map((task, index) => `
              <div class="import-task-item">
                <input type="checkbox" id="import-task-${index}" class="import-task-checkbox" value="${task}">
                <label for="import-task-${index}" class="import-task-title">${task}</label>
              </div>
            `).join('')}
          </div>
          <div class="import-actions">
            <span class="selected-count">0 selected</span>
            <button id="import-selected-btn" class="btn save-btn" disabled>Import Selected</button>
          </div>
        </div>
      </div>
    </div>
  `
  
  document.body.insertAdjacentHTML('beforeend', popupHTML)
  
  const popup = document.getElementById('import-tasks-popup')
  popup.style.display = 'flex'
  
  const closeBtn = popup.querySelector('.close-btn')
  closeBtn.addEventListener('click', () => {
    popup.remove()
  })
  
  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      popup.remove()
    }
  })
  
  const checkboxes = popup.querySelectorAll('.import-task-checkbox')
  const selectedCountEl = popup.querySelector('.selected-count')
  const importBtn = document.getElementById('import-selected-btn')
  
  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      const selectedCount = [...checkboxes].filter(cb => cb.checked).length
      selectedCountEl.textContent = `${selectedCount} selected`
      importBtn.disabled = selectedCount === 0
    })
  })
  
  importBtn.addEventListener('click', async () => {
    // Get selected tasks as an array of strings
    const selectedTasks = [...checkboxes]
      .filter(cb => cb.checked)
      .map(cb => cb.value)
    
    try {
      await addDefaultTasksToEpisode(episodeId, selectedTasks)
      popup.remove()
      const tasksContainer = document.querySelector(`.episode-card[data-episode-id="${episodeId}"] .tasks-container`)
      loadTasksForEpisode(episodeId, tasksContainer)
    } catch (error) {
      console.error('Error importing default tasks:', error)
    }
  })
} catch (error) {
  console.error('Error fetching default tasks:', error)
}
}



// Toggle task completion
async function toggleTaskCompletion(taskId, completed) {
  try {
    // Update task
    await updateTask(taskId, { completed })
    
    // Update UI
    const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`)
    if (completed) {
      taskItem.classList.add('task-completed')
    } else {
      taskItem.classList.remove('task-completed')
    }
  } catch (error) {
    console.error('Error updating task completion:', error)
  }
}

// Confirm delete task
function confirmDeleteTask(taskId) {
  if (confirm('Are you sure you want to delete this task?')) {
    deleteTaskById(taskId)
  }
}

// Delete task
async function deleteTaskById(taskId) {
  try {
    // Get episode ID before deleting
    const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`)
    const tasksContainer = taskItem.closest('.tasks-container')
    const episodeCard = tasksContainer.closest('.episode-card')
    const episodeId = episodeCard.dataset.episodeId
    
    // Delete task
    await deleteTask(taskId)
    
    // Reload tasks
    loadTasksForEpisode(episodeId, tasksContainer)
  } catch (error) {
    console.error('Error deleting task:', error)
  }
}

// Assign task to me
async function assignTaskToMe(taskId) {
  try {
    // Update task
    await updateTask(taskId, { assigned_to: 'Current User' }) // Replace with actual current user
    
    // Get episode ID
    const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`)
    const tasksContainer = taskItem.closest('.tasks-container')
    const episodeCard = tasksContainer.closest('.episode-card')
    const episodeId = episodeCard.dataset.episodeId
    
    // Reload tasks
    loadTasksForEpisode(episodeId, tasksContainer)
  } catch (error) {
    console.error('Error assigning task:', error)
  }
}

// Helper function to fetch local default tasks
async function fetchLocalDefaultTasks() {
  try {
    const response = await fetch("/static/defaulttaskdata/default_tasks.json")
    const data = await response.json()
    return data
  } catch (error) {
    console.error("Error fetching local default tasks:", error)
    return []
  }
}

// Helper function to fetch a single task
async function fetchTask(taskId) {
    try {
        const tasks = await fetchTasks(); // Use the existing fetchTasks function
        const task = tasks.find(task => task._id === taskId);
        if (!task) {
            throw new Error(`Task with ID ${taskId} not found`);
        }
        return task;
    } catch (error) {
        console.error('Error fetching task:', error);
        throw error;
    }
}