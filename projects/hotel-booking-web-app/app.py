import os

from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import hashlib
import re


app = Flask(__name__, template_folder='Templates', static_folder='Static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-secret-key')


def get_connection():
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'worldhotels'))
    return conn

password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')
@app.route('/SignUpPage', methods=['GET', 'POST'])
def SignUpPage():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return "Passwords do not match!"

        if not password_pattern.match(password):
            return "Password must contain at least 8 characters including one uppercase letter, one lowercase letter, and one digit."

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM customer WHERE Email = %s"
        cursor.execute(query, (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return "User already exists with this email address!"

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        query = "INSERT INTO customer (Email, fullName, Password) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, full_name, hashed_password))
        
        customer_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('Loginpage'))
    else:
        return render_template('SignUpPage.html')




@app.route('/booking', methods=['GET', 'POST'])
def book_room():
    if request.method == 'POST':
        location = request.form['location']
        checkin = request.form['checkin']
        checkout = request.form['checkout']
        rooms = request.form['rooms']
        roomtype = request.form['roomtype']

        if 'customer_id' not in session:
            return redirect(url_for('Loginpage'))

        customer_id = session['customer_id']

        conn = get_connection()
        cursor = conn.cursor()

        query = "INSERT INTO booking (CustomerID, CheckInDate, CheckOutDate, City, RoomType) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (customer_id, checkin, checkout, location, roomtype))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('confirmation'))
    else:
        return render_template('booking.html')


@app.route('/OpeningPage')
def OpeningPage():
    return render_template('OpeningPage.html')


def authenticate_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM customer WHERE Email = %s AND Password = %s"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(query, (email, hashed_password))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        conn.close()


@app.route('/Loginpage', methods=['GET', 'POST'])
def Loginpage():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if both email and password are provided
        if not email or not password:
            return "Email and password are required. Please try again."

        # Authenticate the user
        user = authenticate_user(email, password)
        
        # If user exists and authentication is successful, redirect to book_room
        if user:
            session['customer_id'] = user[0]
            print("Session customer_id:", session.get('customer_id'))  # Debug statement
            return redirect(url_for('book_room'))
        else:
            # If authentication fails, return an error message
            return "Invalid email or password. Please try again."

    # If it's a GET request, render the login page template
    return render_template('Loginpage.html')



def calculate_booking_price(checkin_date, checkout_date, city, room_type):
    checkin_date_str = checkin_date.strftime('%Y-%m-%d')
    checkout_date_str = checkout_date.strftime('%Y-%m-%d')

    num_days = (checkout_date - checkin_date).days

    final_price = 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT RateGBP FROM hotels WHERE City = %s"
        cursor.execute(query, (city,))
        row = cursor.fetchone()  # Fetch one row to consume the result set
        if row:
            rate_gbp = row[0]

            base_price = rate_gbp * num_days

            if room_type == 'Double Room':
                base_price *= 1.2
            elif room_type == 'Family Room':
                base_price *= 1.5

            if num_days >= 80:
                discount = 0.3
            elif 60 <= num_days <= 79:
                discount = 0.2
            elif 45 <= num_days <= 59:
                discount = 0.1
            else:
                discount = 0

            final_price = base_price * (1 - discount)

    finally:
        cursor.close()
        conn.close()

    return final_price

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    booking_id = request.form.get('booking_id')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM booking WHERE BookingID = %s"
        cursor.execute(query, (booking_id,))
        conn.commit()
        return "Booking canceled successfully."
    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()


@app.route('/confirmation')
def confirmation():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT BookingID, CustomerID, CheckInDate, CheckOutDate, City, RoomType FROM booking ORDER BY BookingID DESC LIMIT 1"
    cursor.execute(query)
    booking_details = cursor.fetchone()
    cursor.close()
    conn.close()

    checkin_date = booking_details[2]
    checkout_date = booking_details[3]
    room_type = booking_details[5]
    city = booking_details[4]

    booking_price = calculate_booking_price(checkin_date, checkout_date, city, room_type)

    return render_template("confirmation.html", booking_details=booking_details, booking_price=booking_price)


@app.route('/alter_booking/<int:booking_id>', methods=['GET', 'POST'])
def alter_booking(booking_id):
    if 'customer_id' not in session:
        return redirect(url_for('Loginpage'))

    customer_id = session['customer_id']

    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT BookingID FROM booking WHERE CustomerID = %s ORDER BY BookingID DESC LIMIT 1"
        cursor.execute(query, (customer_id,))
        booking_id = cursor.fetchone()[0]
    except Exception as e:
        return f"Error fetching booking ID: {str(e)}"
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        checkin = request.form.get('checkin')
        checkout = request.form.get('checkout')
        roomtype = request.form.get('roomtype')

        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = "UPDATE booking SET CheckInDate = %s, CheckOutDate = %s, RoomType = %s WHERE BookingID = %s"
            cursor.execute(query, (checkin, checkout, roomtype, booking_id))
            conn.commit()
            return redirect(url_for('confirmation'))
        except Exception as e:
            conn.rollback()
            return f"Error updating booking details: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    else:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT * FROM booking WHERE BookingID = %s"
            cursor.execute(query, (booking_id,))
            booking_details = cursor.fetchone()
            return render_template('alter_booking.html', booking_details=booking_details, booking_id=booking_id)
        except Exception as e:
            return f"Error fetching booking details: {str(e)}"
        finally:
            cursor.close()
            conn.close()


@app.route('/confirmation/alter_booking', methods=['POST'])
def confirm_alter_booking():
    booking_id = request.form.get('booking_id')
    return redirect(url_for('alter_booking', booking_id=booking_id))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template("admin.html")


# Route to render the "Add Hotel" form
@app.route('/admin/add_hotel_form', methods=['GET'])
def add_hotel_form():
    return render_template('add_hotel.html')

# Route to handle the form submission and add the hotel to the database
@app.route('/admin/add_hotel', methods=['POST'])
def add_hotel():
    # Extract data from the form submission
    city = request.form['city']
    capacity = request.form['capacity']
    number_of_rooms = request.form['number_of_rooms']
    rate_gbp = request.form['rate_gbp']
    peak_season_rate = request.form['peak_season_rate']
    off_peak_season_rate = request.form['off_peak_season_rate']

    # Establish database connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Define SQL query to insert hotel details into the hotels table
        query = "INSERT INTO hotels (City, Capacity, NumberOfRooms, RateGBP, PeakSeasonRate, OffPeakSeasonRate) VALUES (%s, %s, %s, %s, %s, %s)"
        # Execute the SQL query with the form data
        cursor.execute(query, (city, capacity, number_of_rooms, rate_gbp, peak_season_rate, off_peak_season_rate))
        # Commit the transaction
        conn.commit()
        # Redirect to a success page or route
        return "Hotel added successfully."
    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        # Return an error message
        return f"Error: {str(e)}"
    finally:
        # Close the cursor and database connection
        cursor.close()
        conn.close()







@app.route('/admin/remove_hotel', methods=['GET'])
def remove_hotel_form():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT City FROM hotels"
        cursor.execute(query)
        hotels = cursor.fetchall()
        print("Hotels:", hotels)  # Debug statement
        return render_template('remove_hotel.html', hotels=hotels)
    except Exception as e:
        return f"Error fetching hotels: {str(e)}"
    finally:
        cursor.close()
        conn.close()

@app.route('/remove_hotel', methods=['POST'])
def remove_hotel():
    hotel_to_remove_raw = request.form.get('hotel')
    print("Raw hotel name from form:", repr(hotel_to_remove_raw))

    # Extract hotel name from tuple
    hotel_to_remove = hotel_to_remove_raw.strip("()").strip("',") if hotel_to_remove_raw else None
    if not hotel_to_remove:
        return "No hotel selected for removal."

    print("Hotel to remove from form:", repr(hotel_to_remove))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT City FROM hotels"
        cursor.execute(query)
        hotels_in_db = [row[0].strip("'") for row in cursor.fetchall()]  # Strip leading and trailing single quotes
        print("Hotels in database:", [repr(h) for h in hotels_in_db])

        # Check if the hotel to remove exists in the database
        if hotel_to_remove.lower() in map(str.lower, hotels_in_db):  # Normalize to lowercase before comparison
            delete_query = "DELETE FROM hotels WHERE City = %s"
            cursor.execute(delete_query, (hotel_to_remove,))
            conn.commit()
            return "Hotel removed successfully."
        else:
            print(f"No matching hotel found for removal: {repr(hotel_to_remove)}")
            return f"No matching hotel found for removal: {hotel_to_remove}"
    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()



# Import render_template function from Flask

# Define a new route for the "View Hotels" page
@app.route('/admin/view_hotels')
def view_hotels():
    # Fetch the list of hotels from the database
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM hotels"
        cursor.execute(query)
        hotels = cursor.fetchall()
    except Exception as e:
        # Handle any errors that may occur during database query
        return f"Error fetching hotels: {str(e)}"
    finally:
        cursor.close()
        conn.close()

    # Render the "View Hotels" page template and pass the list of hotels to it
    return render_template('view_hotels.html', hotels=hotels)

# Import render_template and request from Flask
@app.route('/admin/change_price_form', methods=['GET'])
def change_price_form():
    return render_template('change_price_form.html')
# Your existing Flask app setup and routes...
@app.route('/admin/change_price', methods=['POST'])
def change_price():
    print(request.form)  # Add this line to print out the form data for debugging

    if request.method == 'POST':
        # Handle the form submission here
        try:
            # Extract data from the form submission
            city = request.form['city']
            rate_gbp = request.form['rate_gbp']
            peak_season_rate = request.form['peak_season_rate']
            off_peak_season_rate = request.form['off_peak_season_rate']
        except KeyError as e:
            # If any key is missing, return an error response
            return f"KeyError: {e}"

        # Update the prices in the database
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Define SQL query to update hotel prices
            query = "UPDATE hotels SET RateGBP = %s, PeakSeasonRate = %s, OffPeakSeasonRate = %s WHERE City = %s"
            # Execute the SQL query with the form data
            cursor.execute(query, (rate_gbp, peak_season_rate, off_peak_season_rate, city))
            # Commit the transaction
            conn.commit()
            # Redirect to a success page or route
            return "Prices updated successfully."
        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            # Return an error message
            return f"Error: {str(e)}"
        finally:
            # Close the cursor and database connection
            cursor.close()
            conn.close()
    else:
        # Handle GET request to render the form
        return render_template('change_price_form.html')

from flask import render_template

# Define a route to render the view bookings page
@app.route('/admin/view_bookings')
def view_bookings():
    # Fetch the list of bookings from the database
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM booking"
        cursor.execute(query)
        bookings = cursor.fetchall()
    except Exception as e:
        # Handle any errors that may occur during database query
        return f"Error fetching bookings: {str(e)}"
    finally:
        cursor.close()
        conn.close()

    # Render the view bookings page template and pass the list of bookings to it
    return render_template('view_bookings.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
