import matplotlib
matplotlib.use('Agg') #terminal was giving a "will likely fail", so I found that this fixed that message
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, select

DB_PATH = "reservations.db"

def generate_chart_image():

    rows = 12
    cols = 4

    #connects to the database and gets all seats that are reserved 
    engine = create_engine(f"sqlite:///{DB_PATH}")
    metadata = MetaData()
    reservations = Table("reservations", metadata, autoload_with=engine)
    stmt = select(reservations.c.seatRow, reservations.c.seatColumn)
    with engine.connect() as conn:
        reserved_seats = conn.execute(stmt).fetchall()
    reserved_set = {(r, c) for r, c in reserved_seats}
    grid = [[False for _ in range(cols)] for _ in range(rows)]
    for r, c in reserved_set:
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] = True

    #create the chart
    fig, ax = plt.subplots(figsize=(cols *.6, rows *.4))
    ax.set_axis_off()
    for r in range(rows):
        for c in range(cols):
            marker = "[X]" if grid[r][c] else "[O]"
            ax.text(c, rows - 1 - r, marker, ha='center', va='center', fontsize=12, fontweight='bold')
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(-1, rows - .5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_bytes = buf.getvalue()
    encoded = base64.b64encode(img_bytes).decode("utf-8")

    return f"data:image/png;base64,{encoded}"
