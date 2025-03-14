async function publishToSpotify(episodeData) {
  const response = await fetch("/publish/spotify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(episodeData)
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(
      errorData.error || "An error occurred while publishing the episode."
    );
  }

  return await response.json();
}

// Example usage:
// const episodeData = {
//     title: 'Episode Title',
//     description: 'Episode Description',
//     audioUrl: 'https://example.com/audio.mp3'
// };
// publishToSpotify(episodeData)
//     .then(data => console.log(data))
//     .catch(error => console.error(error));
