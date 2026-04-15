document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Set up global track play functionality
    // This works on ANY page with play links or buttons
    
    // Find all play buttons/links with track IDs
    const trackPlayButtons = document.querySelectorAll('a[href^="/track/"], .play-track-btn');
    trackPlayButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get track ID either from href or data attribute
            let trackId;
            if (this.hasAttribute('href')) {
                trackId = this.getAttribute('href').split('/').pop();
            } else if (this.hasAttribute('data-track-id')) {
                trackId = this.getAttribute('data-track-id');
            }
            
            if (trackId && window.player) {
                window.player.loadTrack(trackId);
            }
        });
    });
    
    // Add event listener for playlist creation form
    const playlistForm = document.getElementById('create-playlist-form');
    if (playlistForm) {
        playlistForm.addEventListener('submit', function(e) {
            const playlistNameInput = document.getElementById('playlist-name');
            if (!playlistNameInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a playlist name');
            }
        });
    }
    
    // Handle search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('search-input');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
    
    // Remove tracks from playlist
    document.querySelectorAll('.remove-from-playlist').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const trackId = this.getAttribute('data-track-id');
            const playlistId = this.getAttribute('data-playlist-id');
            const trackElement = this.closest('.track-item');
            
            if (confirm('Are you sure you want to remove this track from the playlist?')) {
                fetch(`/playlist/${playlistId}/remove/${trackId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Animate removal and then remove from DOM
                        trackElement.style.opacity = '0';
                        setTimeout(() => {
                            trackElement.remove();
                        }, 300);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });
    
    // Format track durations
    document.querySelectorAll('.track-duration').forEach(element => {
        const seconds = parseInt(element.getAttribute('data-duration'));
        if (!isNaN(seconds)) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            element.textContent = `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
        }
    });
    
    // Admin panel delete confirmations
    document.querySelectorAll('.delete-confirm').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
