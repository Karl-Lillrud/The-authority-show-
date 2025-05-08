"use client"

// Setup tabs
export function setupTabs(state, updateUI) {
  const tabButtons = document.querySelectorAll(".tab-btn")
  const tabPanes = document.querySelectorAll(".tab-pane")

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const tabId = button.getAttribute("data-tab")

      // Update active state
      tabButtons.forEach((btn) => btn.classList.remove("active"))
      tabPanes.forEach((pane) => pane.classList.remove("active"))

      button.classList.add("active")
      document.getElementById(`${tabId}-tab`)?.classList.add("active")

      state.activeTab = tabId

      // If the workflow tab is selected, render the workflow editor
      if (tabId === "dependencies") {
        import("/static/js/episode-to-do/workflow-page.js")
          .then((module) => {
            module.renderWorkflowEditor(state, updateUI)
          })
          .catch((error) => {
            console.error("Error loading workflow editor:", error)
          })
      }
    })
  })

  // Update the dependencies tab button to say "Edit Workflow"
  const dependenciesTabBtn = document.querySelector('.tab-btn[data-tab="dependencies"]')
  if (dependenciesTabBtn) {
    dependenciesTabBtn.innerHTML = `
      <i class="fas fa-file-alt"></i>
      <span>Edit Workflow</span>
    `
  }
}

// Add global CSS for modals
export function addModalStyles() {
  const style = document.createElement("style")
  style.textContent = `
    .popup {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }

    #add-comment-modal {
      z-index: 2000; /* Ensure comment modal is above other elements */
    }

    #add-comment-modal .popup-content {
      max-width: 500px;
      width: 90%;
    }

    #comment-text {
      min-height: 100px;
    }
    
    .popup-content {
      background-color: white;
      border-radius: 8px;
      padding: 20px;
      width: 90%;
      max-width: 500px;
      max-height: 90vh;
      overflow: auto;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      position: relative;
      transform: scale(0.9);
      opacity: 0;
      transition: transform 0.3s, opacity 0.3s;
    }
    
    .popup-content.show {
      transform: scale(1);
      opacity: 1;
    }
    
    .popup-content.hide {
      transform: scale(0.9);
      opacity: 0;
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #eee;
    }
    
    .modal-header h2 {
      margin: 0;
      font-size: 1.5rem;
    }
    
    .close-btn {
      background: none;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: #666;
    }
    
    .close-btn:hover {
      color: #333;
    }
    
    .popup-body {
      margin-bottom: 20px;
    }
    
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      padding-top: 15px;
      border-top: 1px solid #eee;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
    }
    
    .form-control {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 1rem;
    }
    
    textarea.form-control {
      min-height: 100px;
      resize: vertical;
    }
    
    .btn {
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
      transition: background-color 0.2s;
    }
    
    .save-btn {
      background-color: #4CAF50;
      color: white;
      border: none;
    }
    
    .save-btn:hover {
      background-color: #45a049;
    }
    
    .cancel-btn {
      background-color: #f1f1f1;
      color: #333;
      border: 1px solid #ddd;
    }
    
    .cancel-btn:hover {
      background-color: #e7e7e7;
    }
    
    .help-text {
      font-size: 0.8rem;
      color: #666;
      margin-top: 5px;
    }
    
    /* Dependency visualization styles */
    .task-dependency-warning {
      background-color: #fff3cd;
      border: 1px solid #ffeeba;
      border-radius: 4px;
      padding: 8px 12px;
      margin-top: 8px;
      color: #856404;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .task-dependency-list {
      margin: 5px 0;
      padding-left: 20px;
    }
    
    .task-dependency-item {
      display: flex;
      align-items: center;
      gap: 5px;
      margin-bottom: 3px;
    }
    
    .dependency-status {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    
    .dependency-status.completed {
      background-color: #4CAF50;
    }
    
    .dependency-status.pending {
      background-color: #f0ad4e;
    }
    
    .task-checkbox.disabled {
      opacity: 0.5;
      cursor: not-allowed;
      background-color: #f8f9fa;
    }

    .dependency-preview {
      margin-top: 10px;
      padding: 8px;
      border-radius: 4px;
      background-color: #f8f9fa;
      max-height: 150px;
      overflow-y: auto;
    }

    .dependency-preview-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .dependency-preview-item {
      display: flex;
      align-items: center;
      padding: 4px 0;
      gap: 6px;
    }

    .task-dependencies-badge {
      display: inline-flex;
      align-items: center;
      background-color: #e9ecef;
      border-radius: 12px;
      padding: 2px 8px;
      font-size: 0.8rem;
      margin-right: 5px;
    }

    .kanban-task .task-dependencies {
      margin-top: 4px;
      font-size: 0.8rem;
    }

    .dependency-visualization {
      margin-top: 15px;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 10px;
    }

    .dependency-visualization-title {
      font-weight: 500;
      margin-bottom: 8px;
    }

    .dependency-chain {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      align-items: center;
    }

    .dependency-chain-item {
      background-color: #f1f3f5;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 0.9rem;
    }

    .dependency-chain-arrow {
      color: #adb5bd;
    }
  `
  document.head.appendChild(style)
}

// Add flatpickr for date/time picker
export function addFlatpickrStyles() {
  // Add flatpickr CSS
  const flatpickrCSS = document.createElement("link")
  flatpickrCSS.rel = "stylesheet"
  flatpickrCSS.href = "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"
  document.head.appendChild(flatpickrCSS)

  // Add flatpickr theme (optional)
  const flatpickrTheme = document.createElement("link")
  flatpickrTheme.rel = "stylesheet"
  flatpickrTheme.href = "https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/material_blue.css"
  document.head.appendChild(flatpickrTheme)

  // Add flatpickr JS
  const flatpickrScript = document.createElement("script")
  flatpickrScript.src = "https://cdn.jsdelivr.net/npm/flatpickr"
  document.head.appendChild(flatpickrScript)
}

export function setupModalButtons() {
  // Create modal containers if they don't exist
  if (!document.getElementById("modal-container")) {
    const modalContainer = document.createElement("div")
    modalContainer.id = "modal-container"
    document.body.appendChild(modalContainer)
  }
}
