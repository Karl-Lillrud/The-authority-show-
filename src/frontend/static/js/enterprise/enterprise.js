document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('enterpriseForm');
    const successMessage = document.getElementById('successMessage');
    const countrySelector = document.querySelector('.country-selector');
    const selectedFlag = document.getElementById('selected-flag');
    const countryList = document.getElementById('country-list');
    const countrySearch = document.getElementById('country-search');
    
    // Comprehensive country data with dial codes
    const countries = [
        { name: "Afghanistan", code: "af", dialCode: "+93" },
        { name: "Albania", code: "al", dialCode: "+355" },
        { name: "Algeria", code: "dz", dialCode: "+213" },
        { name: "Andorra", code: "ad", dialCode: "+376" },
        { name: "Angola", code: "ao", dialCode: "+244" },
        { name: "Antigua and Barbuda", code: "ag", dialCode: "+1" },
        { name: "Argentina", code: "ar", dialCode: "+54" },
        { name: "Armenia", code: "am", dialCode: "+374" },
        { name: "Australia", code: "au", dialCode: "+61" },
        { name: "Austria", code: "at", dialCode: "+43" },
        { name: "Azerbaijan", code: "az", dialCode: "+994" },
        { name: "Bahamas", code: "bs", dialCode: "+1" },
        { name: "Bahrain", code: "bh", dialCode: "+973" },
        { name: "Bangladesh", code: "bd", dialCode: "+880" },
        { name: "Barbados", code: "bb", dialCode: "+1" },
        { name: "Belarus", code: "by", dialCode: "+375" },
        { name: "Belgium", code: "be", dialCode: "+32" },
        { name: "Belize", code: "bz", dialCode: "+501" },
        { name: "Benin", code: "bj", dialCode: "+229" },
        { name: "Bhutan", code: "bt", dialCode: "+975" },
        { name: "Bolivia", code: "bo", dialCode: "+591" },
        { name: "Bosnia and Herzegovina", code: "ba", dialCode: "+387" },
        { name: "Botswana", code: "bw", dialCode: "+267" },
        { name: "Brazil", code: "br", dialCode: "+55" },
        { name: "Brunei", code: "bn", dialCode: "+673" },
        { name: "Bulgaria", code: "bg", dialCode: "+359" },
        { name: "Burkina Faso", code: "bf", dialCode: "+226" },
        { name: "Burundi", code: "bi", dialCode: "+257" },
        { name: "Cambodia", code: "kh", dialCode: "+855" },
        { name: "Cameroon", code: "cm", dialCode: "+237" },
        { name: "Canada", code: "ca", dialCode: "+1" },
        { name: "Cape Verde", code: "cv", dialCode: "+238" },
        { name: "Central African Republic", code: "cf", dialCode: "+236" },
        { name: "Chad", code: "td", dialCode: "+235" },
        { name: "Chile", code: "cl", dialCode: "+56" },
        { name: "China", code: "cn", dialCode: "+86" },
        { name: "Colombia", code: "co", dialCode: "+57" },
        { name: "Comoros", code: "km", dialCode: "+269" },
        { name: "Congo", code: "cg", dialCode: "+242" },
        { name: "Costa Rica", code: "cr", dialCode: "+506" },
        { name: "Croatia", code: "hr", dialCode: "+385" },
        { name: "Cuba", code: "cu", dialCode: "+53" },
        { name: "Cyprus", code: "cy", dialCode: "+357" },
        { name: "Czech Republic", code: "cz", dialCode: "+420" },
        { name: "Denmark", code: "dk", dialCode: "+45" },
        { name: "Djibouti", code: "dj", dialCode: "+253" },
        { name: "Dominica", code: "dm", dialCode: "+1" },
        { name: "Dominican Republic", code: "do", dialCode: "+1" },
        { name: "Ecuador", code: "ec", dialCode: "+593" },
        { name: "Egypt", code: "eg", dialCode: "+20" },
        { name: "El Salvador", code: "sv", dialCode: "+503" },
        { name: "Equatorial Guinea", code: "gq", dialCode: "+240" },
        { name: "Eritrea", code: "er", dialCode: "+291" },
        { name: "Estonia", code: "ee", dialCode: "+372" },
        { name: "Eswatini", code: "sz", dialCode: "+268" },
        { name: "Ethiopia", code: "et", dialCode: "+251" },
        { name: "Fiji", code: "fj", dialCode: "+679" },
        { name: "Finland", code: "fi", dialCode: "+358" },
        { name: "France", code: "fr", dialCode: "+33" },
        { name: "Gabon", code: "ga", dialCode: "+241" },
        { name: "Gambia", code: "gm", dialCode: "+220" },
        { name: "Georgia", code: "ge", dialCode: "+995" },
        { name: "Germany", code: "de", dialCode: "+49" },
        { name: "Ghana", code: "gh", dialCode: "+233" },
        { name: "Greece", code: "gr", dialCode: "+30" },
        { name: "Grenada", code: "gd", dialCode: "+1" },
        { name: "Guatemala", code: "gt", dialCode: "+502" },
        { name: "Guinea", code: "gn", dialCode: "+224" },
        { name: "Guinea-Bissau", code: "gw", dialCode: "+245" },
        { name: "Guyana", code: "gy", dialCode: "+592" },
        { name: "Haiti", code: "ht", dialCode: "+509" },
        { name: "Honduras", code: "hn", dialCode: "+504" },
        { name: "Hong Kong", code: "hk", dialCode: "+852" },
        { name: "Hungary", code: "hu", dialCode: "+36" },
        { name: "Iceland", code: "is", dialCode: "+354" },
        { name: "India", code: "in", dialCode: "+91" },
        { name: "Indonesia", code: "id", dialCode: "+62" },
        { name: "Iran", code: "ir", dialCode: "+98" },
        { name: "Iraq", code: "iq", dialCode: "+964" },
        { name: "Ireland", code: "ie", dialCode: "+353" },
        { name: "Israel", code: "il", dialCode: "+972" },
        { name: "Italy", code: "it", dialCode: "+39" },
        { name: "Jamaica", code: "jm", dialCode: "+1" },
        { name: "Japan", code: "jp", dialCode: "+81" },
        { name: "Jordan", code: "jo", dialCode: "+962" },
        { name: "Kazakhstan", code: "kz", dialCode: "+7" },
        { name: "Kenya", code: "ke", dialCode: "+254" },
        { name: "Kiribati", code: "ki", dialCode: "+686" },
        { name: "Kuwait", code: "kw", dialCode: "+965" },
        { name: "Kyrgyzstan", code: "kg", dialCode: "+996" },
        { name: "Laos", code: "la", dialCode: "+856" },
        { name: "Latvia", code: "lv", dialCode: "+371" },
        { name: "Lebanon", code: "lb", dialCode: "+961" },
        { name: "Lesotho", code: "ls", dialCode: "+266" },
        { name: "Liberia", code: "lr", dialCode: "+231" },
        { name: "Libya", code: "ly", dialCode: "+218" },
        { name: "Liechtenstein", code: "li", dialCode: "+423" },
        { name: "Lithuania", code: "lt", dialCode: "+370" },
        { name: "Luxembourg", code: "lu", dialCode: "+352" },
        { name: "Madagascar", code: "mg", dialCode: "+261" },
        { name: "Malawi", code: "mw", dialCode: "+265" },
        { name: "Malaysia", code: "my", dialCode: "+60" },
        { name: "Maldives", code: "mv", dialCode: "+960" },
        { name: "Mali", code: "ml", dialCode: "+223" },
        { name: "Malta", code: "mt", dialCode: "+356" },
        { name: "Marshall Islands", code: "mh", dialCode: "+692" },
        { name: "Mauritania", code: "mr", dialCode: "+222" },
        { name: "Mauritius", code: "mu", dialCode: "+230" },
        { name: "Mexico", code: "mx", dialCode: "+52" },
        { name: "Micronesia", code: "fm", dialCode: "+691" },
        { name: "Moldova", code: "md", dialCode: "+373" },
        { name: "Monaco", code: "mc", dialCode: "+377" },
        { name: "Mongolia", code: "mn", dialCode: "+976" },
        { name: "Montenegro", code: "me", dialCode: "+382" },
        { name: "Morocco", code: "ma", dialCode: "+212" },
        { name: "Mozambique", code: "mz", dialCode: "+258" },
        { name: "Myanmar", code: "mm", dialCode: "+95" },
        { name: "Namibia", code: "na", dialCode: "+264" },
        { name: "Nauru", code: "nr", dialCode: "+674" },
        { name: "Nepal", code: "np", dialCode: "+977" },
        { name: "Netherlands", code: "nl", dialCode: "+31" },
        { name: "New Zealand", code: "nz", dialCode: "+64" },
        { name: "Nicaragua", code: "ni", dialCode: "+505" },
        { name: "Niger", code: "ne", dialCode: "+227" },
        { name: "Nigeria", code: "ng", dialCode: "+234" },
        { name: "North Korea", code: "kp", dialCode: "+850" },
        { name: "North Macedonia", code: "mk", dialCode: "+389" },
        { name: "Norway", code: "no", dialCode: "+47" },
        { name: "Oman", code: "om", dialCode: "+968" },
        { name: "Pakistan", code: "pk", dialCode: "+92" },
        { name: "Palau", code: "pw", dialCode: "+680" },
        { name: "Palestine", code: "ps", dialCode: "+970" },
        { name: "Panama", code: "pa", dialCode: "+507" },
        { name: "Papua New Guinea", code: "pg", dialCode: "+675" },
        { name: "Paraguay", code: "py", dialCode: "+595" },
        { name: "Peru", code: "pe", dialCode: "+51" },
        { name: "Philippines", code: "ph", dialCode: "+63" },
        { name: "Poland", code: "pl", dialCode: "+48" },
        { name: "Portugal", code: "pt", dialCode: "+351" },
        { name: "Qatar", code: "qa", dialCode: "+974" },
        { name: "Romania", code: "ro", dialCode: "+40" },
        { name: "Russia", code: "ru", dialCode: "+7" },
        { name: "Rwanda", code: "rw", dialCode: "+250" },
        { name: "Saint Kitts and Nevis", code: "kn", dialCode: "+1" },
        { name: "Saint Lucia", code: "lc", dialCode: "+1" },
        { name: "Saint Vincent and the Grenadines", code: "vc", dialCode: "+1" },
        { name: "Samoa", code: "ws", dialCode: "+685" },
        { name: "San Marino", code: "sm", dialCode: "+378" },
        { name: "Sao Tome and Principe", code: "st", dialCode: "+239" },
        { name: "Saudi Arabia", code: "sa", dialCode: "+966" },
        { name: "Senegal", code: "sn", dialCode: "+221" },
        { name: "Serbia", code: "rs", dialCode: "+381" },
        { name: "Seychelles", code: "sc", dialCode: "+248" },
        { name: "Sierra Leone", code: "sl", dialCode: "+232" },
        { name: "Singapore", code: "sg", dialCode: "+65" },
        { name: "Slovakia", code: "sk", dialCode: "+421" },
        { name: "Slovenia", code: "si", dialCode: "+386" },
        { name: "Solomon Islands", code: "sb", dialCode: "+677" },
        { name: "Somalia", code: "so", dialCode: "+252" },
        { name: "South Africa", code: "za", dialCode: "+27" },
        { name: "South Korea", code: "kr", dialCode: "+82" },
        { name: "South Sudan", code: "ss", dialCode: "+211" },
        { name: "Spain", code: "es", dialCode: "+34" },
        { name: "Sri Lanka", code: "lk", dialCode: "+94" },
        { name: "Sudan", code: "sd", dialCode: "+249" },
        { name: "Suriname", code: "sr", dialCode: "+597" },
        { name: "Sweden", code: "se", dialCode: "+46" },
        { name: "Switzerland", code: "ch", dialCode: "+41" },
        { name: "Syria", code: "sy", dialCode: "+963" },
        { name: "Taiwan", code: "tw", dialCode: "+886" },
        { name: "Tajikistan", code: "tj", dialCode: "+992" },
        { name: "Tanzania", code: "tz", dialCode: "+255" },
        { name: "Thailand", code: "th", dialCode: "+66" },
        { name: "Timor-Leste", code: "tl", dialCode: "+670" },
        { name: "Togo", code: "tg", dialCode: "+228" },
        { name: "Tonga", code: "to", dialCode: "+676" },
        { name: "Trinidad and Tobago", code: "tt", dialCode: "+1" },
        { name: "Tunisia", code: "tn", dialCode: "+216" },
        { name: "Turkey", code: "tr", dialCode: "+90" },
        { name: "Turkmenistan", code: "tm", dialCode: "+993" },
        { name: "Tuvalu", code: "tv", dialCode: "+688" },
        { name: "Uganda", code: "ug", dialCode: "+256" },
        { name: "Ukraine", code: "ua", dialCode: "+380" },
        { name: "United Arab Emirates", code: "ae", dialCode: "+971" },
        { name: "United Kingdom", code: "gb", dialCode: "+44" },
        { name: "United States", code: "us", dialCode: "+1" },
        { name: "Uruguay", code: "uy", dialCode: "+598" },
        { name: "Uzbekistan", code: "uz", dialCode: "+998" },
        { name: "Vanuatu", code: "vu", dialCode: "+678" },
        { name: "Vatican City", code: "va", dialCode: "+39" },
        { name: "Venezuela", code: "ve", dialCode: "+58" },
        { name: "Vietnam", code: "vn", dialCode: "+84" },
        { name: "Yemen", code: "ye", dialCode: "+967" },
        { name: "Zambia", code: "zm", dialCode: "+260" },
        { name: "Zimbabwe", code: "zw", dialCode: "+263" }
    ];
    
    // Default country code (selected on page load)
    let selectedDialCode = "+1";
    
    // Initialize country list
    function initializeCountryList() {
        // Populate the country dropdown
        countries.forEach(country => {
            const listItem = document.createElement('li');
            listItem.dataset.code = country.code;
            listItem.dataset.dialCode = country.dialCode;
            
            // Load flag from flagcdn
            listItem.innerHTML = `
                <div class="flag ${country.code}" style="background-image: url('https://flagcdn.com/w20/${country.code}.png');"></div>
                <span class="country-name">${country.name}</span>
                <span class="dial-code">${country.dialCode}</span>
            `;
            
            listItem.addEventListener('click', () => selectCountry(country));
            countryList.appendChild(listItem);
        });
        
        // Toggle dropdown on click
        if (selectedFlag) {
            selectedFlag.addEventListener('click', toggleDropdown);
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (countrySelector && !countrySelector.contains(e.target)) {
                closeDropdown();
            }
        });
        
        // Handle search functionality
        if (countrySearch) {
            countrySearch.addEventListener('input', searchCountries);
        }
    }
    
    // Toggle country dropdown
    function toggleDropdown(event) {
        if (event) {
            event.stopPropagation();
        }
        
        if (countrySelector) {
            countrySelector.classList.toggle('open');
            if (countrySelector.classList.contains('open') && countrySearch) {
                countrySearch.focus();
            }
        }
    }
    
    // Close country dropdown
    function closeDropdown() {
        if (countrySelector) {
            countrySelector.classList.remove('open');
        }
        
        // Reset search
        if (countrySearch) {
            countrySearch.value = '';
            searchCountries();
        }
    }
    
    // Search countries
    function searchCountries() {
        const searchTerm = countrySearch ? countrySearch.value.toLowerCase() : '';
        const items = countryList ? countryList.querySelectorAll('li') : [];
        
        items.forEach(item => {
            const countryName = item.querySelector('.country-name').textContent.toLowerCase();
            const dialCode = item.querySelector('.dial-code').textContent.toLowerCase();
            
            if (countryName.includes(searchTerm) || dialCode.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Select country and update UI
    function selectCountry(country) {
        // Update the flag and dial code in the selected flag button
        if (selectedFlag) {
            const flagElement = selectedFlag.querySelector('.flag');
            const codeElement = selectedFlag.querySelector('.country-code');
            
            if (flagElement) {
                flagElement.className = `flag ${country.code}`;
                flagElement.style.backgroundImage = `url('https://flagcdn.com/w20/${country.code}.png')`;
            }
            if (codeElement) codeElement.textContent = country.dialCode;
        }
        
        // Store the selected dial code
        selectedDialCode = country.dialCode;
        
        // Close the dropdown
        closeDropdown();
        
        // Focus on phone input field
        const phoneInput = document.getElementById('phone');
        if (phoneInput) {
            phoneInput.focus();
        }
    }
    
    // Initialize the country dropdown
    initializeCountryList();
    
    // Form handling
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const phoneValue = document.getElementById('phone').value;
            
            // Ensure phone number has the country code prefix
            const fullPhone = `${selectedDialCode}${phoneValue}`;
            
            // Validate form (basic validation)
            if (!validateForm(name, email, phoneValue)) {
                return;
            }
            
            // Submit the form with the complete phone number
            submitForm({
                name: name,
                email: email,
                phone: fullPhone
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
        
        if (!phone || phone.trim() === '') {
            showError('Please enter your phone number');
            return false;
        }
        
        return true;
    }
    
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
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
});