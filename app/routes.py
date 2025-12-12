import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .chart_generation import generate_chart_image

routes = Blueprint("routes", __name__)

# -----------------------------
# DB helpers (ALWAYS use instance/reservations.db)
# -----------------------------

def get_db_path() -> str:
    # Flask's instance folder path (we will always store the DB there)
    db_path = os.path.join(current_app.instance_path, "reservations.db")
    os.makedirs(current_app.instance_path, exist_ok=True)
    return db_path

def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables():
    conn = get_conn()
    cur = conn.cursor()

    # reservations table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passengerName TEXT NOT NULL,
            seatRow INTEGER NOT NULL,
            seatColumn INTEGER NOT NULL,
            eTicketNumber TEXT NOT NULL
        )
    """)

    # admin_users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def ensure_default_admin():
    # creates admin/admin123 if no admin exists
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM admin_users")
    cnt = cur.fetchone()["cnt"]

    if cnt == 0:
        cur.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        conn.commit()

    cur.close()
    conn.close()

# run table setup once before the first request
@routes.before_app_request
def init_db_once():
    ensure_tables()
    ensure_default_admin()


# -----------------------------
# App routes
# -----------------------------

@routes.route("/")
def home():
    return render_template("index.html")

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

def admin_required():
    return session.get("is_admin") is True

@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("admin_login.html", error="Username and password are required... try again.")

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM admin_users WHERE username = ?", (username,))
        admin = cur.fetchone()

        cur.close()
        conn.close()

        if not admin or password != admin["password"]:
            return render_template("admin_login.html", error="Invalid username or password... try again.")

        session.clear()
        session["is_admin"] = True
        session["admin_username"] = username
        return redirect(url_for("routes.admin_dashboard"))

    return render_template("admin_login.html")

@routes.route("/admin_logout")
def admin_logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("routes.admin_login"))

@routes.route("/admin_dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    cost_matrix = get_cost_matrix()
    total_price = 0
    reservations = []

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, passengerName, seatRow, seatColumn, eTicketNumber FROM reservations")
    rows = cur.fetchall()

    for row in rows:
        r = row["seatRow"]
        c = row["seatColumn"]
        price = cost_matrix[r][c]
        total_price += price
        reservations.append({
            "id": row["id"],
            "name": row["passengerName"],
            "row": r + 1,
            "col": c + 1,
            "eticket": row["eTicketNumber"],
            "price": price
        })

    cur.close()
    conn.close()

    chart_img = generate_chart_image()
    return render_template(
        "admin_dashboard.html",
        reservations=reservations,
        total_price=total_price,
        chart_img=chart_img
    )

@routes.route("/new_reservation", methods=["GET", "POST"])
def new_reservation():
    chart_img = generate_chart_image()

    if request.method == "POST":
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
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM reservations WHERE seatRow=? AND seatColumn=?", (row, seat))
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return render_template("new_reservation.html", error=f"Seat {seat_number} is already taken.", chart_img=chart_img)

        cost_matrix = get_cost_matrix()
        price = cost_matrix[row][seat]

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
        reservation_code = "".join(result)

        cur.execute("""
            INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber)
            VALUES (?, ?, ?, ?)
        """, (passengerName, row, seat, reservation_code))

        conn.commit()
        cur.close()
        conn.close()

        chart_img = generate_chart_image()
        success = (
            f"Congrats {first}! Row: {row + 1}, Seat: {seat + 1} is now reserved for you. "
            f"Enjoy your Trip! Your eTicket number is: {reservation_code}."
        )
        return render_template("new_reservation.html", chart_img=chart_img, success=success)

    return render_template("new_reservation.html", chart_img=chart_img)

@routes.route("/reservations")
def reservation_list():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservations")
    reservations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("reservation_list.html", reservations=reservations)

@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("routes.reservation_list"))
