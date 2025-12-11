from flask import Blueprint, render_template, request, redirect, url_for
from .database import get_connection
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
        row  = request.form.get("row")
        seat = request.form.get("seat")

    #error check
        if not first or not last or not seat or not row:
            return render_template("new_reservation.html", error="Must have all fields filled out.")
    
        row = int(row)
        seat = int(seat)


        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM reservations 
            WHERE row_no = %s AND seat_no = %s""", (row, seat))
        existing = cursor.fetchall()
        #we are checing if the seat is already taken, if it is then we return a message saying so.

        if existing:
            return render_template("new_reservation.html",error=f"Row {row}, Seat {seat} is taken.")
    
        cost_matrix = get_cost_matrix()
        #account for 13 and 5
        price = cost_matrix[row - 1][seat - 1]

        #we need to generate a random string code using the random and string imports.
        #this should work i think.
        seatcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
        #inputs all of our values we have created and extrapolated into the DB.
        cursor.execute("""
            INSERT INTO reservations (first_name, last_name, row_no, seat_no, price, code)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (first, last, row, seat, price, seatcode))
        conn.commit()

        cursor.close()
        conn.close()
    
        return redirect(url_for("routes.reservation_list"))
    return render_template("new_reservation.html")


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

