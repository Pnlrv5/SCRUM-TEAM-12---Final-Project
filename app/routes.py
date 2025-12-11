from flask import Blueprint, render_template, request, redirect, url_for
from .database import get_connection

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('index.html')

@routes.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Quick validation for blank fields
        if not username or not password:
            return render_template(
                "admin_login.html",
                error="Username and password are required... try again."
            )

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username=%s", (username,))
        admin = cursor.fetchone()

        
        if not admin or password != admin["password_hash"]:
            return render_template(
                "admin_login.html",
                error="Invalid username or password... try again."
            )
        return redirect(url_for("routes.admin_dashboard"))
    return render_template("admin_login.html")


@routes.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")