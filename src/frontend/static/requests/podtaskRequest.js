// Updated podtaskRequest.js remains the same as before:
export async function fetchTasks() {
  try {
    const response = await fetch("/get_podtasks");
    const data = await response.json();
    if (response.ok) {
      return data.podtasks;
    } else {
      console.error("Failed to fetch tasks:", data.error);
      alert("Failed to fetch tasks: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching tasks:", error);
    alert("Failed to fetch tasks.");
  }
}

export async function fetchTask(taskId) {
  try {
    const response = await fetch(`/get_podtask/${taskId}`);
    const data = await response.json();
    if (response.ok) {
      return data;
    } else {
      console.error("Failed to fetch task:", data.error);
      alert("Failed to fetch task: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching task:", error);
    alert("Failed to fetch task.");
  }
}

export async function saveTask(taskData) {
  try {
    // Updated endpoint: using "/add_podtasks" to match backend route
    const response = await fetch("/add_podtasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskData)
    });
    const result = await response.json();
    if (response.ok) {
      return result;
    } else {
      console.error("Error saving task:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error saving task:", error);
    alert("Failed to save task.");
  }
}

export async function updateTask(taskId, taskData) {
  try {
    const response = await fetch(`/update_podtasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskData)
    });
    const result = await response.json();
    if (response.ok) {
      alert("Task updated successfully!");
      return result;
    } else {
      console.error("Error updating task:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error updating task:", error);
    alert("Failed to update task.");
  }
}

export async function deleteTask(taskId) {
  try {
    const response = await fetch(`/delete_podtasks/${taskId}`, {
      method: "DELETE"
    });
    const result = await response.json();
    if (response.ok) {
      alert("Task deleted successfully!");
      return result;
    } else {
      console.error("Error deleting task:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error deleting task:", error);
    alert("Failed to delete task.");
  }
}

export async function fetchDefaultTasks() {
  try {
    const response = await fetch("/get_default_tasks");
    const data = await response.json();
    if (response.ok) {
      return data.default_tasks;
    } else {
      console.error("Failed to fetch default tasks:", data.error);
      alert("Failed to fetch default tasks: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching default tasks:", error);
    alert("Failed to fetch default tasks.");
  }
}

export async function deleteDefaultTask(taskId) {
  try {
    const response = await fetch(`/delete_default_task/${taskId}`, {
      method: "DELETE"
    });
    const result = await response.json();
    if (response.ok) {
      alert("Default task deleted successfully!");
      return result;
    } else {
      console.error("Error deleting default task:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error deleting default task:", error);
    alert("Failed to delete default task.");
  }
}

export async function addSelectedDefaultTasks(tasks) {
  try {
    const response = await fetch("/add_selected_default_tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tasks })
    });
    const result = await response.json();
    if (response.ok) {
      alert("Selected tasks added successfully!");
      return result;
    } else {
      console.error("Error adding selected tasks:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error adding selected tasks:", error);
    alert("Failed to add selected tasks.");
  }
}

export async function addTasksToEpisode(episodeId, guestId, tasks) {
  try {
    const response = await fetch("/add_tasks_to_episode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tasks,
        episodeId: episodeId,
        guestId: guestId      
      })
    });
    const result = await response.json();
    if (response.ok) {
      alert("Tasks added to episode successfully!");
      return result;
    } else {
      console.error("Error adding tasks to episode:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error adding tasks to episode:", error);
    alert("Failed to add tasks to episode.");
  }
}

export async function fetchLocalDefaultTasks() {
  try {
    const response = await fetch("/static/defaulttaskdata/default_tasks.json");
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching local default tasks:", error);
    alert("Failed to fetch local default tasks.");
  }
}

export async function addDefaultTasksToEpisode(episodeId, defaultTasks) {
  try {
    const response = await fetch("/add_default_tasks_to_episode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        default_tasks: defaultTasks,
        episode_id: episodeId
      })
    });
    const result = await response.json();
    if (response.ok) {
      alert("Default tasks added to episode successfully!");
      return result;
    } else {
      console.error("Error adding default tasks to episode:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error adding default tasks to episode:", error);
    alert("Failed to add default tasks to episode.");
  }
}

export async function saveWorkflow(episodeId, workflowName, workflowDescription, tasks) {
  try {
    const response = await fetch("/save_workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        episode_id: episodeId, 
        tasks, 
        name: workflowName,
        description: workflowDescription 
      }),
    });
    const data = await response.json();
    if (response.ok) {
      alert("Workflow saved successfully!");
      return data;
    } else {
      alert("Failed to save workflow: " + data.error);
      return null;
    }
  } catch (error) {
    console.error("Error saving workflow:", error);
    alert("Failed to save workflow.");
    throw error;
  }
}

export async function getWorkflows() {
  try {
    const response = await fetch("/get_workflows", {
      method: "GET", 
      headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    if (response.ok) {
      return data.workflows;
    } else {
      alert("Failed to fetch workflows: " + data.error);
      return [];
    }
  } catch (error) {
    console.error("Error fetching workflows:", error);
    alert("Failed to fetch workflows.");
    throw error;
  }
}
