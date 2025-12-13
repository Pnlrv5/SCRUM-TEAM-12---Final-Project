import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import io
import base64

from .models import Reservation


def generate_chart_image():
    rows = 12
    cols = 4

    # Build empty grid
    grid = [[False for _ in range(cols)] for _ in range(rows)]

    # Pull reservations from the same DB your app is using (SQLAlchemy ORM)
    reservations = Reservation.query.all()
    for r in reservations:
        if 0 <= r.seatRow < rows and 0 <= r.seatColumn < cols:
            grid[r.seatRow][r.seatColumn] = True

    # Draw chart
    fig, ax = plt.subplots(figsize=(cols * 0.6, rows * 0.4))
    ax.set_axis_off()

    for r in range(rows):
        for c in range(cols):
            marker = "[X]" if grid[r][c] else "[O]"
            ax.text(
                c, rows - 1 - r, marker,
                ha="center", va="center",
                fontsize=12, fontweight="bold"
            )

    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(-1, rows - 0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)

    buf.seek(0)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Return an <img> src value your template can use
    return f"data:image/png;base64,{encoded}"
