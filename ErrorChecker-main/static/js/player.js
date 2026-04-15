class AudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentTrack = null;
        this.playlist = [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.progressInterval = null;
        
        // Initialize player elements
        this.playerElement = document.getElementById('fixed-audio-player') || document.getElementById('audio-player');
        this.trackTitleElement = document.getElementById('track-title');
        this.trackArtistElement = document.getElementById('track-artist');
        this.progressBar = document.getElementById('progress');
        this.currentTimeElement = document.getElementById('current-time');
        this.durationElement = document.getElementById('duration');
        this.playButton = document.getElementById('play-button');
        this.prevButton = document.getElementById('prev-button');
        this.nextButton = document.getElementById('next-button');
        this.progressContainer = document.getElementById('progress-container');
        
        // Bind event listeners
        this.audio.addEventListener('ended', () => this.playNext());
        this.audio.addEventListener('canplay', () => {
            if (this.isPlaying) this.audio.play();
            this.updateDuration();
        });
        
        this.playButton.addEventListener('click', () => this.togglePlay());
        this.prevButton.addEventListener('click', () => this.playPrev());
        this.nextButton.addEventListener('click', () => this.playNext());
        
        // Add progress bar click event
        if (this.progressContainer) {
            this.progressContainer.addEventListener('click', (e) => {
                const progressContainerWidth = this.progressContainer.clientWidth;
                const clickPosition = e.offsetX;
                const percentage = clickPosition / progressContainerWidth;
                
                this.audio.currentTime = percentage * this.audio.duration;
                this.updateProgress();
            });
        }
    }
    
    loadTrack(trackId) {
        fetch(`/track/${trackId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Premium track');
                }
                return response.json();
            })
            .then(track => {
                this.currentTrack = track;
                this.audio.src = track.file_path;
                
                // Update player UI
                this.trackTitleElement.textContent = track.title;
                this.trackArtistElement.textContent = track.artist;
                
                // Highlight current track in playlist
                document.querySelectorAll('.track-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                const trackElement = document.querySelector(`.track-item[data-id="${trackId}"]`);
                if (trackElement) trackElement.classList.add('active');
                
                // Auto-play the loaded track
                this.play();
            })
            .catch(error => {
                console.error('Error loading track:', error);
                if (error.message === 'Premium track') {
                    window.location.href = '/upgrade';
                }
            });
    }
    
    play() {
        this.isPlaying = true;
        this.audio.play()
            .then(() => {
                this.playButton.innerHTML = '<i class="fas fa-pause"></i>';
                this.startProgressInterval();
            })
            .catch(error => {
                console.error('Error playing audio:', error);
            });
    }
    
    pause() {
        this.isPlaying = false;
        this.audio.pause();
        this.playButton.innerHTML = '<i class="fas fa-play"></i>';
        this.clearProgressInterval();
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    playNext() {
        if (this.playlist.length === 0) return;
        
        this.currentIndex = (this.currentIndex + 1) % this.playlist.length;
        this.loadTrack(this.playlist[this.currentIndex]);
    }
    
    playPrev() {
        if (this.playlist.length === 0) return;
        
        this.currentIndex = (this.currentIndex - 1 + this.playlist.length) % this.playlist.length;
        this.loadTrack(this.playlist[this.currentIndex]);
    }
    
    setPlaylist(trackIds, startIndex = 0) {
        this.playlist = trackIds;
        this.currentIndex = startIndex;
        
        if (this.playlist.length > 0) {
            this.loadTrack(this.playlist[this.currentIndex]);
        }
    }
    
    startProgressInterval() {
        this.clearProgressInterval();
        this.progressInterval = setInterval(() => {
            this.updateProgress();
        }, 1000);
    }
    
    clearProgressInterval() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    updateProgress() {
        if (!this.audio.duration) return;
        
        const percentage = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressBar.style.width = `${percentage}%`;
        
        // Update current time display
        this.currentTimeElement.textContent = this.formatTime(this.audio.currentTime);
    }
    
    updateDuration() {
        this.durationElement.textContent = this.formatTime(this.audio.duration);
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
    }
}

// Initialize player when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if either player element exists
    if (document.getElementById('fixed-audio-player') || document.getElementById('audio-player')) {
        window.player = new AudioPlayer();
        
        // Get all track elements
        const trackElements = document.querySelectorAll('.track-item');
        const trackIds = Array.from(trackElements).map(el => parseInt(el.dataset.id));
        
        // Add click event to each track
        trackElements.forEach((trackElement, index) => {
            trackElement.addEventListener('click', () => {
                window.player.setPlaylist(trackIds, index);
            });
        });
    }
    
    // Handle favorite button clicks
    document.querySelectorAll('.favorite-button').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering track play
            
            const trackId = button.dataset.id;
            
            fetch(`/favorite/${trackId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'added') {
                    button.classList.add('active');
                    button.innerHTML = '<i class="fas fa-heart"></i>';
                } else {
                    button.classList.remove('active');
                    button.innerHTML = '<i class="far fa-heart"></i>';
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Handle playlist add buttons
    document.querySelectorAll('.add-to-playlist').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering track play
            
            const trackId = button.dataset.id;
            const dropdown = button.nextElementSibling;
            
            if (dropdown.classList.contains('show')) {
                dropdown.classList.remove('show');
            } else {
                // Close all other open dropdowns
                document.querySelectorAll('.playlist-dropdown.show').forEach(d => {
                    if (d !== dropdown) d.classList.remove('show');
                });
                
                dropdown.classList.add('show');
            }
        });
    });
    
    // Handle clicking outside of dropdowns
    document.addEventListener('click', (e) => {
        if (!e.target.matches('.add-to-playlist') && !e.target.closest('.playlist-dropdown')) {
            document.querySelectorAll('.playlist-dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
    
    // Handle add to playlist actions
    document.querySelectorAll('.playlist-dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            
            const playlistId = item.dataset.playlist;
            const trackId = item.closest('.playlist-dropdown').dataset.track;
            
            fetch(`/playlist/${playlistId}/add/${trackId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                if (data.status === 'success') {
                    showNotification('Track added to playlist', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to add track to playlist', 'danger');
            });
            
            // Close the dropdown
            item.closest('.playlist-dropdown').classList.remove('show');
        });
    });
});

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show the notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
