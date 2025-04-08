// Create a loading bar module that can be imported into podprofile.js
export function createLoadingBar() {
  // Create the loading bar popup container
  const loadingPopup = document.createElement("div");
  loadingPopup.className = "popup loading-popup";
  loadingPopup.style.display = "none";

  // Create the loading bar content with improved design
  loadingPopup.innerHTML = `
    <div class="popup-content loading-popup-content">
      <h2 class="loading-title">Processing Your Podcast</h2>
      <div class="loading-step-text">Initializing...</div>
      <div class="loading-bar-container">
        <div class="loading-bar-progress"></div>
      </div>
      <div class="loading-percentage">0%</div>
    </div>
  `;

  // Add to document body
  document.body.appendChild(loadingPopup);

  // Define the loading steps and their percentage values with more detailed descriptions
  const loadingSteps = [
    { text: "Registering episode", percentage: 25 },
    { text: "Sending data", percentage: 50 },
    { text: "Sending invitation email", percentage: 75 },
    { text: "Podcast registered successfully", percentage: 100 }
  ];

  // Function to show the loading popup with a fade-in effect
  function showLoadingPopup() {
    loadingPopup.style.display = "flex";
    // Reset progress
    updateProgress(0, "Initializing...");

    // Force reflow to ensure animation plays
    void loadingPopup.offsetWidth;
  }

  // Function to hide the loading popup with a fade-out effect
  function hideLoadingPopup() {
    loadingPopup.style.opacity = "0";
    setTimeout(() => {
      loadingPopup.style.display = "none";
      loadingPopup.style.opacity = "1";
    }, 300);
  }

  // Function to update the progress bar with smooth animation
  function updateProgress(percentage, stepText) {
    const progressBar = loadingPopup.querySelector(".loading-bar-progress");
    const percentageText = loadingPopup.querySelector(".loading-percentage");
    const stepTextElement = loadingPopup.querySelector(".loading-step-text");

    // Animate the progress bar with a smooth transition
    progressBar.style.width = `${percentage}%`;

    // Update the percentage text with animation
    animateCounter(
      percentageText,
      Number.parseInt(percentageText.textContent),
      percentage
    );

    // Update the step text with a fade effect
    if (stepText) {
      fadeElement(stepTextElement, () => {
        stepTextElement.textContent = stepText;
      });
    }
  }

  // Helper function to animate counter
  function animateCounter(element, start, end) {
    const duration = 800; // ms
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsedTime = currentTime - startTime;

      if (elapsedTime < duration) {
        const value = Math.round(
          easeOutQuad(elapsedTime, start, end - start, duration)
        );
        element.textContent = `${value}%`;
        requestAnimationFrame(updateCounter);
      } else {
        element.textContent = `${end}%`;
      }
    }

    requestAnimationFrame(updateCounter);
  }

  // Easing function for smooth animation
  function easeOutQuad(t, b, c, d) {
    t /= d;
    return -c * t * (t - 2) + b;
  }

  // Helper function to fade element
  function fadeElement(element, callback) {
    element.style.opacity = "0";
    setTimeout(() => {
      callback();
      element.style.opacity = "1";
    }, 200);
  }

  // Function to process a specific step with improved animation
  function processStep(stepIndex) {
    if (stepIndex >= loadingSteps.length) {
      // All steps completed
      updateProgress(100, "Complete!");
      return;
    }

    const step = loadingSteps[stepIndex];
    updateProgress(step.percentage, step.text);
  }

  return {
    showLoadingPopup,
    hideLoadingPopup,
    updateProgress,
    processStep,
    loadingSteps
  };
}
