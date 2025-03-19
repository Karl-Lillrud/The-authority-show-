document.getElementById('publishPodcastForm').addEventListener('submit', function (e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const audioUrl = document.getElementById('audioUrl').value;

    // Validate title
    if (!title) {
        alert("Please provide a title");
        return;
    }

    // Validate description
    if (!description) {
        alert("Please provide a description");
        return;
    }

    // Make sure the audio URL is valid (optional, can be handled backend)
    if (!audioUrl) { 
        alert("Please provide an audio URL");
        return;
    }

    // Log form data for debugging
    console.log('Form Data:', { title, description, audioUrl });

    fetch('/publish/spotify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, description, audioUrl })
    })
    .then(response => response.json())
    .then(data => {
        // Log response data for debugging
        console.log('Response Data:', data);

        if (data.error) {
            console.error('Error:', data.error);
            alert('Failed to publish podcast on Spotify.');
        } else {
            console.log('Podcast publicerad:', data);
            alert('Podcast publicerad på Spotify!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while publishing the podcast.');
    });
});
