import translations from './translations.js';

class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.translations = translations;
        this.rtlLanguages = ['ar', 'he', 'fa', 'ur']; // Add more RTL languages as needed
        // Set language and direction on load
        document.documentElement.lang = this.currentLanguage;
        const isRTL = this.rtlLanguages.includes(this.currentLanguage);
        document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
        document.body.classList.toggle('rtl', isRTL);
        // Make sure translations are applied on load
        this.updatePageContent();
        // Make available globally
        window.languageManager = this;
    }

    setLanguage(language) {
        if (this.translations[language]) {
            this.currentLanguage = language;
            localStorage.setItem('language', language);
            document.documentElement.lang = language;
            
            // Set RTL direction for RTL languages
            const isRTL = this.rtlLanguages.includes(language);
            document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
            
            // Add RTL class to body for additional styling if needed
            document.body.classList.toggle('rtl', isRTL);
            
            this.updatePageContent();
            // Make sure it's always on window
            window.languageManager = this;
        }
    }

    getTranslation(key) {
        return this.translations[this.currentLanguage][key] || this.translations['en'][key] || key;
    }

    updatePageContent() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.getTranslation(key);
        });

        // Update all elements with data-i18n-placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.getTranslation(key);
        });

        // Update all elements with data-i18n-title attribute
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.getTranslation(key);
        });

        // Update all elements with data-i18n-aria-label attribute
        document.querySelectorAll('[data-i18n-aria-label]').forEach(element => {
            const key = element.getAttribute('data-i18n-aria-label');
            element.setAttribute('aria-label', this.getTranslation(key));
        });
    }
}

const languageManager = new LanguageManager();
window.languageManager = languageManager;
export default languageManager; 