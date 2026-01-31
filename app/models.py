

# Models for Movie, Show, Seat, User, Booking (Single Theater: BatVerse Cinema)
from app import db
from datetime import datetime

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	is_admin = db.Column(db.Boolean, default=False)
	bookings = db.relationship('Booking', backref='user', lazy=True)

class Movie(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	description = db.Column(db.Text, nullable=True)
	shows = db.relationship('Show', backref='movie', lazy=True)

class Show(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
	show_time = db.Column(db.DateTime, nullable=False)
	ticket_price_first = db.Column(db.Float, nullable=False)
	ticket_price_second = db.Column(db.Float, nullable=False)
	seats = db.relationship('Seat', backref='show', lazy=True)
	bookings = db.relationship('Booking', backref='show', lazy=True)

class Seat(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
	seat_number = db.Column(db.String(10), nullable=False)
	is_booked = db.Column(db.Boolean, default=False)

class Booking(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
	seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
	booking_time = db.Column(db.DateTime, default=datetime.utcnow)
	email_sent = db.Column(db.Boolean, default=False)

class PaymentRecord(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	utr = db.Column(db.String(12), unique=True, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
