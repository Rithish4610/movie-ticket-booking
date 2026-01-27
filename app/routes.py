from app import app
from flask import render_template

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/movies')
def movies():
    return '<h2>Movies listing coming soon!</h2>'
# More routes will be added here
