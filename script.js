document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    form.addEventListener("submit", (e) => {
        const requiredFields = ["firstName", "lastName", "company", "email", "bio", "areas", "guestEmail", "guestName"];
        let isValid = true;

        requiredFields.forEach((field) => {
            const input = document.getElementById(field);
            if (!input.value.trim()) {
                isValid = false;
                alert(`${input.previousElementSibling.textContent} är obligatoriskt.`);
                input.focus();
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    });
});
