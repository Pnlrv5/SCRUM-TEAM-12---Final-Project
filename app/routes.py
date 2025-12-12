from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .chart_generation import generate_chart_image
import sqlite3
import os

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('index.html')

# given in class document
def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# helper for protecting admin-only routes
def admin_required():
    return session.get("is_admin") is True

#  ALWAYS use the instance DB (this is where Flask expects it)
def get_db_path():
    # current_app.instance_path points to ./instance
    return os.path.join(current_app.instance_path, "reservations.db")

def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

#  If tables don’t exist yet, create them from schema.sql
def ensure_schema():
    conn = get_conn()
    cur = conn.cursor()
    try:
        # if this works, schema exists
        cur.execute("SELECT 1 FROM admins LIMIT 1;")
    except sqlite3.OperationalError:
        # run schema.sql from project root
        # app/routes.py -> project root is one level up from app/
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        schema_file = os.path.join(project_root, "schema.sql")

        with open(schema_file, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        cur.close()
        conn.close()

@routes.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    ensure_schema()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("admin_login.html", error="Username and password are required... try again.")

        conn = get_conn()
        cursor = conn.cursor()

        #  table is admins (per schema.sql), placeholders are ?
        cursor.execute("SELECT username, password FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if not admin or password != admin["password"]:
            return render_template("admin_login.html", error="Invalid username or password... try again.")

        session.clear()
        session["is_admin"] = True
        session["admin_username"] = username

        return redirect(url_for("routes.admin_dashboard"))

    return render_template("admin_login.html")

@routes.route('/admin_logout')
def admin_logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("routes.admin_login"))

@routes.route("/admin_dashboard")
def admin_dashboard():
    ensure_schema()

    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    cost_matrix = get_cost_matrix()
    total_price = 0
    reservations = []

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id, passengerName, seatRow, seatColumn, eTicketNumber FROM reservations")
    rows = cursor.fetchall()

    for row in rows:
        r = row["seatRow"]
        c = row["seatColumn"]
        price = cost_matrix[r][c]
        total_price += price
        reservations.append({
            "id": row["id"],
            "name": row["passengerName"],
            "row": r + 1,  # display as 1-indexed
            "col": c + 1,  # display as 1-indexed
            "eticket": row["eTicketNumber"],
            "price": price
        })

    cursor.close()
    conn.close()

    chart_img = generate_chart_image()
    return render_template(
        "admin_dashboard.html",
        reservations=reservations,
        total_price=total_price,
        chart_img=chart_img
    )

# reservation route
@routes.route('/new_reservation', methods=['GET', 'POST'])
def new_reservation():
    ensure_schema()

    chart_img = generate_chart_image()
    if request.method == 'POST':
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        seatRow = request.form.get("row")
        seatColumn = request.form.get("seat")

        if not first or not last or not seatColumn or not seatRow:
            return render_template("new_reservation.html", error="Must have all fields filled out.", chart_img=chart_img)

        row = int(seatRow) - 1
        seat = int(seatColumn) - 1
        passengerName = f"{first} {last}"
        seat_number = f"{row}-{seat}"

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM reservations WHERE seatRow=? AND seatColumn=?", (row, seat))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return render_template("new_reservation.html", error=f"Seat {seat_number} is already taken.", chart_img=chart_img)

        cost_matrix = get_cost_matrix()
        price = cost_matrix[row][seat]

        pattern = "INFOTC4320"
        i = j = 0
        result = []
        while i < len(first) or j < len(pattern):
            if i < len(first):
                result.append(first[i]); i += 1
            if j < len(pattern):
                result.append(pattern[j]); j += 1
        reservation_code = ''.join(result)

        cursor.execute("""
            INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber)
            VALUES (?, ?, ?, ?)
        """, (passengerName, row, seat, reservation_code))

        conn.commit()
        cursor.close()
        conn.close()

        chart_img = generate_chart_image()
        success = f"Congrats {first}! Row: {row + 1}, Seat: {seat + 1} is now reserved for you. Enjoy your Trip! Your eTicket number is: {reservation_code}."
        return render_template("new_reservation.html", chart_img=chart_img, success=success)

    return render_template("new_reservation.html", chart_img=chart_img)

@routes.route("/reservations")
def reservation_list():
    ensure_schema()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reservations")
    reservations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("reservation_list.html", reservations=reservations)

@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    ensure_schema()

    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("routes.reservation_list"))
