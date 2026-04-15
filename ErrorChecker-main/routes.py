import os
from datetime import datetime, date
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func

from app import db
from models import User, Track, Artist, Album, Genre, Playlist, PlaylistTrack, Favorite

# Define decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Define decorator for premium-only routes
def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_premium:
            flash('This feature is only available for premium users.', 'warning')
            return redirect(url_for('upgrade'))
        return f(*args, **kwargs)
    return decorated_function

def init_routes(app):
    
    @app.route('/')
    def index():
        # Get some recent tracks for the homepage
        recent_tracks = Track.query.order_by(Track.added_at.desc()).limit(10).all()
        popular_tracks = Track.query.order_by(Track.play_count.desc()).limit(10).all()
        
        return render_template('index.html', recent_tracks=recent_tracks, popular_tracks=popular_tracks)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('register.html')
            
            user_exists = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()
            
            if user_exists:
                flash('Username or email already exists', 'danger')
                return render_template('register.html')
            
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            # Make the first user an admin
            if User.query.count() == 0:
                new_user.role = 'admin'
                flash('You have been registered as an admin user!', 'success')
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get user's playlists
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
        
        # Get recommendations (recent tracks)
        recommended_tracks = Track.query.order_by(Track.added_at.desc()).limit(5).all()
        
        # Get favorite tracks
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        favorite_tracks = [fav.track for fav in favorites]
        
        return render_template('dashboard.html', 
                              playlists=user_playlists, 
                              recommended_tracks=recommended_tracks,
                              favorite_tracks=favorite_tracks)
    
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_panel():
        users = User.query.all()
        tracks = Track.query.all()
        artists = Artist.query.all()
        albums = Album.query.all()
        genres = Genre.query.all()
        
        return render_template('admin.html', 
                              users=users, 
                              tracks=tracks, 
                              artists=artists, 
                              albums=albums, 
                              genres=genres)
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            # Validate current password if attempting to change it
            if new_password and not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile'))
            
            # Check if username or email already exists
            if username != current_user.username:
                user_exists = User.query.filter_by(username=username).first()
                if user_exists:
                    flash('Username already taken', 'danger')
                    return redirect(url_for('profile'))
                current_user.username = username
            
            if email != current_user.email:
                email_exists = User.query.filter_by(email=email).first()
                if email_exists:
                    flash('Email already registered', 'danger')
                    return redirect(url_for('profile'))
                current_user.email = email
            
            # Update password if provided
            if new_password:
                current_user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile'))
        
        return render_template('profile.html')
    
    @app.route('/player')
    @login_required
    def player():
        # Get all tracks accessible by the user
        if current_user.is_premium or current_user.role == 'admin':
            tracks = Track.query.all()
        else:
            tracks = Track.query.filter_by(is_premium=False).all()
        
        return render_template('player.html', tracks=tracks)
    
    @app.route('/track/<int:track_id>')
    @login_required
    def play_track(track_id):
        track = Track.query.get_or_404(track_id)
        
        # Check if user can access this track
        if track.is_premium and not (current_user.is_premium or current_user.role == 'admin'):
            flash('This track is only available for premium users', 'warning')
            return redirect(url_for('upgrade'))
        
        # Increment play count
        track.play_count += 1
        db.session.commit()
        
        # Return track data
        return jsonify({
            'id': track.id,
            'title': track.title,
            'artist': track.artist.name,
            'file_path': track.file_path,
            'duration': track.duration
        })
    
    @app.route('/search', methods=['GET'])
    def search():
        query = request.args.get('query', '')
        
        if not query:
            return render_template('search.html', results=None)
        
        # Search for tracks, artists, and albums
        tracks = Track.query.filter(
            Track.title.ilike(f'%{query}%')
        ).all()
        
        artists = Artist.query.filter(
            Artist.name.ilike(f'%{query}%')
        ).all()
        
        albums = Album.query.filter(
            Album.title.ilike(f'%{query}%')
        ).all()
        
        return render_template('search.html', 
                              query=query, 
                              tracks=tracks, 
                              artists=artists, 
                              albums=albums)
    
    @app.route('/favorite/<int:track_id>', methods=['POST'])
    @login_required
    def favorite_track(track_id):
        track = Track.query.get_or_404(track_id)
        
        # Check if already favorited
        existing_favorite = Favorite.query.filter_by(
            user_id=current_user.id, 
            track_id=track.id
        ).first()
        
        if existing_favorite:
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({'status': 'removed'})
        else:
            favorite = Favorite(user_id=current_user.id, track_id=track.id)
            db.session.add(favorite)
            db.session.commit()
            return jsonify({'status': 'added'})
    
    @app.route('/playlists', methods=['GET', 'POST'])
    @login_required
    def playlists():
        if request.method == 'POST':
            name = request.form.get('name')
            
            if not name:
                flash('Playlist name is required', 'danger')
                return redirect(url_for('playlists'))
            
            playlist = Playlist(name=name, user_id=current_user.id)
            db.session.add(playlist)
            db.session.commit()
            
            flash('Playlist created successfully', 'success')
        
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
        return render_template('playlists.html', playlists=user_playlists)
    
    @app.route('/playlist/<int:playlist_id>')
    @login_required
    def view_playlist(playlist_id):
        playlist = Playlist.query.get_or_404(playlist_id)
        
        # Ensure user owns this playlist
        if playlist.user_id != current_user.id and current_user.role != 'admin':
            flash('You do not have permission to view this playlist', 'danger')
            return redirect(url_for('playlists'))
        
        playlist_tracks = PlaylistTrack.query.filter_by(playlist_id=playlist.id).all()
        
        return render_template('playlist.html', 
                              playlist=playlist, 
                              playlist_tracks=playlist_tracks)
    
    @app.route('/playlist/<int:playlist_id>/add/<int:track_id>', methods=['POST'])
    @login_required
    def add_to_playlist(playlist_id, track_id):
        playlist = Playlist.query.get_or_404(playlist_id)
        track = Track.query.get_or_404(track_id)
        
        # Ensure user owns this playlist
        if playlist.user_id != current_user.id:
            return jsonify({'error': 'Not authorized'}), 403
        
        # Check if track already in playlist
        existing = PlaylistTrack.query.filter_by(
            playlist_id=playlist.id, 
            track_id=track.id
        ).first()
        
        if existing:
            return jsonify({'error': 'Track already in playlist'}), 400
        
        playlist_track = PlaylistTrack(playlist_id=playlist.id, track_id=track.id)
        db.session.add(playlist_track)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    @app.route('/playlist/<int:playlist_id>/remove/<int:track_id>', methods=['POST'])
    @login_required
    def remove_from_playlist(playlist_id, track_id):
        playlist = Playlist.query.get_or_404(playlist_id)
        
        # Ensure user owns this playlist
        if playlist.user_id != current_user.id:
            return jsonify({'error': 'Not authorized'}), 403
        
        playlist_track = PlaylistTrack.query.filter_by(
            playlist_id=playlist.id,
            track_id=track_id
        ).first_or_404()
        
        db.session.delete(playlist_track)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    @app.route('/upgrade')
    @login_required
    def upgrade():
        return render_template('upgrade.html')
    
    @app.route('/upgrade/premium', methods=['POST'])
    @login_required
    def process_upgrade():
        # In a real application, this would process payment
        # For this demo, we'll just upgrade the user
        current_user.is_premium = True
        db.session.commit()
        
        flash('Congratulations! You are now a premium user.', 'success')
        return redirect(url_for('dashboard'))
    
    # Admin routes for managing content
    @app.route('/admin/add_artist', methods=['POST'])
    @login_required
    @admin_required
    def add_artist():
        name = request.form.get('name')
        bio = request.form.get('bio')
        
        if not name:
            flash('Artist name is required', 'danger')
            return redirect(url_for('admin_panel'))
        
        artist = Artist(name=name, bio=bio)
        db.session.add(artist)
        db.session.commit()
        
        flash('Artist added successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/add_album', methods=['POST'])
    @login_required
    @admin_required
    def add_album():
        title = request.form.get('title')
        artist_id = request.form.get('artist_id')
        release_date = request.form.get('release_date')
        cover_url = request.form.get('cover_url')
        
        if not title or not artist_id:
            flash('Album title and artist are required', 'danger')
            return redirect(url_for('admin_panel'))
        
        album = Album(
            title=title, 
            artist_id=artist_id,
            release_date=datetime.strptime(release_date, '%Y-%m-%d').date() if release_date else None,
            cover_url=cover_url
        )
        db.session.add(album)
        db.session.commit()
        
        flash('Album added successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/add_genre', methods=['POST'])
    @login_required
    @admin_required
    def add_genre():
        name = request.form.get('name')
        
        if not name:
            flash('Genre name is required', 'danger')
            return redirect(url_for('admin_panel'))
        
        genre = Genre(name=name)
        db.session.add(genre)
        db.session.commit()
        
        flash('Genre added successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/add_track', methods=['POST'])
    @login_required
    @admin_required
    def add_track():
        title = request.form.get('title')
        artist_id = request.form.get('artist_id')
        album_id = request.form.get('album_id')
        genre_id = request.form.get('genre_id')
        duration = request.form.get('duration')
        file_path = request.form.get('file_path')
        is_premium = 'is_premium' in request.form
        
        if not title or not artist_id:
            flash('Track title and artist are required', 'danger')
            return redirect(url_for('admin_panel'))
        
        # Handle file upload
        audio_file = request.files.get('audio_file')
        if audio_file and audio_file.filename:
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            # Secure the filename to prevent security issues
            filename = secure_filename(audio_file.filename)
            
            # Generate a unique filename to avoid overwriting
            base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_filename = f"{base}_{timestamp}{ext}"
            
            # Save the file
            file_path = os.path.join('static', 'uploads', new_filename)
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
            audio_file.save(full_path)
            
            # Set file_path for database
            file_path = '/' + file_path.replace('\\', '/')
        
        if not file_path:
            flash('Either file upload or file URL is required', 'danger')
            return redirect(url_for('admin_panel'))
        
        track = Track(
            title=title,
            artist_id=artist_id,
            album_id=album_id if album_id else None,
            genre_id=genre_id if genre_id else None,
            duration=duration if duration else None,
            file_path=file_path,
            is_premium=is_premium,
            release_date=date.today(),
            added_at=datetime.utcnow()
        )
        db.session.add(track)
        db.session.commit()
        
        flash('Track added successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/delete_track/<int:track_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_track(track_id):
        track = Track.query.get_or_404(track_id)
        db.session.delete(track)
        db.session.commit()
        
        flash('Track deleted successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/delete_artist/<int:artist_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_artist(artist_id):
        artist = Artist.query.get_or_404(artist_id)
        
        # Check if artist has tracks
        if artist.tracks.count() > 0:
            flash('Cannot delete artist with associated tracks', 'danger')
            return redirect(url_for('admin_panel'))
        
        db.session.delete(artist)
        db.session.commit()
        
        flash('Artist deleted successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/delete_album/<int:album_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_album(album_id):
        album = Album.query.get_or_404(album_id)
        
        # Check if album has tracks
        if album.tracks.count() > 0:
            flash('Cannot delete album with associated tracks', 'danger')
            return redirect(url_for('admin_panel'))
        
        db.session.delete(album)
        db.session.commit()
        
        flash('Album deleted successfully', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/artist/<int:artist_id>')
    def view_artist(artist_id):
        artist = Artist.query.get_or_404(artist_id)
        tracks = Track.query.filter_by(artist_id=artist.id).all()
        albums = Album.query.filter_by(artist_id=artist.id).all()
        
        return render_template('artist.html', 
                              artist=artist,
                              tracks=tracks,
                              albums=albums)
    
    @app.route('/album/<int:album_id>')
    def view_album(album_id):
        album = Album.query.get_or_404(album_id)
        tracks = Track.query.filter_by(album_id=album.id).all()
        
        return render_template('album.html',
                              album=album,
                              tracks=tracks)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
