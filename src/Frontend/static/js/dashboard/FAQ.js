document.addEventListener('DOMContentLoaded', function() {
  const searchBtn = document.getElementById('faq-search-btn');
  const searchInput = document.getElementById('faq-search');

  if (!searchBtn || !searchInput) return;

  function removeHighlights() {
    document.querySelectorAll('.faq-item').forEach(item => {
      // Ta bort tidigare <mark>-taggar genom att återställa texten
      item.innerHTML = item.innerHTML.replace(/<mark>(.*?)<\/mark>/gi, '$1');
      item.style.background = '';
    });
  }

  searchBtn.onclick = function() {
    const query = searchInput.value.trim();
    if (!query) return;

    removeHighlights();

    const items = document.querySelectorAll('.faq-item');
    let found = false;
    const regex = new RegExp(`(${query})`, 'gi');

    for (const item of items) {
      let html = item.innerHTML;
      if (html.toLowerCase().includes(query.toLowerCase())) {
        // Markera alla träffar med <mark>
        html = html.replace(regex, '<mark>$1</mark>');
        item.innerHTML = html;
        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
        found = true;
        break; // Endast första träffen markeras och scrollas till
      }
    }
    if (!found) {
      alert('No match found!');
    }
  };

  // Gör så att Enter i input också söker
  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      searchBtn.click();
    }
  });
});