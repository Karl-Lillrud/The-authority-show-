// Podcast Card Component
class PodcastCard {
  constructor(data) {
    this.data = data;
    this.isPlaying = false;
    this.audio = null;
  }

  formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }

  togglePlay(audioUrl) {
    if (this.isPlaying) {
      this.pauseAudio();
    } else {
      this.playAudio(audioUrl);
    }
  }

  playAudio(audioUrl) {
    if (window.currentlyPlayingAudio) {
      window.currentlyPlayingAudio.pause();
      window.currentlyPlayingAudio = null;
    }

    if (!this.audio) {
      this.audio = new Audio(audioUrl);
      this.audio.addEventListener('ended', () => {
        this.isPlaying = false;
        this.updatePlayButton();
      });
    }

    this.audio.play();
    this.isPlaying = true;
    window.currentlyPlayingAudio = this.audio;
    this.updatePlayButton();
  }

  pauseAudio() {
    if (this.audio) {
      this.audio.pause();
      this.isPlaying = false;
      window.currentlyPlayingAudio = null;
      this.updatePlayButton();
    }
  }

  updatePlayButton() {
    const button = document.querySelector(`[data-podcast-id="${this.data.id}"] .play-button`);
    if (button) {
      button.innerHTML = this.isPlaying ? 
        '<i class="fas fa-pause"></i>' : 
        '<i class="fas fa-play"></i>';
    }
  }

  render() {
    return `
      <div class="podcast-card animate-slide-up" data-podcast-id="${this.data.id}">
        <div class="podcast-thumbnail">
          <img src="${this.data.thumbnailUrl}" alt="${this.data.title}" loading="lazy">
        </div>
        <div class="podcast-content">
          <h3 class="podcast-title">${this.data.title}</h3>
          <div class="podcast-meta">
            <span class="duration-badge">
              <i class="fas fa-clock"></i>
              ${this.formatDuration(this.data.duration)}
            </span>
            <span class="release-date">
              <i class="fas fa-calendar"></i>
              ${this.formatDate(this.data.releaseDate)}
            </span>
          </div>
          <p class="podcast-description">${this.data.description}</p>
          <div class="podcast-footer">
            <button class="play-button" onclick="togglePlay('${this.data.audioUrl}')">
              <i class="fas fa-play"></i>
            </button>
            <div class="podcast-stats">
              <span class="views"><i class="fas fa-headphones"></i> ${this.data.views}</span>
              <span class="likes"><i class="fas fa-heart"></i> ${this.data.likes}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// Main Podcast Handler
class PodcastManager {
  constructor() {
    this.podcasts = [];
    this.currentFilter = 'all';
    this.currentSort = 'newest';
    this.searchTerm = '';
  }

  async init() {
    try {
      await this.loadPodcasts();
      this.setupEventListeners();
      this.render();
    } catch (error) {
      console.error('Failed to initialize podcast manager:', error);
    }
  }

  async loadPodcasts() {
    try {
      const response = await fetch('/api/podcasts');
      const data = await response.json();
      this.podcasts = data.map(podcast => new PodcastCard(podcast));
    } catch (error) {
      console.error('Failed to load podcasts:', error);
    }
  }

  setupEventListeners() {
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.toLowerCase();
        this.render();
      });
    }

    // Filter functionality
    const filterSelect = document.querySelector('.filter-select');
    if (filterSelect) {
      filterSelect.addEventListener('change', (e) => {
        this.currentFilter = e.target.value;
        this.render();
      });
    }

    // Sort functionality
    const sortSelect = document.querySelector('.sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.currentSort = e.target.value;
        this.render();
      });
    }
  }

  filterPodcasts() {
    return this.podcasts
      .filter(podcast => {
        const matchesSearch = podcast.data.title.toLowerCase().includes(this.searchTerm) ||
                            podcast.data.description.toLowerCase().includes(this.searchTerm);
        const matchesFilter = this.currentFilter === 'all' || podcast.data.category === this.currentFilter;
        return matchesSearch && matchesFilter;
      })
      .sort((a, b) => {
        switch (this.currentSort) {
          case 'newest':
            return new Date(b.data.releaseDate) - new Date(a.data.releaseDate);
          case 'oldest':
            return new Date(a.data.releaseDate) - new Date(b.data.releaseDate);
          case 'popular':
            return b.data.views - a.data.views;
          default:
            return 0;
        }
      });
  }

  render() {
    const container = document.querySelector('.podcast-grid');
    if (!container) return;

    const filteredPodcasts = this.filterPodcasts();
    if (filteredPodcasts.length === 0) {
      container.innerHTML = `
        <div class="no-results animate-fade-in">
          <i class="fas fa-podcast"></i>
          <h3>No podcasts found</h3>
          <p>Try adjusting your search or filters</p>
        </div>
      `;
      return;
    }

    container.innerHTML = filteredPodcasts
      .map(podcast => podcast.render())
      .join('');
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const podcastManager = new PodcastManager();
  podcastManager.init();
});