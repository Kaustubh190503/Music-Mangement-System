import os
from datetime import datetime
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func

from db import db
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
        # In a real app, this would connect to a payment processor
        return render_template('upgrade.html')
    
    @app.route('/process_upgrade', methods=['POST'])
    @login_required
    def process_upgrade():
        # This is a simplified mock of the upgrade process
        # In a real app, you would integrate with a payment processor
        
        # Update user to premium
        current_user.is_premium = True
        db.session.commit()
        
        flash('Congratulations! You are now a premium user.', 'success')
        return redirect(url_for('dashboard'))
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def upload_track():
        if request.method == 'POST':
            title = request.form.get('title')
            artist_name = request.form.get('artist')
            album_title = request.form.get('album')
            genre_name = request.form.get('genre')
            duration = request.form.get('duration')
            is_premium = 'is_premium' in request.form
            
            # Process artist
            artist = Artist.query.filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.session.add(artist)
                db.session.flush()
            
            # Process genre
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.flush()
            
            # Process album
            album = Album.query.filter_by(title=album_title, artist_id=artist.id).first()
            if not album:
                album = Album(title=album_title, artist_id=artist.id)
                db.session.add(album)
                db.session.flush()
            
            # Create track
            # In a real app, we would handle file uploads
            file_path = f"/uploads/{secure_filename(title)}.mp3"
            
            track = Track(
                title=title,
                artist_id=artist.id,
                album_id=album.id,
                genre_id=genre.id,
                duration=duration,
                file_path=file_path,
                is_premium=is_premium
            )
            
            db.session.add(track)
            db.session.commit()
            
            flash('Track uploaded successfully!', 'success')
            return redirect(url_for('upload_track'))
        
        artists = Artist.query.all()
        albums = Album.query.all()
        genres = Genre.query.all()
        
        return render_template('upload.html', 
                              artists=artists, 
                              albums=albums, 
                              genres=genres)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('error.html', error_code=404, message="Page not found"), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error.html', error_code=403, message="Access forbidden"), 403
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('error.html', error_code=500, message="Server error"), 500
