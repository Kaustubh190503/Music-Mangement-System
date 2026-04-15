# Surtaal Music Player

A web application built with Flask for streaming music with user authentication and playlist management.

## Setting Up On Your Local Machine

### Prerequisites

- Python 3.11 or higher
- Visual Studio Code
- Git (optional)

### Step 1: Clone the Repository

Download the project from Replit or clone the repository:

```
git clone <repository_url>
cd surtaal
```

### Step 2: Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install flask flask-login flask-sqlalchemy email-validator python-dotenv gunicorn pymysql
```

### Step 4: Configure Environment Variables (Optional)

For local development, you won't need to create a .env file as the application is configured to use SQLite by default. If you want to use different settings, you can create a .env file with these variables:

```
SESSION_SECRET=your_secret_key_here
```

### Step 5: Run the Application

```bash
python main.py
```

The application will be available at http://localhost:5000

### Step 6: Using VS Code for Development

1. Open the project folder in VS Code
2. Make sure your virtual environment is activated
3. For debugging, create a launch.json file in the .vscode folder:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "main.py",
                "FLASK_ENV": "development"
            },
            "args": [
                "run",
                "--no-debugger"
            ],
            "jinja": true
        }
    ]
}
```

## Project Structure

The application follows a blueprint-based Flask structure:

- `app/` - Application package
  - `__init__.py` - Application factory and configuration
  - `models.py` - Database models
  - `routes.py` - Route definitions and views
- `static/` - Static files (CSS, JS, images)
- `templates/` - HTML templates
- `main.py` - Application entry point

## Features

- User authentication (login/register)
- Music playback
- Playlist management
- User profile management
- Premium user features
- Admin dashboard for content management
