# Manage_Cloud - MySQL Database Manager

A PyQt6-based MySQL database manager with SSH tunneling support.

## Project Structure

- `app/`: Main application package.
  - `core/`: Core logic and integration (SSH tunnel, DB connections).
  - `models/`: Data models and database schema definitions.
  - `ui/`: User interface components (Windows, Widgets, Resources).
  - `utils/`: Utility functions and helper classes (Logging, Config parsing).
- `assets/`: Static assets such as icons, images, and stylesheets.
- `main.py`: Entry point for the application.
- `.env.example`: Template for environment variables.
- `requirements.txt`: Project dependencies.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your credentials.
3. Run the application:
   ```bash
   python main.py
   ```
