from flask import Blueprint, render_template, request, redirect, url_for
from .database import get_connection
from .chart_generation import generate_chart_image
import random
import string


routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('index.html')
#given in class document
def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

@routes.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            return render_template(
                "admin_login.html",error="Username and password are required... try again.")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username=%s", (username,))
        admin = cursor.fetchone()
        if not admin or password != admin["password_hash"]:
            return render_template(
                "admin_login.html",
                error="Invalid username or password... try again.")
        return redirect(url_for("routes.admin_dashboard"))
    return render_template("admin_login.html")


@routes.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")



# reservation route
@routes.route('/new_reservation', methods=['GET', 'POST'])
def new_reservation():
    if request.method == 'POST':

        #inputs need to be in scope for entire function
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        flight_no = request.form.get("flight_number", "").strip().upper()
        row  = request.form.get("row")
        seat = request.form.get("seat")

        #error check
        if not first or not last or not email or not flight_no or not seat or not row:
            return render_template("new_reservation.html", error="Must have all fields filled out.")
    
        row = int(row)
        seat = int(seat)
        passenger_name = f"{first} {last}"
        seat_number = f"{row}-{seat}"


        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM reservations 
            WHERE flight_number=%s AND seat_number=%s""", (flight_no, seat_number))
        existing = cursor.fetchone()
        #we are checing if the seat is already taken, if it is then we return a message saying so.

        if existing:
            cursor.close()
            conn.close()
            return render_template("new_reservation.html",error=f"Seat {seat_number} is already taken on Flight {flight_no}.")
    
        cost_matrix = get_cost_matrix()
        #account for 13 and 5
        price = cost_matrix[row - 1][seat - 1]

        #we need to generate a random string code using the random and string imports.
        #this should work i think.
        reservation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
        #inputs all of our values we have created and extrapolated into the DB.
        cursor.execute("""
            INSERT INTO reservations (passenger_name, passenger_email, flight_number, seat_number, price, reservation_code)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (passenger_name, email, flight_no, seat_number, price, reservation_code))
        
        conn.commit()
        cursor.close()
        conn.close()
    
        return redirect(url_for("routes.reservation_list"))
    chart_img = generate_chart_image()
    return render_template("new_reservation.html", chart_img=chart_img)



#reservations route, very short.
@routes.route("/reservations")
def reservation_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations")
    reservations = cursor.fetchall()

    cursor.close()
    conn.close()



    return render_template("reservation_list.html", reservations=reservations)

