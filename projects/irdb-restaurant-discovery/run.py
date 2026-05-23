"""Development entry point for running the Flask app locally."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

