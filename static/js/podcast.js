document.addEventListener('DOMContentLoaded', function() {
    const episodesList = document.getElementById('episodesList');
    
    // Example episode data - replace with actual data from your backend
    const episodes = [
        {
            title: "The AI arsenal that could stop World War III",
            duration: "14:01",
            date: "Thu, 24 Apr 2025",
            author: "Palmer Luckey"
        },
        {
            title: "Can big tech and privacy coexist?",
            duration: "17:15",
            date: "Wed, 23 Apr 2025",
            author: "Carole Cadwalladr and Chris Anderson"
        }
        // Add more episodes as needed
    ];

    // Render episodes
    function renderEpisodes(episodes) {
        episodesList.innerHTML = episodes.map(episode => `
            <div class="episode-item">
                <h4 class="episode-title">${episode.title}</h4>
                <div class="episode-meta">
                    <span>${episode.duration}</span>
                    <span>${episode.date}</span>
                    <span>${episode.author}</span>
                </div>
            </div>
        `).join('');
    }

    // Initialize the page
    function init() {
        renderEpisodes(episodes);

        // Add event listener for podcast selection
        const podcastSelect = document.getElementById('podcastSelect');
        podcastSelect.addEventListener('change', function(e) {
            // Handle podcast change
            // You can fetch new episodes based on selection
        });

        // Add event listener for new episode button
        const newEpisodeBtn = document.querySelector('.btn-primary');
        newEpisodeBtn.addEventListener('click', function() {
            // Handle new episode creation
            console.log('Create new episode');
        });
    }

    init();
});
