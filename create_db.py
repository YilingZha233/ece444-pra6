"""Create missing tables without deleting existing entries."""

from project.app import app, db

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("Database tables are ready.")
