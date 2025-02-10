document.addEventListener('DOMContentLoaded', function () {
    // Initialize i18next for translations
    i18next
        .use(i18nextHttpBackend)
        .init({
            lng: 'en',
            fallbackLng: 'en',
            backend: {
                loadPath: '/locales/{{lng}}/translation.json'
            }
        }, function (err, t) {
            if (err) return console.error(err);
            updateContent();
        });

    function updateContent() {
        document.querySelectorAll('[data-i18n]').forEach(function (element) {
            var key = element.getAttribute('data-i18n');
            element.textContent = i18next.t(key);
        });

        document.querySelectorAll('[data-placeholder-key]').forEach(function (element) {
            var key = element.getAttribute('data-placeholder-key');
            element.setAttribute('placeholder', i18next.t(key));
        });
    }

    // Language switcher
    document.getElementById('lang-en').addEventListener('click', function () { changeLanguage('en'); });
    document.getElementById('lang-ar').addEventListener('click', function () { changeLanguage('ar'); });
    document.getElementById('lang-es').addEventListener('click', function () { changeLanguage('es'); });
    document.getElementById('lang-de').addEventListener('click', function () { changeLanguage('de'); });
    document.getElementById('lang-fr').addEventListener('click', function () { changeLanguage('fr'); });
    document.getElementById('lang-zh').addEventListener('click', function () { changeLanguage('zh'); });

    function changeLanguage(lng) {
        i18next.changeLanguage(lng, function (err, t) {
            if (err) return console.error(err);
            updateContent();
            document.body.dir = (lng === 'ar') ? 'rtl' : 'ltr';
        });
    }

    // Fetch available slots from the backend
    function fetchAvailableSlots() {
        fetch('/available-slots')
            .then(response => response.json())
            .then(slots => {
                const timeSelect = document.getElementById('preferredTime');
                timeSelect.innerHTML = ''; // Clear existing options

                slots.forEach(slot => {
                    const option = document.createElement('option');
                    option.value = slot.start;
                    option.textContent = `${new Date(slot.start).toLocaleString()} - ${new Date(slot.end).toLocaleString()}`;
                    timeSelect.appendChild(option);
                });

                if (slots.length === 0) {
                    timeSelect.innerHTML = `<option disabled>No available slots</option>`;
                }
            })
            .catch(error => console.error('Error fetching slots:', error));
    }

    // Call fetchAvailableSlots on page load
    fetchAvailableSlots();

    // Form submission logic
    document.getElementById('booking-form').addEventListener('submit', function (e) {
        e.preventDefault();

        var formData = new FormData(this);

        fetch('/book', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.message === 'Booking Successful') {
                    alert(i18next.t('form.success') + " Booking ID: " + data.bookingId);
                } else {
                    alert(i18next.t('form.error') + " " + data.error);
                }
            })
            .catch(error => console.error('Error:', error));
    });
});
