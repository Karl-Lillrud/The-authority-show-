function registerEpisode(formData) {
    const url = "/register_episode";  // Endpoint for registering the episode

    // Create a new FormData object to append the form fields
    const data = new FormData();
    data.append("podcastId", formData.podcastId);
    data.append("title", formData.title);
    data.append("description", formData.description);
    data.append("publishDate", formData.publishDate);
    data.append("duration", formData.duration);
    data.append("guestId", formData.guestId);
    data.append("status", formData.status);

    // Append all files to the form data
    for (let i = 0; i < formData.audio.length; i++) {
        console.log('Appending file:', formData.audio[i]); // Log each file being appended
        data.append("audio", formData.audio[i]);  // 'audio' corresponds to the name of the file input in the form
    }

    // Send the POST request with multipart/form-data (automatically handled by FormData)
    fetch(url, {
        method: 'POST',
        body: data,  // FormData object contains the file and form fields
    })
    .then(response => response.json())
    .then(result => {
        console.log('Result from registerEpisode:', result);
    })
    .catch(error => {
        console.error('Error during episode registration:', error);
    });
}
