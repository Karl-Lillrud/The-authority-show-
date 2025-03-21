window.addSelectedDefaultTasks = function () {
    const selectedTasks = [];
    const checkboxes = document.querySelectorAll('#default-tasks-list input[type="checkbox"]:checked');

    checkboxes.forEach((checkbox) => {
        selectedTasks.push(checkbox.value);
    });

    if (selectedTasks.length === 0) {
        alert("No tasks selected!");
        return;
    }

    // Call function to add tasks to episode
    window.addTasksToEpisode(selectedTasks);

    // Close the popup after adding tasks
    window.closeDefaultTasksPopup();
};

// Ensure addTasksToEpisode is global
window.addTasksToEpisode = function (tasks) {
    console.log("Tasks added to episode:", tasks);
};

// Ensure closeDefaultTasksPopup is global
window.closeDefaultTasksPopup = function () {
    document.getElementById("default-tasks-popup").style.display = "none";
};
