import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

try:
    from .chart_generation import generate_chart_image
except Exception:
    generate_chart_image = None

routes = Blueprint("routes", __name__)

DB_FILENAME = "reservations.db"

def get_db_path():
    instance_dir = current_app.instance_path
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, DB_FILENAME)

def ensure_schema(conn):
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
            name TEXT,
            email TEXT,
            seat TEXT,
            price REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()

def ensure_default_admin(conn):
    row = conn.execute("SELECT COUNT(*) AS cnt FROM admin_users").fetchone()
    cnt = row[0] if row else 0
    if cnt == 0:
        conn.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        conn.commit()

def get_conn():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    ensure_default_admin(conn)
    return conn

def init_db(app):
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, DB_FILENAME)
    conn = sqlite3.connect(db_path)
    ensure_schema(conn)
    ensure_default_admin(conn)
    conn.close()

@routes.route("/")
def index():
    return render_template("index.html")

@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with get_conn() as conn:
            user = conn.execute(
                "SELECT username, password FROM admin_users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and user["password"] == password:
            session["admin_logged_in"] = True
            session["admin_username"] = user["username"]
            return redirect(url_for("routes.admin_dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("routes.admin_login"))

    return render_template("admin_login.html")

@routes.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "success")
    return redirect(url_for("routes.admin_login"))

@routes.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    with get_conn() as conn:
        reservations = conn.execute(
            "SELECT * FROM reservations ORDER BY created_at DESC, id DESC"
        ).fetchall()

    return render_template("admin_dashboard.html", reservations=reservations)

@routes.route("/chart")
def chart():
    if generate_chart_image is None:
        return "Chart generation not configured.", 500
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))
    return generate_chart_image()
