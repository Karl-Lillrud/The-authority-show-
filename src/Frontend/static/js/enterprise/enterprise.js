document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('enterpriseForm');
    const successMessage = document.getElementById('successMessage');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const phone = document.getElementById('phone').value;
            
            // Validate form (basic validation)
            if (!validateForm(name, email, phone)) {
                return;
            }
            
            // In a real application, you would send this data to your server
            // For this example, we'll just simulate a successful submission
            submitForm({
                name: name,
                email: email,
                phone: phone
            });
        });
    }
    
    function validateForm(name, email, phone) {
        // Basic validation
        if (!name || name.trim() === '') {
            showError('Please enter your name');
            return false;
        }
        
        if (!validateEmail(email)) {
            showError('Please enter a valid email address');
            return false;
        }
        
        if (!validatePhone(phone)) {
            showError('Please enter a valid phone number');
            return false;
        }
        
        return true;
    }
    
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
    
    function validatePhone(phone) {
        // This is a simple validation that checks if the phone number has at least 10 digits
        const re = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;
        return re.test(String(phone));
    }
    
    function showError(message) {
        // In a real application, you would show an error message to the user
        alert(message);
    }
    
    async function submitForm(data) {
        const submitBtn = document.querySelector('.submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
        }

        try {
            const response = await fetch('/enterprise/submit-inquiry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                if (form) form.style.display = 'none';
                if (successMessage) successMessage.classList.remove('hidden');
                console.log('Form submitted successfully!');
            } else {
                showError(result.message || 'Failed to submit form. Please try again.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Get Contacted';
                }
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            showError('An error occurred while submitting the form. Please try again.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Get Contacted';
            }
        }
    }
    
    // Add input masking for phone number (simple implementation)
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
            e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
        });
    }
});