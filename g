A Flask-based music streaming platform with user authentication, playlist management, and music playback functionality.

## Features

- User authentication (login, registration)
- Music playback with progress bar
- Playlist creation and management
- Favorites system
- Admin panel for content management
- Search functionality
- Premium user features
- Audio file upload functionality

## Prerequisites

- Python 3.11 (recommended) or Python 3.10
- Git (optional, for cloning)

## Setting Up on Your Laptop

### Step 1: Get the Project Files

Download the project files from Replit using the "Download as ZIP" option, then extract them to a folder on your laptop.

### Step 2: Set Up a Python Virtual Environment

```bash
# Navigate to the project directory
cd path/to/surtaal-music-player

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Required Packages

```bash
# Install all required packages
pip install flask flask-sqlalchemy flask-login flask-wtf email-validator werkzeug gunicorn
```

### Step 4: Initialize the Database

```bash
# Create the initial database with admin user and sample content
python setup_admin.py
```

### Step 5: Run the Application

```bash
# Start the application
python main.py
```

### Step 6: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Default Admin Login

- Username: `admin`
- Password: `admin123`

## Project Structure

- `app.py`: Core application setup and database configuration
- `main.py`: Entry point for the application
- `models.py`: Database models (User, Track, Artist, etc.)
- `routes.py`: URL routes and request handlers
- `static/`: Static files (CSS, JavaScript, uploads)
- `templates/`: HTML templates
- `setup_admin.py`: Script to create admin user and sample data

## Managing Audio Files

Music files are stored in the `static/uploads` directory. You can:

1. Upload new files via the admin panel
2. Add tracks with external URLs

## Troubleshooting

If you encounter issues:

1. Ensure you're using Python 3.11 or 3.10
2. Make sure all dependencies are installed
3. If you get "No module found" errors, check that your virtual environment is activated
4. For database errors, try deleting the `surtaal.db` file and running `setup_admin.py` again

## Additional Notes

- The application uses SQLite by default, no additional database setup required
- File uploads go to the `static/uploads` directory
- The player supports common audio formats (mp3, wav, ogg)
