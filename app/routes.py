import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

routes = Blueprint("routes", __name__)
DB_FILENAME = "reservations.db"


def db_path():
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, DB_FILENAME)


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passengerName TEXT,
            seatRow INTEGER,
            seatColumn INTEGER,
            eTicketNumber TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) AS c FROM admin_users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    conn.commit()
    conn.close()


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

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
        admin = cur.fetchone()
        conn.close()

        if admin and admin["password"] == password:
            session["is_admin"] = True
            return redirect(url_for("routes.admin_dashboard"))

        return render_template("admin_login.html", error="Invalid username or password.")

    return render_template("admin_login.html")


@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("routes.admin_login"))

    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservations ORDER BY id DESC")
    reservations = cur.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", reservations=reservations)


@routes.route("/reservations")
def reservation_list():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservations ORDER BY id DESC")
    reservations = cur.fetchall()
    conn.close()

    return render_template("reservation_list.html", reservations=reservations)


@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("routes.reservation_list"))
