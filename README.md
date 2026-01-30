# Online Movie Ticket Booking System

## Features
- View movies and show timings
- Select seats (basic layout)
- Book tickets
- Receive confirmation email
- Admin panel to add movies
- Booking history
- Seat availability check
- Date & time validation

## Tech Stack
- Flask
- SQLite
- HTML, CSS, JS
- Email (SMTP)

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure email settings in `app/__init__.py`:
   - `MAIL_USERNAME`: Your full email address (e.g. sendercode0000@gmail.com)
   - `MAIL_PASSWORD`: Your email's app password (not your regular password; for Gmail, generate an App Password)
   - `MAIL_DEFAULT_SENDER`: Same as your email address
   - Example:
     ```python
     app.config['MAIL_USERNAME'] = 'sendercode0000@gmail.com'
     app.config['MAIL_PASSWORD'] = 'your_app_password'
     app.config['MAIL_DEFAULT_SENDER'] = 'sendercode0000@gmail.com'
     ```
   - For Gmail, enable 2-Step Verification and create an App Password: https://support.google.com/accounts/answer/185833
3. Run the app:
   ```bash
   python run.py
   ```

---

This project is in the initial scaffolding stage. More features and documentation will be added soon.

# movie-ticket-booking
