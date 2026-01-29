
from app import app, db
from flask import render_template, request, redirect, url_for, flash, session
from app.models import Movie, Show
from datetime import datetime, timedelta

# Booking route for a show
@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
def book_show(show_id):
    show = Show.query.get_or_404(show_id)
    movie = show.movie
    # For demo: assume 40 seats, 8 per row, seat numbers A1-A8, B1-B8, ...
    rows = ['A','B','C','D','E']
    seats_per_row = 8
    all_seats = [f"{row}{num}" for row in rows for num in range(1, seats_per_row+1)]
    # Get booked seats for this show
    booked_seats = set(seat.seat_number for seat in show.seats if seat.is_booked)
    if request.method == 'POST':
        selected_seats = request.form.getlist('seats')
        if not selected_seats:
            flash('Please select at least one seat.', 'danger')
            return redirect(url_for('book_show', show_id=show_id))
        # Store selected seats in session and redirect to user info form
        session['selected_seats'] = selected_seats
        session['show_id'] = show_id
        return redirect(url_for('user_info'))
    return render_template('book_show.html', show=show, movie=movie, all_seats=all_seats, booked_seats=booked_seats)

# Step 2: User info form after seat selection
@app.route('/user_info', methods=['GET', 'POST'])
def user_info():
    selected_seats = session.get('selected_seats')
    show_id = session.get('show_id')
    if not selected_seats or not show_id:
        flash('Please select seats first.', 'danger')
        return redirect(url_for('movies'))
    show = Show.query.get_or_404(show_id)
    movie = show.movie
    # Determine class for each selected seat
    # Group seats by class for display
    class_map = {'First Class': [], 'Second Class': []}
    for seat in selected_seats:
        if seat[0] in ['A', 'B']:
            class_map['First Class'].append(seat)
        else:
            class_map['Second Class'].append(seat)
    # Prepare display string(s)
    seat_display = []
    if class_map['First Class']:
        seat_display.append(f"{','.join(class_map['First Class'])} (First Class)")
    if class_map['Second Class']:
        seat_display.append(f"{','.join(class_map['Second Class'])} (Second Class)")
    seat_display_str = ', '.join(seat_display)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        if not name or not email or not phone:
            flash('Please fill in all fields.', 'danger')
            return render_template('user_info.html', show=show, movie=movie, seat_display_str=seat_display_str)
        # Store user info in session and proceed to payment (to be implemented)
        session['user_info'] = {'name': name, 'email': email, 'phone': phone}
        return redirect(url_for('payment'))
    return render_template('user_info.html', show=show, movie=movie, seat_display_str=seat_display_str)
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/movies')
def movies():
    # Show only available dates (today or future)
    shows = Show.query.order_by(Show.show_time).all()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Only include dates that have at least one show in the future (today or later)
    shows_by_date = {}
    for show in shows:
        show_date = show.show_time.replace(hour=0, minute=0, second=0, microsecond=0)
        date_str = show.show_time.strftime('%d %b %Y')
        if show_date >= today:
            if date_str not in shows_by_date:
                shows_by_date[date_str] = []
            shows_by_date[date_str].append(show)
    # Remove dates where all shows are in the past (for today)
    filtered_dates = []
    now = datetime.now()
    for date_str, show_list in shows_by_date.items():
        # If date is after today, always include
        date_obj = datetime.strptime(date_str, '%d %b %Y')
        if date_obj > today:
            filtered_dates.append(date_str)
        else:
            # For today, only include if at least one show is in the future
            if any(show.show_time >= now for show in show_list):
                filtered_dates.append(date_str)
    dates = sorted(filtered_dates, key=lambda d: datetime.strptime(d, '%d %b %Y'))
    return render_template('movies.html', dates=dates)

# Show movies and showtimes for a selected date
@app.route('/movies/<date_str>')
def movies_by_date(date_str):
    # date_str format: 'dd MMM yyyy'
    date_start = datetime.strptime(date_str, '%d %b %Y')
    date_end = date_start + timedelta(days=1)
    now = datetime.now()
    shows = Show.query.join(Movie).filter(
        Show.show_time >= date_start,
        Show.show_time < date_end
    ).order_by(Show.show_time).all()
    from collections import defaultdict, OrderedDict
    movies_dict = defaultdict(list)
    for show in shows:
        # For today, only include shows in the future
        if date_start.date() == now.date():
            if show.show_time >= now:
                movies_dict[show.movie.title].append(show)
        else:
            movies_dict[show.movie.title].append(show)
    movies_dict = OrderedDict(sorted(movies_dict.items()))
    return render_template('movies_by_date.html', date=date_str, movies_dict=movies_dict)

# Admin route to add a new movie
@app.route('/admin/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        show_date = request.form['show_date']
        num_shows = int(request.form['num_shows'])
        ticket_price_first = request.form['ticket_price_first']
        ticket_price_second = request.form['ticket_price_second']
        if not title or not show_date or not ticket_price_first or not ticket_price_second:
            flash('All fields are required!', 'danger')
            return render_template('add_movie.html')
        movie = Movie(title=title, description=description)
        db.session.add(movie)
        db.session.commit()
        # Add multiple shows for this movie
        for i in range(1, num_shows + 1):
            show_time_str = request.form.get(f'show_time_{i}')
            if not show_time_str:
                continue
            # Combine date and time
            dt_str = f"{show_date} {show_time_str}"
            show_datetime = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            show = Show(
                movie_id=movie.id,
                show_time=show_datetime,
                ticket_price_first=float(ticket_price_first),
                ticket_price_second=float(ticket_price_second)
            )
            db.session.add(show)
        db.session.commit()
        flash('Movie and shows added successfully!', 'success')
        return redirect(url_for('add_movie'))
    return render_template('add_movie.html')
