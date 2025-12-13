import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

try:
    from .chart_generation import generate_chart_image
except Exception:
    generate_chart_image = None

routes = Blueprint("routes", __name__)

DB_FILENAME = "reservations.db"

def db_path():
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, DB_FILENAME)

def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passengerName TEXT NOT NULL,
                seatRow INTEGER NOT NULL,
                seatColumn INTEGER NOT NULL,
                eTicketNumber TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        row = conn.execute("SELECT COUNT(*) AS cnt FROM admin_users").fetchone()
        if row["cnt"] == 0:
            conn.execute(
                "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                ("admin", "admin123"),
            )
        conn.commit()

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

@routes.route("/")
def home():
    return render_template("index.html")

@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("admin_login.html", error="Username and password are required.")

        with get_conn() as conn:
            admin = conn.execute(
                "SELECT username, password_hash FROM admin_users WHERE username = ?",
                (username,),
            ).fetchone()

        if not admin or password != admin["password_hash"]:
            return render_template("admin_login.html", error="Invalid username or password.")

        session["admin_logged_in"] = True
        return redirect(url_for("routes.admin_dashboard"))

    return render_template("admin_login.html")

@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))
    return render_template("admin_dashboard.html")

@routes.route("/new_reservation", methods=["GET", "POST"])
def new_reservation():
    chart_img = generate_chart_image() if generate_chart_image else None

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
        seat_number = f"{row + 1}-{seat + 1}"

        with get_conn() as conn:
            existing = conn.execute(
                "SELECT 1 FROM reservations WHERE seatRow=? AND seatColumn=?",
                (row, seat),
            ).fetchone()

            if existing:
                return render_template("new_reservation.html", error=f"Seat {seat_number} is already taken.", chart_img=chart_img)

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

            conn.execute(
                """
                INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber)
                VALUES (?, ?, ?, ?)
                """,
                (passengerName, row, seat, reservation_code),
            )
            conn.commit()

        chart_img = generate_chart_image() if generate_chart_image else None
        success = f"Congrats {first}! Row: {row + 1}, Seat: {seat + 1} is now reserved for you. Your eTicket number is: {reservation_code}."
        return render_template("new_reservation.html", chart_img=chart_img, success=success)

    return render_template("new_reservation.html", chart_img=chart_img)

@routes.route("/reservations")
def reservation_list():
    with get_conn() as conn:
        reservations = conn.execute("SELECT * FROM reservations ORDER BY created_at DESC, id DESC").fetchall()
    return render_template("reservation_list.html", reservations=reservations)

@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
        conn.commit()
    return redirect(url_for("routes.reservation_list"))

@routes.route("/chart")
def chart():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))
    if generate_chart_image is None:
        return "Chart unavailable", 500
    return generate_chart_image()
