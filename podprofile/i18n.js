// i18n.js - Internationalization Support

const translations = {
    en: {
        "title.podProfile": "Pod Profile",
        "headings.podProfile": "Pod Profile Details",
        "labels.podName": "Pod Name",
        "labels.podRss": "RSS Feed",
        "buttons.submit": "Submit",
        "notifications.defaultToast": "Action completed successfully."
    },
    es: {
        "title.podProfile": "Perfil del Podcast",
        "headings.podProfile": "Detalles del Perfil del Podcast",
        "labels.podName": "Nombre del Podcast",
        "labels.podRss": "Fuente RSS",
        "buttons.submit": "Enviar",
        "notifications.defaultToast": "Acción completada con éxito."
    },
    fr: {
        "title.podProfile": "Profil du Podcast",
        "headings.podProfile": "Détails du Profil du Podcast",
        "labels.podName": "Nom du Podcast",
        "labels.podRss": "Flux RSS",
        "buttons.submit": "Soumettre",
        "notifications.defaultToast": "Action complétée avec succès."
    }
};

function initializeI18n() {
    const userLang = localStorage.getItem("language") || "en";
    setLanguage(userLang);
}

function setLanguage(lang) {
    if (!translations[lang]) lang = "en";
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (translations[lang][key]) {
            el.innerText = translations[lang][key];
        }
    });
    localStorage.setItem("language", lang);
}

document.getElementById("language-selector")?.addEventListener("change", (e) => {
    setLanguage(e.target.value);
});

document.addEventListener("DOMContentLoaded", initializeI18n);
