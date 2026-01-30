from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_booking.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
# Flask-Mail config (update with your SMTP details)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sendercode0000@gmail.com'  # change this
app.config['MAIL_PASSWORD'] = 'xjccpbnvsrxnwjug'   # change this
app.config['MAIL_DEFAULT_SENDER'] = 'sendercode0000@gmail.com'  # change this

db = SQLAlchemy(app)
mail = Mail(app)

from app import routes
