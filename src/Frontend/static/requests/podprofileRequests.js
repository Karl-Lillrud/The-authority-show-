export async function postPodcastData(podName, podRss) {
    try {
        const response = await fetch("/post_podcast_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ podName, podRss })
        });

        const result = await response.json();

        if (response.ok) {
            return result.redirectUrl; // Return the redirect URL
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error("Failed to register podcast:", error);
        throw error;
    }
}

