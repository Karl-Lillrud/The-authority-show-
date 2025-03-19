document.addEventListener('DOMContentLoaded', function() {
  const guestForm = document.getElementById('guest-signup-form');
  guestForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('guest-email').value;
    // Here you can integrate your email sending service (e.g., EmailJS) if needed.
    // For now, we'll simply show a confirmation alert.
    alert('Thank you! Your application as a guest has been submitted using: ' + email);
    guestForm.reset();
  });
});