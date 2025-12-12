from flask import Blueprint, render_template, request, redirect, url_for
from .chart_generation import generate_chart_image
import sqlite3


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
        conn = sqlite3.connect('reservations.db')
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
    chart_img = generate_chart_image()
    if request.method == 'POST':

        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        seatRow  = request.form.get("row")
        seatColumn = request.form.get("seat")
        if not first or not last or not seatColumn or not seatRow:
            return render_template("new_reservation.html", error="Must have all fields filled out.", chart_img=chart_img)
    
        #1 index to 0 index
        row = int(seatRow) - 1
        seat = int(seatColumn) - 1
        passengerName = f"{first} {last}"
        seat_number = f"{row}-{seat}"

        conn = sqlite3.connect('reservations.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        #Uses db column names in reservations.db
        cursor.execute("""
            SELECT * FROM reservations 
            WHERE seatRow=? AND seatColumn=?""", (row, seat))
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return render_template("new_reservation.html",error=f"Seat {seat_number} is already taken.", chart_img=chart_img)
    
        cost_matrix = get_cost_matrix()
        price = cost_matrix[row - 1][seat - 1]
        pattern = "INFOTC4320"
        i = 0
        j = 0
        result = []

        while i < len(first) or j < len(pattern):
            if i < len(first):
                result.append(first[i])
                i += 1
            if j < len(pattern):
                result.append(pattern[j])
                j += 1
        reservation_code = ''.join(result)
    
        #SQLite DB schema
        cursor.execute("""
            INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber)
            VALUES (?, ?, ?, ?)
            """, (passengerName, row, seat, reservation_code))
        
        conn.commit()
        cursor.close()
        conn.close()
        #updates seating chart
        chart_img = generate_chart_image()
        
        success = f"Congrats {first}! Row: {row + 1}, Seat: {seat + 1} is now reserved for you. Enjoy your Trip! Your eTicket number is: {reservation_code}."
        return render_template("new_reservation.html", chart_img=chart_img, success=success)

    return render_template("new_reservation.html", chart_img=chart_img)



#reservations route, very short.
@routes.route("/reservations")
def reservation_list():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reservations")
    reservations = cursor.fetchall()

    cursor.close()
    conn.close()



    return render_template("reservation_list.html", reservations=reservations)

#route to delete from database
@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    conn = sqlite3.connect('reservations.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("routes.reservation_list"))
