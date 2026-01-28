from app import app, db
from flask import render_template, request, redirect, url_for, flash
from app.models import Movie, Show
from datetime import datetime

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/movies')
def movies():
    shows = Show.query.join(Movie).order_by(Show.show_time).all()
    # Structure: {date: {movie_title: [show, ...]}}
    from collections import defaultdict, OrderedDict
    shows_by_date = defaultdict(lambda: defaultdict(list))
    for show in shows:
        date_str = show.show_time.strftime('%d %b %Y')
        shows_by_date[date_str][show.movie.title].append(show)
    # Sort dates and movie titles for display
    shows_by_date = OrderedDict(sorted(shows_by_date.items(), key=lambda x: datetime.strptime(x[0], '%d %b %Y')))
    for date in shows_by_date:
        shows_by_date[date] = OrderedDict(sorted(shows_by_date[date].items()))
    return render_template('movies.html', shows_by_date=shows_by_date)

# Admin route to add a new movie
@app.route('/admin/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        show_time = request.form['show_time']
        ticket_price = request.form['ticket_price']
        if not title or not show_time or not ticket_price:
            flash('All fields are required!', 'danger')
            return render_template('add_movie.html')
        movie = Movie(title=title, description=description)
        db.session.add(movie)
        db.session.commit()
        # Add show for this movie
        show = Show(
            movie_id=movie.id,
            show_time=datetime.strptime(show_time, '%Y-%m-%dT%H:%M'),
            ticket_price=float(ticket_price)
        )
        db.session.add(show)
        db.session.commit()
        flash('Movie and show added successfully!', 'success')
        return redirect(url_for('add_movie'))
    return render_template('add_movie.html')
