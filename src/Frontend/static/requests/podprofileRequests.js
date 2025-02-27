async function postPodcastData(podName, podRss) {
    try {
        const response = await fetch("/add_podcasts", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ podName, podRss })
        });

        const result = await response.json();

        if (response.ok) {
            return result.redirect_url; // Return the redirect URL
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error("Failed to register podcast:", error);
        throw error;
    }
}

