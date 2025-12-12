import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

routes = Blueprint("routes", __name__)

# -----------------------------
# Database helpers
# -----------------------------

def get_db_path():
    # Always use Flask instance folder
    return os.path.join(current_app.instance_path, "reservations.db")

def get_conn():
    os.makedirs(current_app.instance_path, exist_ok=True)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def ensure_admin_table():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)
    conn.execute("""
        INSERT OR IGNORE INTO admin_users (username, password)
        VALUES ('admin', 'admin123');
    """)
    conn.commit()
    conn.close()

# -----------------------------
# Admin Login
# -----------------------------

@routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    ensure_admin_table()  

    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_conn()
        admin = conn.execute(
            "SELECT * FROM admin_users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            return redirect(url_for("routes.admin_dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("admin_login.html", error=error)

# -----------------------------
# Admin Dashboard
# -----------------------------

@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    return render_template("admin_dashboard.html")

# -----------------------------
# Admin Logout
# -----------------------------

@routes.route("/admin_logout")
def admin_logout():
    session.clear()
    return redirect(url_for("routes.admin_login"))
