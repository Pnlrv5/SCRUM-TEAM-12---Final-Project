from sqlalchemy import create_engine, MetaData, Table, select

DB_PATH = "reservations.db"

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

def calculate_total_sales():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    metadata = MetaData()
    reservations = Table("reservations", metadata, autoload_with=engine)
    seat = select(reservations.c.seatRow, reservations.c.seatColumn)
    #connects to database 
    with engine.connect() as conn:
        reserved = conn.execute(seat).fetchall()
    cost_matrix = get_cost_matrix()

    #creats total and adds cost of each reserved seat
    total = 0
    for row, col in reserved:
        if 0 <= row < 12 and 0 <= col < 4:
            total += cost_matrix[row][col]

    return total
