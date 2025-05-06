const questions = [
    {
        text: "Do you enjoy working collaboratively as part of a team?",
        dealbreaker: false,
        options: [
            { text: "Yes, I thrive in team environments!", value: true },
            { text: "No, I prefer working alone.", value: false }
        ]
    },
    {
        text: "Are you available to work standard office hours (9 AM - 5 PM)?",
        dealbreaker: false,
        options: [
            { text: "Yes, those hours work for me.", value: true },
            { text: "No, my availability varies.", value: false }
        ]
    },
    {
        text: "Do you enjoy working remotely and have experience with remote work?",
        dealbreaker: false,
        options: [
            { text: "Yes, I enjoy remote work and have experience.", value: true },
            { text: "No, I prefer an office setting or have no remote experience.", value: false }
        ]
    },
    {
        text: "Are you excited about working in a fast-paced environment where things change quickly and creativity is valued?",
        dealbreaker: false,
        options: [
            { text: "Absolutely, that sounds exciting!", value: true },
            { text: "I prefer more stable and predictable environments.", value: false }
        ]
    },
    {
        text: "Do you believe creativity and innovation are key to success in your work?",
        dealbreaker: false,
        options: [
            { text: "Yes, creativity and innovation are crucial.", value: true },
            { text: "I focus more on established processes.", value: false }
        ]
    },
    {
        text: "Are you open to constantly learning and adapting to new challenges as you grow in your role?",
        dealbreaker: false,
        options: [
            { text: "Yes, I'm a lifelong learner.", value: true },
            { text: "I prefer to stick to what I know.", value: false }
        ]
    },
    {
        text: "Do you understand that we work as a team where you must rely on your own drive and motivation, yet collaboration is key and we support each other in pairs and groups?",
        dealbreaker: true,
        options: [
            { text: "Yes, I understand and agree.", value: true },
            { text: "No, that's not clear or I disagree.", value: false }
        ]
    },
    {
        text: "Would you be comfortable participating in virtual meetings and working with online collaboration tools regularly?",
        dealbreaker: false,
        options: [
            { text: "Yes, I'm comfortable with virtual collaboration.", value: true },
            { text: "No, I have reservations about that.", value: false }
        ]
    },
    {
        text: "If hired, are you ready to contribute to a company that values creativity, growth, and continuous improvement, even during challenging times?",
        dealbreaker: false,
        options: [
            { text: "Yes, I'm ready to contribute!", value: true },
            { text: "I'm not sure I'm up for that.", value: false }
        ]
    },
    {
        text: "Are you adaptable and open to change as the company grows and evolves?",
        dealbreaker: true,
        options: [
            { text: "Yes, I embrace change and adaptability.", value: true },
            { text: "No, I prefer things to remain consistent.", value: false }
        ]
    }
];

let currentQuestionIndex = 0;
let failedAnswers = 0;

function renderCurrentQuestion() {
    if (currentQuestionIndex >= questions.length) return;

    const questionData = questions[currentQuestionIndex];
    const questionTextElement = document.getElementById('question-text');
    const optionButton1 = document.getElementById('option-button-1');
    const optionButton2 = document.getElementById('option-button-2');

    if (questionTextElement) {
        questionTextElement.textContent = questionData.text;
    }

    if (optionButton1 && questionData.options[0]) {
        optionButton1.textContent = questionData.options[0].text;
        optionButton1.onclick = () => nextQuestion(questionData.options[0].value);
    }

    if (optionButton2 && questionData.options[1]) {
        optionButton2.textContent = questionData.options[1].text;
        optionButton2.onclick = () => nextQuestion(questionData.options[1].value);
    }
}

window.nextQuestion = function(answerValue) {
    updateProgress();

    if (!answerValue) { // answerValue is now directly true or false
        failedAnswers++;
    }

    if (questions[currentQuestionIndex].dealbreaker && !answerValue) {
        showResult(false);
        return;
    }

    currentQuestionIndex++;
    if (currentQuestionIndex < questions.length) {
        renderCurrentQuestion(); // Display the next question
    } else {
        showResult(failedAnswers < 5);
    }
}

window.showResult = function(isPass) {
    const resultContainer = document.getElementById('result-container');
    const questionContainer = document.getElementById('question-container');
    const liaDetailsSection = document.getElementById('lia-details-section');

    if (resultContainer && questionContainer && liaDetailsSection) {
        if (isPass) {
            resultContainer.textContent = "You made the cut, welcome to the team! Please provide your details below so we can get you started with the onboarding process.";
            resultContainer.className = 'result-message pass';
            liaDetailsSection.style.display = 'block'; // Show the details form
        } else {
            resultContainer.textContent = "Thank you for taking the time, but as it looks you will not be a great fit for our team given your responses.";
            resultContainer.className = 'result-message fail';
            liaDetailsSection.style.display = 'none'; // Ensure details form is hidden on fail
        }

        questionContainer.style.display = 'none';
        resultContainer.style.display = 'block';
    }
}

window.updateProgress = function() {
    const progressBarElement = document.getElementById('progress-bar');
    if (progressBarElement) {
        // Ensure currentQuestionIndex for progress is capped at questions.length
        const progressIndex = Math.min(currentQuestionIndex + 1, questions.length);
        const progress = (progressIndex / questions.length) * 100;
        progressBarElement.style.width = progress + '%';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    renderCurrentQuestion(); // Display the first question when the page loads

    const liaContactForm = document.getElementById('lia-contact-form');
    if (liaContactForm) {
        liaContactForm.addEventListener('submit', async function(event) { // Made async
            event.preventDefault();
            const name = document.getElementById('lia-name').value.trim();
            const email = document.getElementById('lia-email').value.trim();
            const phone = document.getElementById('lia-phone').value.trim();
            const schoolAndStudy = document.getElementById('lia-school-study').value.trim(); // Get new field

            if (!name || !email || !phone || !schoolAndStudy) { // Validate new field
                alert('Please fill in all fields.');
                return;
            }
            // Basic email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('Please enter a valid email address.');
                return;
            }

            const formData = { name, email, phone, schoolAndStudy };
            console.log('LIA Details Submitted:', formData);

            // Disable button during submission
            const submitButton = liaContactForm.querySelector('.submit-btn');
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';

            try {
                const response = await fetch('/lia/submit-inquiry', { // Backend endpoint
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        // Redirect to Google Drive on successful backend processing
                        window.location.href = "https://drive.google.com/drive/folders/1qQeAYxkNDU0uCaBkJuaTzx7im5sRP62F";
                    } else {
                        alert(result.error || 'Failed to submit inquiry. Please try again.');
                        submitButton.disabled = false;
                        submitButton.textContent = 'Ask For Access';
                    }
                } else {
                    alert('An error occurred while submitting your inquiry. Please try again.');
                    submitButton.disabled = false;
                    submitButton.textContent = 'Ask For Access';
                }
            } catch (error) {
                console.error('Error submitting LIA inquiry:', error);
                alert('An error occurred. Please check your connection and try again.');
                submitButton.disabled = false;
                submitButton.textContent = 'Ask For Access';
            }
        });
    }

    const liaPhoneInput = document.getElementById('lia-phone');
    if (liaPhoneInput) {
        liaPhoneInput.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
            e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
        });
    }
});