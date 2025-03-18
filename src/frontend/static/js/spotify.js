document.getElementById('publishPodcastForm').addEventListener('submit', function (e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const audioUrl = document.getElementById('audioUrl').value;

    // Make sure the audio URL is valid (optional, can be handled backend)
if (!audioUrl) { 
    alert("Please provide an audio URL");
    return;
}

    fetch('/publish/spotify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, description, audioUrl })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Podcast publicerad:', data);
        alert('Podcast publicerad på Spotify!');
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
