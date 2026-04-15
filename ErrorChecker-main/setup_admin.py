from app import app, db
from models import User, Artist, Genre, Album, Track
from datetime import datetime, date
import os

with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_premium=True,
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")
    
    # Create static/uploads directory if it doesn't exist
    uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created uploads directory at {uploads_dir}")
    
    # Check if we have genres
    if Genre.query.count() == 0:
        # Add some genres
        genres = [
            Genre(name='Rock'),
            Genre(name='Pop'),
            Genre(name='Electronic'),
            Genre(name='Jazz'),
            Genre(name='Classical')
        ]
        db.session.add_all(genres)
        db.session.commit()
        print("Added sample genres.")
    
    # Check if we have artists
    if Artist.query.count() == 0:
        # Add some artists
        artists = [
            Artist(name='Sample Artist 1', bio='This is a sample artist biography for demonstration purposes.'),
            Artist(name='Sample Artist 2', bio='Another sample artist with some music to listen to.')
        ]
        db.session.add_all(artists)
        db.session.commit()
        print("Added sample artists.")
    
    # Get references
    rock = Genre.query.filter_by(name='Rock').first()
    pop = Genre.query.filter_by(name='Pop').first()
    artist1 = Artist.query.filter_by(name='Sample Artist 1').first()
    artist2 = Artist.query.filter_by(name='Sample Artist 2').first()
    
    # Check if we have albums
    if Album.query.count() == 0 and artist1 and artist2:
        # Add some albums
        albums = [
            Album(title='Sample Album 1', artist=artist1, release_date=date(2023, 1, 15)),
            Album(title='Sample Album 2', artist=artist2, release_date=date(2022, 6, 10))
        ]
        db.session.add_all(albums)
        db.session.commit()
        print("Added sample albums.")
    
    # Get album references
    album1 = Album.query.filter_by(title='Sample Album 1').first()
    album2 = Album.query.filter_by(title='Sample Album 2').first()
    
    # Create placeholder track files
    def create_placeholder_file(filename):
        file_path = os.path.join(uploads_dir, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write('This is a placeholder audio file for demonstration purposes.')
            return True
        return False
    
    # Check if we have tracks
    if Track.query.count() == 0 and rock and pop and artist1 and artist2 and album1 and album2:
        # Create placeholder files
        create_placeholder_file('track1.mp3')
        create_placeholder_file('track2.mp3')
        create_placeholder_file('track3.mp3')
        create_placeholder_file('track4.mp3')
        
        # Add some tracks
        tracks = [
            Track(
                title='Sample Track 1',
                artist=artist1,
                album=album1,
                genre=rock,
                duration=180,  # 3 minutes
                file_path='/static/uploads/track1.mp3',
                is_premium=False,
                release_date=date(2023, 1, 15),
                added_at=datetime.utcnow()
            ),
            Track(
                title='Sample Track 2',
                artist=artist1,
                album=album1,
                genre=rock,
                duration=210,  # 3.5 minutes
                file_path='/static/uploads/track2.mp3',
                is_premium=True,
                release_date=date(2023, 1, 15),
                added_at=datetime.utcnow()
            ),
            Track(
                title='Sample Track 3',
                artist=artist2,
                album=album2,
                genre=pop,
                duration=240,  # 4 minutes
                file_path='/static/uploads/track3.mp3',
                is_premium=False,
                release_date=date(2022, 6, 10),
                added_at=datetime.utcnow()
            ),
            Track(
                title='Sample Track 4',
                artist=artist2,
                album=album2,
                genre=pop,
                duration=270,  # 4.5 minutes
                file_path='/static/uploads/track4.mp3',
                is_premium=True,
                release_date=date(2022, 6, 10),
                added_at=datetime.utcnow()
            )
        ]
        db.session.add_all(tracks)
        db.session.commit()
        print("Added sample tracks.")
    
    print("Setup completed successfully!")