document.addEventListener("DOMContentLoaded", () => {
    const transcriptContainer = document.getElementById("transcript-container");
    const episodeId = transcriptContainer.dataset.episodeId;  // Get episode ID from the data-attribute
    const audio = document.getElementById("audio");

    // Ensure episode ID is present
    if (episodeId) {
        fetch(`/get_transcript?episode_id=${episodeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                transcriptContainer.innerHTML = "No transcript available for this episode.";
            } else if (data && data.length > 0) {
                // Populate the transcript container with the data
                const transcriptHTML = data.map(segment => `
                    <p>
                        <span class="timestamp" data-time="${segment.start}">[${formatTime(segment.start)}]</span> 
                        ${segment.text}
                    </p>
                `).join("");
                transcriptContainer.innerHTML = transcriptHTML;

                // Add click event listener to all timestamps
                const timestamps = document.querySelectorAll('.timestamp');
                timestamps.forEach(timestamp => {
                    timestamp.addEventListener('click', (e) => {
                        const time = parseFloat(e.target.dataset.time);
                        audio.currentTime = time;  // Jump to the clicked timestamp in the audio
                        audio.play();
                    });
                });
            } else {
                transcriptContainer.innerHTML = "Transcript data is missing or malformed.";
            }
        })
        .catch(error => {
            console.error("Error fetching transcript:", error);
            transcriptContainer.innerHTML = "Failed to load transcript.";
        });
    } else {
        transcriptContainer.innerHTML = "No episode ID provided.";
    }

    // Highlight the current transcript line while audio plays
    audio.addEventListener("timeupdate", () => {
        const currentTime = audio.currentTime;
        const timestamps = document.querySelectorAll('.timestamp');
        const transcriptLines = document.querySelectorAll('p');
        let closestTimestamp = null;
        let activeLine = null;

        // Loop through timestamps and find the closest one
        timestamps.forEach((timestamp, index) => {
            const timestampTime = parseFloat(timestamp.dataset.time);
            if (currentTime >= timestampTime && (!closestTimestamp || timestampTime > parseFloat(closestTimestamp.dataset.time))) {
                closestTimestamp = timestamp;
                activeLine = transcriptLines[index];  // Get the line corresponding to the timestamp
            }
        });

        // Remove highlight from previous timestamp and line
        timestamps.forEach(timestamp => {
            timestamp.classList.remove('active-timestamp');
        });
        transcriptLines.forEach(line => {
            line.classList.remove('active-line');
        });

        // Highlight the closest timestamp and the active line
        if (closestTimestamp) {
            closestTimestamp.classList.add('active-timestamp');
            activeLine.classList.add('active-line');
        }
    });
});

// Format time to MM:SS format
function formatTime(seconds) {
    let mins = Math.floor(seconds / 60);
    let secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
}
