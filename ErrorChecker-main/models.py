from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', 'premium'
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    playlists = db.relationship('Playlist', backref='owner', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    
    # Relationships
    tracks = db.relationship('Track', backref='artist', lazy='dynamic')
    
    def __repr__(self):
        return f'<Artist {self.name}>'

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    release_date = db.Column(db.Date)
    cover_url = db.Column(db.String(255))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    
    # Relationships
    artist = db.relationship('Artist', backref='albums')
    tracks = db.relationship('Track', backref='album', lazy='dynamic')
    
    def __repr__(self):
        return f'<Album {self.title}>'

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Genre {self.name}>'

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer)  # Duration in seconds
    file_path = db.Column(db.String(255), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    is_premium = db.Column(db.Boolean, default=False)
    play_count = db.Column(db.Integer, default=0)
    release_date = db.Column(db.Date)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    genre = db.relationship('Genre', backref='tracks')
    
    def __repr__(self):
        return f'<Track {self.title}>'

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tracks = db.relationship('PlaylistTrack', backref='playlist', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Playlist {self.name}>'

class PlaylistTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    track = db.relationship('Track')
    
    def __repr__(self):
        return f'<PlaylistTrack {self.id}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    track = db.relationship('Track')
    
    def __repr__(self):
        return f'<Favorite {self.id}>'
