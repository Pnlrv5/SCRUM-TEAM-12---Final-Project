import os
import sqlite3

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)

try:
    from chart_generation import generate_chart_image
except Exception:
    generate_chart_image = None

routes = Blueprint("routes", __name__)

DB_FILENAME = "reservations.db"


def get_db_path():
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, DB_FILENAME)


def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            seat TEXT,
            price REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM admin_users"
    ).fetchone()[0]

    if count == 0:
        conn.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    conn.commit()
    conn.close()


@routes.before_app_first_request
def setup_database():
    init_db()


@routes.route("/")
def index():
    return render_template("index.html")


@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_conn()
        user = conn.execute(
            "SELECT * FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and user["password"] == password:
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("routes.admin_dashboard"))

        flash("Invalid username or password", "error")

    return render_template("admin_login.html")


@routes.route("/admin_logout")
def admin_logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("routes.admin_login"))


@routes.route("/admin")
@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    conn = get_conn()
    reservations = conn.execute(
        "SELECT * FROM reservations ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        reservations=reservations
    )


@routes.route("/chart")
def chart():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    if generate_chart_image is None:
        return "Chart unavailable", 500

    return generate_chart_image()
