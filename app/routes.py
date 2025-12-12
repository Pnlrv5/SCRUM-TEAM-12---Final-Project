from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .chart_generation import generate_chart_image
import sqlite3

routes = Blueprint('routes', __name__)

DB_PATH = "instance/reservations.db"

@routes.route('/')
def home():
    return render_template('index.html')

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

def admin_required():
    return session.get("is_admin") is True


@routes.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template(
                "admin_login.html",
                error="Username and password are required."
            )

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password FROM admin_users WHERE username = ?",
            (username,)
        )
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if not admin or password != admin["password"]:
            return render_template(
                "admin_login.html",
                error="Invalid username or password."
            )

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
    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    cost_matrix = get_cost_matrix()
    total_price = 0
    reservations = []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, passengerName, seatRow, seatColumn, eTicketNumber FROM reservations"
    )
    rows = cursor.fetchall()

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

    cursor.close()
    conn.close()

    chart_img = generate_chart_image()
    return render_template(
        "admin_dashboard.html",
        reservations=reservations,
        total_price=total_price,
        chart_img=chart_img
    )


@routes.route('/new_reservation', methods=['GET', 'POST'])
def new_reservation():
    chart_img = generate_chart_image()

    if request.method == 'POST':
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        seatRow = request.form.get("row")
        seatColumn = request.form.get("seat")

        if not first or not last or not seatRow or not seatColumn:
            return render_template(
                "new_reservation.html",
                error="All fields are required.",
                chart_img=chart_img
            )

        row = int(seatRow) - 1
        seat = int(seatColumn) - 1
        passengerName = f"{first} {last}"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM reservations WHERE seatRow=? AND seatColumn=?",
            (row, seat)
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return render_template(
                "new_reservation.html",
                error="Seat already taken.",
                chart_img=chart_img
            )

        cost_matrix = get_cost_matrix()
        price = cost_matrix[row][seat]

        pattern = "INFOTC4320"
        reservation_code = "".join(
            first[i] if i < len(first) else pattern[i - len(first)]
            for i in range(len(pattern))
        )

        cursor.execute(
            """
            INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber)
            VALUES (?, ?, ?, ?)
            """,
            (passengerName, row, seat, reservation_code)
        )

        conn.commit()
        cursor.close()
        conn.close()

        chart_img = generate_chart_image()
        success = (
            f"Congrats {first}! Row {row+1}, Seat {seat+1} reserved. "
            f"eTicket: {reservation_code}"
        )

        return render_template(
            "new_reservation.html",
            success=success,
            chart_img=chart_img
        )

    return render_template("new_reservation.html", chart_img=chart_img)


@routes.route("/reservations")
def reservation_list():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reservations")
    reservations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("reservation_list.html", reservations=reservations)


@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("routes.reservation_list"))
