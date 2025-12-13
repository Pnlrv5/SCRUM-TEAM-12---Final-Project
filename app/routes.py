import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

try:
    from .chart_generation import generate_chart_image
except Exception:
    generate_chart_image = None

routes = Blueprint("routes", __name__)
DB_FILENAME = "reservations.db"


def get_db_path() -> str:
    instance_dir = current_app.instance_path
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, DB_FILENAME)


def init_db() -> None:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passengerName TEXT NOT NULL,
            seatRow INTEGER NOT NULL,
            seatColumn INTEGER NOT NULL,
            eTicketNumber TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    row = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()
    if row and row[0] == 0:
        conn.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123"),
        )
    conn.commit()
    conn.close()


def get_conn() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


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
            user = conn.execute(
                "SELECT username, password FROM admin_users WHERE username = ?",
                (username,),
            ).fetchone()

        if user and user["password"] == password:
            session["admin_logged_in"] = True
            session["admin_username"] = user["username"]
            return redirect(url_for("routes.admin_dashboard"))

        return render_template("admin_login.html", error="Invalid username or password.")

    return render_template("admin_login.html")


@routes.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.")
    return redirect(url_for("routes.admin_login"))


@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    with get_conn() as conn:
        reservations = conn.execute(
            "SELECT * FROM reservations ORDER BY created_at DESC, id DESC"
        ).fetchall()

    return render_template("admin_dashboard.html", reservations=reservations)


@routes.route("/reservations")
def reservation_list():
    with get_conn() as conn:
        reservations = conn.execute("SELECT * FROM reservations ORDER BY id DESC").fetchall()
    return render_template("reservation_list.html", reservations=reservations)


@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    with get_conn() as conn:
        conn.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
        conn.commit()

    return redirect(url_for("routes.reservation_list"))


@routes.route("/chart")
def chart():
    if generate_chart_image is None:
        return "Chart unavailable", 500
    return generate_chart_image()
