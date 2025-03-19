export async function publishToSpotify(episodeData) {
  console.log("Starting publishToSpotify with data:", episodeData); // Log input data

  // Kontrollera om audioUrl finns i data
  if (!episodeData.audioUrl) {
      console.error("Error: 'audioUrl' is missing");
      throw new Error("Audio URL is missing. Please provide a valid audio URL.");
  }

  const response = await fetch("/publish/spotify", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify(episodeData)
  });

  console.log("Received response from /publish/spotify:", response); // Log response object

  if (!response.ok) {
      const errorData = await response.json();
      console.error("Error response from /publish/spotify:", errorData); // Log error details
      throw new Error(errorData.error || "An error occurred while publishing the episode.");
  }

  // Parse the response JSON if successful
  const result = await response.json();
  console.log("Successfully published to Spotify:", result); // Log success result
  return result;
}

// Example usage:
// const episodeData = {
//     title: 'Episode Title',
//     description: 'Episode Description',
//     audioUrl: 'C:\\Users\\sarwe\\Desktop\\LIa\\audio.mp3' // Local path to the audio file
// };
// publishToSpotify(episodeData)
//     .then(data => console.log(data))
//     .catch(error => console.error(error));
