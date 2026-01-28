from app import app, db
from flask import render_template, request, redirect, url_for, flash
from app.models import Movie, Show
from datetime import datetime, timedelta

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/movies')
def movies():
    # Show only available dates
    shows = Show.query.order_by(Show.show_time).all()
    dates = sorted(set(show.show_time.strftime('%d %b %Y') for show in shows))
    return render_template('movies.html', dates=dates)

# Show movies and showtimes for a selected date
@app.route('/movies/<date_str>')
def movies_by_date(date_str):
    # date_str format: 'dd MMM yyyy'
    shows = Show.query.join(Movie).filter(
        Show.show_time >= datetime.strptime(date_str, '%d %b %Y'),
        Show.show_time < datetime.strptime(date_str, '%d %b %Y') + timedelta(days=1)
    ).order_by(Show.show_time).all()
    from collections import defaultdict, OrderedDict
    movies_dict = defaultdict(list)
    for show in shows:
        movies_dict[show.movie.title].append(show)
    movies_dict = OrderedDict(sorted(movies_dict.items()))
    return render_template('movies_by_date.html', date=date_str, movies_dict=movies_dict)

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
