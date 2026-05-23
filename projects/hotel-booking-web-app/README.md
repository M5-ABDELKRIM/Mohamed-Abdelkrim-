# World Hotels Booking System

Flask and MySQL web application built for the UFCFES-30-1 Web Development and Databases coursework. The project implements a hotel booking system for the fictional **World Hotels (WH)** chain, covering customer booking flows, admin hotel management, dynamic database-backed pages, and responsive HTML/CSS views.

## Assignment Brief Summary

The brief required a website for a UK hotel chain where customers can browse destinations, register/login, create and manage bookings, view calculated prices, and receive a booking confirmation. It also required an admin perspective for managing hotels, room prices, bookings, and related hotel data. The coursework assessed database design, responsive front-end implementation, Flask business logic, a user system, security awareness, and supporting project explanation.

## Implemented Features

- Customer registration with password strength validation.
- Customer login using SHA-256 hashed password checks.
- Session-based booking flow for logged-in customers.
- Hotel booking form with city, check-in/check-out dates, room count, and room type.
- Booking confirmation page with generated booking ID and calculated price.
- Booking alteration and cancellation routes.
- Simulated payment prompt on confirmation page.
- Admin panel for adding hotels, removing hotels, viewing hotels, viewing bookings, and changing hotel prices.
- MySQL database dump with `customer`, `booking`, and `hotels` tables.
- Responsive page styling through separate CSS files in `Static/`.

## Tech Stack

- Python Flask
- MySQL
- HTML
- CSS
- Jinja templates

## Project Structure

```text
.
+-- app.py
+-- requirements.txt
+-- .env.example
+-- dumps/
|   +-- Dump20240504.sql
+-- Static/
|   +-- *.css
|   +-- image assets
+-- Templates/
    +-- *.html
```

## Database

The project uses a MySQL database named `worldhotels`.

The included SQL dump creates and seeds:

- `hotels`: hotel city, room capacity, and seasonal rates.
- `customer`: demo users with hashed passwords.
- `booking`: booking records linked to customers.

Demo customer password for seeded users:

```text
Password123
```

## Setup Instructions

1. Create and activate a Python virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create the MySQL database and import the dump.

```sql
CREATE DATABASE worldhotels;
```

```bash
mysql -u root -p worldhotels < dumps/Dump20240504.sql
```

On Windows PowerShell, run the SQL through the MySQL command-line client:

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS worldhotels;"
cmd /c "mysql -u root -p worldhotels < dumps\Dump20240504.sql"
```

If PowerShell says `mysql` is not recognized, use the full MySQL path:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.2\bin\mysql.exe" -u root -p -e "CREATE DATABASE IF NOT EXISTS worldhotels;"
cmd /c """C:\Program Files\MySQL\MySQL Server 8.2\bin\mysql.exe"" -u root -p worldhotels < dumps\Dump20240504.sql"
```

4. Configure environment variables. Copy `.env.example` to `.env` or set these values in your terminal.

```bash
set FLASK_SECRET_KEY=replace-with-a-local-secret
set DB_HOST=127.0.0.1
set DB_USER=root
set DB_PASSWORD=your_mysql_password
set DB_NAME=worldhotels
```

5. Run the Flask app.

```bash
python app.py
```

6. Open the website in a browser.

```text
http://127.0.0.1:5000/OpeningPage
```

## Main Routes

- `/OpeningPage` - landing/welcome page.
- `/SignUpPage` - customer registration.
- `/Loginpage` - customer login.
- `/booking` - create a booking.
- `/confirmation` - view latest booking confirmation and price.
- `/alter_booking/<booking_id>` - update a booking.
- `/admin` - admin control panel.
- `/admin/view_hotels` - view hotels.
- `/admin/view_bookings` - view bookings.

## Assignment Mapping

| Coursework element | Project evidence |
| --- | --- |
| Normalised database | MySQL schema and SQL dump in `dumps/Dump20240504.sql` |
| Responsive design and look & feel | HTML templates and CSS files in `Templates/` and `Static/` |
| Business logic and user system | Flask routes in `app.py` for signup, login, bookings, pricing, and admin actions |
| Website demo/explanation support | README setup instructions and feature summary |
| Security awareness | Password hashing, password complexity validation, parameterised SQL queries, environment variables for secrets |

## Notes and Limitations

- The payment step is simulated, as allowed by the brief.
- Admin access currently uses a direct `/admin` route rather than a separate admin authentication role.
- The database schema is a compact coursework implementation and does not fully model every optional report, room-status, currency, or cancellation-charge requirement from the brief.
- The SQL dump has been anonymised for GitHub presentation.

## Author

Mohamed Abdelkrim
