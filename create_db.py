from app import app, d

with app.app_context():
    db.create_all()
    print("Database tables created.")
