from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    seat_row = db.Column(db.Integer, nullable=False)
    seat_col = db.Column(db.String(1), nullable=False)
    price = db.Column(db.Float, nullable=False)
    reservation_code = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"<Reservation {self.first_name} {self.last_name} Seat {self.seat_row}{self.seat_col}>"