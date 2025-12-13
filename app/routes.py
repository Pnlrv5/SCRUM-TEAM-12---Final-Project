import os
print("ROUTES FILE RUNNING:", os.path.abspath(__file__))

from flask import Blueprint, render_template, request, redirect, url_for, session
from .database import db
from .models import AdminUser, Reservation

try:
    from .chart_generation import generate_chart_image
except Exception:
    generate_chart_image = None

routes = Blueprint("routes", __name__)

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

        admin = AdminUser.query.filter_by(username=username).first()
        if not admin or admin.password_hash != password:
            return render_template("admin_login.html", error="Invalid username or password.")

        session["admin_logged_in"] = True
        session["admin_username"] = admin.username
        return redirect(url_for("routes.admin_dashboard"))

    return render_template("admin_login.html")

@routes.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    return redirect(url_for("routes.admin_login"))

@routes.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    reservations = Reservation.query.order_by(Reservation.created_at.desc(), Reservation.id.desc()).all()
    return render_template("admin_dashboard.html", reservations=reservations)

@routes.route("/new_reservation", methods=["GET", "POST"])
def new_reservation():
    chart_img = generate_chart_image() if generate_chart_image else None

    if request.method == "POST":
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        seatRow = request.form.get("row")
        seatColumn = request.form.get("seat")

        if not first or not last or not seatRow or not seatColumn:
            return render_template("new_reservation.html", error="Must have all fields filled out.", chart_img=chart_img)

        row = int(seatRow) - 1
        seat = int(seatColumn) - 1
        passengerName = f"{first} {last}"
        seat_number = f"{row}-{seat}"

        existing = Reservation.query.filter_by(seatRow=row, seatColumn=seat).first()
        if existing:
            return render_template("new_reservation.html", error=f"Seat {seat_number} is already taken.", chart_img=chart_img)

        cost_matrix = get_cost_matrix()
        price = cost_matrix[row][seat]  # not stored, but you can add a column if needed

        pattern = "INFOTC4320"
        i = j = 0
        result = []
        while i < len(first) or j < len(pattern):
            if i < len(first):
                result.append(first[i]); i += 1
            if j < len(pattern):
                result.append(pattern[j]); j += 1
        reservation_code = "".join(result)

        r = Reservation(
            passengerName=passengerName,
            seatRow=row,
            seatColumn=seat,
            eTicketNumber=reservation_code,
        )
        db.session.add(r)
        db.session.commit()

        chart_img = generate_chart_image() if generate_chart_image else None
        success = f"Congrats {first}! Row: {row + 1}, Seat: {seat + 1} is now reserved. eTicket: {reservation_code}."
        return render_template("new_reservation.html", chart_img=chart_img, success=success)

    return render_template("new_reservation.html", chart_img=chart_img)

@routes.route("/reservations")
def reservation_list():
    reservations = Reservation.query.order_by(Reservation.id.desc()).all()
    return render_template("reservation_list.html", reservations=reservations)

@routes.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("routes.admin_login"))

    r = Reservation.query.get_or_404(reservation_id)
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for("routes.reservation_list"))

@routes.route("/chart")
def chart():
    if generate_chart_image is None:
        return "Chart unavailable", 500
    return generate_chart_image()
