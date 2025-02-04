document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded and script running");

    const inviteForm = document.querySelector('#inviteForm');
    const messageDiv = document.querySelector('#message');

    inviteForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission
        console.log("Form submitted");

        const email = document.querySelector('#email').value;
        console.log("Email entered:", email);

        messageDiv.style.display = 'none';

        try {
            const response = await fetch('https://lmbc5o6v0d.execute-api.eu-north-1.amazonaws.com/Development', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            console.log("Response received:", response);
            const result = await response.json(); // Parse response as JSON
            console.log("Server response:", result);

            if (response.ok) {
                console.log("Email sent successfully");
                alert('Invitation email sent successfully!'); // Display success message
                messageDiv.textContent = ''; // Clear message div
            } else {
                console.error("Failed to send email:", result);
                alert(`Failed to send email: ${result.message || result}`); // Display error message
            }
        } catch (error) {
            console.error("Error sending request:", error);
            alert(`An error occurred: ${error.message}`); // Display network error
        }

        document.querySelector('#email').value = ''; // Clear input field
    });
});