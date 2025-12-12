from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .chart_generation import generate_chart_image
import sqlite3

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('index.html')

# given in class document
def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# ✅ NEW: helper for protecting admin-only routes
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
                error="Username and password are required... try again."
            )

        conn = sqlite3.connect('reservations.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ✅ SQLite uses ? placeholders (NOT %s) and no dictionary=True
        cursor.execute(
            "SELECT username, password FROM admin_users WHERE username = ?",
            (username,)
        )
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        # ✅ professor schema uses column name password (NOT password_hash)
        if not admin or password != admin["password"]:
            return render_template(
                "admin_login.html",
                error="Invalid username or password... try again."
            )

        # ✅ Persist login
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
    # ✅ Protect dashboard
    if not admin_required():
        return redirect(url_for("routes.admin_login"))

    cost_matrix = get_cost_matrix()
    total_price = 0
    reservations = []

    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, passengerName, seatRow, seatColumn, eTicketNumber FROM reservations")
    rows = cursor.fetchall()

    for row in rows:
        r = row['seatRow']
        c = row['seatColumn']
        price = cost_matrix[r][c]
        total_price += price
        reservations.append({
            'id': row['id'],
            'name': row['passengerName'],
            'row': r + 1,  # 1-indexed
            'col': c + 1,  # 1-indexed
            'eticket': row['eTicketNumber'],
            'price': price
        })

    cursor.close()
    conn.close()

    chart_img = generate_chart_image()
    return render_template(
        "admin_dashboard.html",
        reservations=reservati
