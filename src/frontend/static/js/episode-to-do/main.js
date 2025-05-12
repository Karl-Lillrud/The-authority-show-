"use client"

import { fetchPodcasts } from "/static/requests/podcastRequests.js"
import { fetchAllEpisodes, fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"
import { fetchTasks, fetchLocalDefaultTasks } from "/static/requests/podtaskRequest.js"
import languageManager from '/static/js/i18n/languageManager.js'

// Import components
import { initTaskPageWithComments, renderEnhancedTaskList } from "/static/js/episode-to-do/task-page-integrations.js"
import { renderKanbanBoard } from "/static/js/episode-to-do/kanban-page.js"
import { renderWorkflowEditor } from "/static/js/episode-to-do/workflow-page.js"
import {
  renderTimeline,
  updateProgressBar,
  setupTimelineToggle,
  updateEpisodeDisplay,
  populateEpisodesList,
  populateEpisodeDropdown,
  setupEpisodeDropdown,
  populatePodcastSelector,
} from "/static/js/episode-to-do/layout.js"
import {
  setupTabs,
  addModalStyles,
  addFlatpickrStyles,
  setupModalButtons,
} from "/static/js/episode-to-do/sidebar-header.js"

window.languageManager = languageManager;
languageManager.updatePageContent();

document.addEventListener("DOMContentLoaded", async () => {
  // State management
  const state = {
    podcasts: [],
    episodes: [],
    tasks: [],
    templates: [],
    workflows: [], // Added to store workflows
    activePodcast: null,
    activeTemplate: null,
    activeTab: "tasks",
    selectedEpisode: null,
    selectedTask: null,
    showTimeline: true,
    expandedTasks: {},
    completedTasks: {},
    currentUser: {
      id: "current-user", // In a real app, get this from your auth system
      name: "Current User", // In a real app, get this from your auth system
    },
  }

  // Initialize the UI
  await initData()
  initUI()

  async function initData() {
    try {
      console.log("Fetching data from database...")

      // Fetch podcasts
      const podcastsData = await fetchPodcasts()
      console.log("Podcasts data:", podcastsData)
      state.podcasts = podcastsData.podcast || [] // Note: using podcast instead of podcasts based on your other files

      if (state.podcasts.length > 0) {
        state.activePodcast = state.podcasts[0]

        // Fetch episodes for the active podcast
        const episodesData = await fetchEpisodesByPodcast(state.activePodcast._id) // Note: using _id instead of id based on your other files
        console.log("Episodes data:", episodesData)
        state.episodes = episodesData || []

        if (state.episodes.length > 0) {
          state.selectedEpisode = state.episodes[0]

          // Fetch tasks for the selected episode
          const tasksData = await fetchTasks()
          console.log("Tasks data:", tasksData)

          // Filter tasks for the selected episode
          state.tasks = tasksData
            ? tasksData.filter(
                (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
              )
            : []

          // Load comments for each task
          if (state.tasks.length > 0) {
            console.log("Loading comments for tasks...")
            for (const task of state.tasks) {
              try {
                // We'll load comments when tasks are expanded to avoid too many requests at once
                if (!task.comments) {
                  task.comments = []
                }
              } catch (commentError) {
                console.error("Error initializing comments for task:", commentError)
              }
            }
          }
        }
      } else {
        // If no podcasts, try to fetch all episodes
        const allEpisodes = await fetchAllEpisodes()
        console.log("All episodes data:", allEpisodes)
        state.episodes = allEpisodes || []

        if (state.episodes.length > 0) {
          state.selectedEpisode = state.episodes[0]

          // Fetch tasks for the selected episode
          const tasksData = await fetchTasks()
          console.log("Tasks data:", tasksData)

          // Filter tasks for the selected episode
          state.tasks = tasksData
            ? tasksData.filter(
                (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
              )
            : []

          // Load comments for each task
          if (state.tasks.length > 0) {
            console.log("Loading comments for tasks...")
            for (const task of state.tasks) {
              try {
                // We'll load comments when tasks are expanded to avoid too many requests at once
                if (!task.comments) {
                  task.comments = []
                }
              } catch (commentError) {
                console.error("Error initializing comments for task:", commentError)
              }
            }
          }
        }
      }

      // Fetch default tasks for templates
      const defaultTasksData = await fetchLocalDefaultTasks()
      console.log("Default tasks data:", defaultTasksData)

      // Create template from default tasks
      state.templates = [
        {
          id: "default-template",
          name: "Default Podcast Template",
          description: "Standard workflow for podcast episodes",
          tasks: Array.isArray(defaultTasksData)
            ? defaultTasksData.map((taskName, index) => ({
                id: `default-${index}`,
                name: taskName,
                description: `Default task: ${taskName}`,
                status: "not-started",
                dueDate: "Before recording",
                assignee: null,
                assigneeName: null,
                comments: [],
                dependencies: [], // Added dependencies array
              }))
            : [],
        },
      ]

      state.activeTemplate = state.templates[0]

      // Fetch workflows from the database
      try {
        const workflowsResponse = await fetch("/get_workflows", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        })

        if (workflowsResponse.ok) {
          const workflowsData = await workflowsResponse.json()
          state.workflows = workflowsData.workflows || []
          console.log("Workflows data:", state.workflows)
        }
      } catch (error) {
        console.error("Error fetching workflows:", error)
        state.workflows = []
      }

      console.log("Initialized data:", {
        podcasts: state.podcasts,
        episodes: state.episodes,
        tasks: state.tasks,
        templates: state.templates,
        workflows: state.workflows,
      })
    } catch (error) {
      console.error("Error initializing data:", error)
      alert("Failed to load data. Please refresh the page.")
    }
  }

  function initUI() {
    // Check if we have the necessary data to initialize the UI
    if (!state.activeTemplate) {
      console.warn("Cannot initialize UI: Missing template data")
      return
    }

    // Even if we don't have podcasts or episodes, we can still show the UI with empty states
    console.log("Initializing UI with available data")

    // Add global CSS for modals
    addModalStyles()

    // Add flatpickr CSS and JS
    addFlatpickrStyles()

    // Set up modal buttons
    setupModalButtons()

    // Create a function to update all UI components
    const updateUI = () => {
      // Populate podcast selector
      populatePodcastSelector(state, updateUI)

      // Populate episodes list for the active podcast
      populateEpisodesList(state, updateUI)

      // Populate episode dropdown
      populateEpisodeDropdown(state, updateUI)

      // Populate task list
      renderEnhancedTaskList(state, updateUI)

      // Populate kanban board
      renderKanbanBoard(state, updateUI)

      // Populate timeline
      renderTimeline(state)

      // Update episode display
      updateEpisodeDisplay(state)

      // Update progress bar
      updateProgressBar(state)

      // If we're on the workflow tab, render the workflow editor
      if (state.activeTab === "dependencies") {
        renderWorkflowEditor(state, updateUI)
      }
    }

    // Set up tab switching
    setupTabs(state, updateUI)

    // Set up timeline toggle
    setupTimelineToggle(state)

    // Set up episode dropdown
    setupEpisodeDropdown(state)

    // Initial UI update
    updateUI()

    // Initialize the task page with comment functionality
    initTaskPageWithComments(state, updateUI)
  }
})
