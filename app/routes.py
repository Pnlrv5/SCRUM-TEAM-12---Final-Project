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

routes = Blueprint("routes", __name__)
DB_FILENAME = "reservations.db"


def get_db_path():
    instance_dir = current_app.instance_path
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, DB_FILENAME)


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

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

    row = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()
    if row[0] == 0:
        conn.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    conn.commit()
    conn.close()


def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


@routes.route("/")
def index():
    return render_template("index.html")


@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_conn()
        user = conn.execute(
            "SELECT * FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and user["password"] == password:
            session["admin_logged_in"] = True
            return redirect(url_for("routes.admin_dashboard"))

        flash("Invalid login")
        return redirect(url_for("routes.admin_login"))

    return render_template("admin_login.html")


@routes.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    conn = get_conn()
    reservations = conn.execute(
        "SELECT * FROM reservations ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", reservations=reservations)


@routes.route("/admin_logout")
def admin_logout():
    session.clear()
    return redirect(url_for("routes.admin_login"))
