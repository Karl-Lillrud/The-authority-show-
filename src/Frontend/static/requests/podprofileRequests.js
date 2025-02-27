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

export async function savePodProfile(data) {
    try {
        const response = await fetch("/save_podprofile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            return true;
        } else {
            throw new Error("Failed to save pod profile.");
        }
    } catch (error) {
        console.error("Error saving pod profile:", error);
        throw error;
    }
}

export async function sendInvitation(email, subject, body) {
    try {
        const response = await fetch('/send_invitation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, subject, body })
        });

        const result = await response.json();
        if (result.success) {
            console.log(`Invitation sent to ${email}`);
        } else {
            console.error(`Failed to send invitation to ${email}`);
        }
    } catch (error) {
        console.error('Error sending invitation:', error);
    }
}

