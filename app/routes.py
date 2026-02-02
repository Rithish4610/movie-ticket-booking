
from app import app, db, mail
from flask import render_template, request, redirect, url_for, flash, session
from flask_mail import Message
from app.models import Movie, Show, PaymentRecord, Seat
from datetime import datetime, timedelta
from flask import jsonify

# Simulated payment status (for demo)
payment_status = {'paid': False}

# Endpoint to simulate payment completion (for demo/testing only)
@app.route('/simulate_payment', methods=['POST'])
def simulate_payment():
    data = request.json
    utr = data.get('utr')
    
    # Strict Validation: Must be present, exactly 12 chars, and ALL digits
    if not utr or len(utr) != 12 or not utr.isdigit():
        return jsonify({'status': 'invalid_utr_format'}), 400
    
    # Check if UTR is already used (Database Check)
    existing = PaymentRecord.query.filter_by(utr=utr).first()
    if existing:
        return jsonify({'status': 'used_utr'}), 400
    
    # Valid UTR - Save it to prevent reuse
    new_record = PaymentRecord(utr=utr)
    db.session.add(new_record)
    db.session.commit()

    payment_status['paid'] = True
    return jsonify({'status': 'ok'})

# Endpoint to check payment status (AJAX polling)
@app.route('/payment_status')
def payment_status_check():
    return jsonify({'paid': payment_status['paid']})

# Payment route after user info
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    selected_seats = session.get('selected_seats')
    show_id = session.get('show_id')
    user_info = session.get('user_info')
    print('DEBUG: /payment route called')
    print('DEBUG: session.selected_seats =', selected_seats)
    print('DEBUG: session.show_id =', show_id)
    print('DEBUG: session.user_info =', user_info)
    print('DEBUG: payment_status["paid"] =', payment_status['paid'])
    if not selected_seats or not show_id or not user_info:
        print('DEBUG: Session missing, redirecting to movies')
        flash('Session expired or invalid. Please start again.', 'danger')
        return redirect(url_for('movies'))
    show = Show.query.get_or_404(show_id)
    movie = show.movie
    total_price = 0
    for seat in selected_seats:
        if seat[0] in ['A', 'B']:
            total_price += show.ticket_price_first
        else:
            total_price += show.ticket_price_second
    # Generate UPI payment URL and QR code
    upi_id = "9363613681@ptyes"
    upi_payee = "Movie Booking"
    upi_url = f"upi://pay?pa={upi_id}&pn={upi_payee.replace(' ', '%20')}&am={total_price}&cu=INR"

    # Generate QR code image as base64
    import qrcode
    import io
    import base64
    qr = qrcode.make(upi_url)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    qr_data_url = f"data:image/png;base64,{qr_b64}"

    # Define confirm_and_show helper first so it can be called from POST logic
    def confirm_and_show():
        # Mark seats as booked
        for seat in show.seats:
            if seat.seat_number in selected_seats:
                seat.is_booked = True
        db.session.commit()
        # Send confirmation email
        try:
            msg = Message(
                subject='Your Movie Ticket is Booked!',
                recipients=[user_info['email']],
                body=f"""
Dear {user_info['name']},

Your ticket is booked successfully!

Movie: {movie.title}
Show Time: {show.show_time.strftime('%d %b %Y, %I:%M %p')}
Seats: {', '.join(selected_seats)}
Total Paid: ₹{total_price}

Thank you for booking with us!
Enjoy your movie.
                """
            )
            mail.send(msg)
        except Exception as e:
            print('Email send failed:', e)
        flash('Payment successful! Your Knight Seats are booked.', 'success')
        # Clear session data after confirmation
        session.pop('selected_seats', None)
        session.pop('show_id', None)
        session.pop('user_info', None)
        return render_template('confirmation.html', show=show, movie=movie, user_info=user_info, selected_seats=selected_seats, total_price=total_price)

    # Handle Manual Payment Submission
    if request.method == 'POST':
        utr = request.form.get('utr')
        if not utr or len(utr) != 12 or not utr.isdigit():
            flash('Invalid UTR! Please enter exactly 12 digits.', 'danger')
        else:
            existing = PaymentRecord.query.filter_by(utr=utr).first()
            if existing:
                flash('This UTR has already been used!', 'danger')
            else:
                # Valid Payment
                new_record = PaymentRecord(utr=utr)
                db.session.add(new_record)
                db.session.commit()
                return confirm_and_show()

    # Logic to handle payment confirmation only when status is verified (Polling fallback)
    # If payment_status['paid'] is True, mark seats as booked, send email, and show confirmation
    if payment_status['paid']:
        payment_status['paid'] = False  # Reset for next booking
        return confirm_and_show()
    return render_template('payment.html', show=show, movie=movie, user_info=user_info, selected_seats=selected_seats, total_price=total_price, upi_url=upi_url, qr_data_url=qr_data_url)

# Booking route for a show
@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
def book_show(show_id):
    show = Show.query.get_or_404(show_id)
    movie = show.movie
    # For demo: assume 40 seats, 8 per row, seat numbers A1-A8, B1-B8, ...
    rows = ['A','B','C','D','E']
    seats_per_row = 8
    
    # Auto-generate seats if they don't exist for this show
    if not show.seats:
        for row in rows:
            for num in range(1, seats_per_row+1):
                seat_num = f"{row}{num}"
                seat = Seat(show_id=show.id, seat_number=seat_num)
                db.session.add(seat)
        db.session.commit()
        # Reload show to get the new seats
        show = Show.query.get_or_404(show_id)

    all_seats = [f"{row}{num}" for row in rows for num in range(1, seats_per_row+1)]
    # Get booked seats for this show
    booked_seats = set(seat.seat_number for seat in show.seats if seat.is_booked)
    if request.method == 'POST':
        selected_seats = request.form.getlist('seats')
        if not selected_seats:
            flash('Please select at least one Knight Seat.', 'danger')
            return redirect(url_for('book_show', show_id=show_id))
        # Prevent booking of already booked seats
        overlap = set(selected_seats) & booked_seats
        if overlap:
            flash(f"The following Knight Seats are already booked and cannot be selected: {', '.join(sorted(overlap))}", 'danger')
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
        flash('Please select Knight Seats first.', 'danger')
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
        # Phone number validation: must be exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            flash('Phone Number must be exactly 10 digits.', 'danger')
            return render_template('user_info.html', show=show, movie=movie, seat_display_str=seat_display_str)
        # Store user info in session and proceed to payment
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
            
            # Auto-generate seats for the new show
            rows = ['A','B','C','D','E']
            seats_per_row = 8
            for row in rows:
                for num in range(1, seats_per_row+1):
                    seat_num = f"{row}{num}"
                    seat = Seat(show_id=show.id, seat_number=seat_num)
                    db.session.add(seat)
            db.session.commit()

        flash('Movie and shows added successfully!', 'success')
        return redirect(url_for('add_movie'))
    return render_template('add_movie.html')
