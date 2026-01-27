from app import app

@app.route('/')
def home():
    return 'Welcome to the Online Movie Ticket Booking System!'

# More routes will be added here
