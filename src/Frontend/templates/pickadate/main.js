/* js/main.js */
document.addEventListener('DOMContentLoaded', function() {
    i18next
      .use(i18nextHttpBackend)
      .init({
        lng: 'en',
        fallbackLng: 'en',
        backend: {
          loadPath: '/locales/{{lng}}/translation.json'
        }
      }, function(err, t) {
        if (err) return console.error(err);
        updateContent();
      });
  
    function updateContent() {
      document.querySelectorAll('[data-i18n]').forEach(function(element) {
        var key = element.getAttribute('data-i18n');
        element.textContent = i18next.t(key);
      });
      document.querySelectorAll('[data-placeholder-key]').forEach(function(element) {
        var key = element.getAttribute('data-placeholder-key');
        element.setAttribute('placeholder', i18next.t(key));
      });
    }
  
    document.getElementById('lang-en').addEventListener('click', function() { changeLanguage('en'); });
    document.getElementById('lang-ar').addEventListener('click', function() { changeLanguage('ar'); });
    document.getElementById('lang-es').addEventListener('click', function() { changeLanguage('es'); });
    document.getElementById('lang-de').addEventListener('click', function() { changeLanguage('de'); });
    document.getElementById('lang-fr').addEventListener('click', function() { changeLanguage('fr'); });
    document.getElementById('lang-zh').addEventListener('click', function() { changeLanguage('zh'); });
  
    function changeLanguage(lng) {
      i18next.changeLanguage(lng, function(err, t) {
        if (err) return console.error(err);
        updateContent();
        document.body.dir = (lng === 'ar') ? 'rtl' : 'ltr';
      });
    }
  
    document.getElementById('booking-form').addEventListener('submit', function(e) {
      e.preventDefault();
      var formData = {
        guestName: document.getElementById('guestName').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        socialMedia: document.getElementById('socialMedia').value,
        podcastName: document.getElementById('podcastName').value,
        preferredTime: document.getElementById('preferredTime').value,
        meetingPreferences: document.getElementById('meetingPreferences').value,
        upload: document.getElementById('upload').files[0]
      };
      console.log("Form Data:", formData);
      alert(i18next.t('form.submit') + " " + i18next.t('header.title'));
    });
  });
  