# IRDb

IRDb is a Flask restaurant discovery platform with customer browsing, map search, favourites, review moderation, and restaurant-owner dashboard features.

## Features

- Customer registration and login
- Restaurant discovery with search, filtering, ratings, and brand grouping
- Interactive map view with restaurant markers
- Customer profiles with review history and saved restaurants
- Admin moderation queue for reviews and flags
- Restaurant-owner portal for branch details and review replies

## Tech Stack

- Python 3
- Flask
- SQLAlchemy
- MySQL via PyMySQL
- Vanilla HTML, CSS, and JavaScript
- Leaflet for maps

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and update the database settings.
4. Run the app:

```bash
python run.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## Environment Variables

The app reads configuration from `.env`. Real secrets and local credentials should stay out of Git.
