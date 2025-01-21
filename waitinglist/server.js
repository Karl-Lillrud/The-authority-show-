document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded and script running");

    const inviteForm = document.querySelector('#inviteForm');
    const messageDiv = document.querySelector('#message');

    inviteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        console.log("Form submitted");

        const email = document.querySelector('#email').value;
        console.log("Email entered:", email);

        messageDiv.style.display = 'none';

        try {
            const response = await fetch('send-invitation.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ email }),
            });

            console.log("Response received:", response);
            const result = await response.text();
            console.log("Server response:", result);

            if (response.ok) {
                console.log("Email sent successfully");
                alert('Invitation email sent successfully!'); // Visa meddelande
                messageDiv.textContent = ''; // Töm meddelande-div
            } else {
                console.error("Failed to send email:", result);
                alert(`Failed to send email: ${result}`); // Visa felmeddelande
            }
        } catch (error) {
            console.error("Error sending request:", error);
            alert(`An error occurred: ${error.message}`); // Visa nätverksfel
        }

        document.querySelector('#email').value = ''; // Töm e-postfältet
    });
});
