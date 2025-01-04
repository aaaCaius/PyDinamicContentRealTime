import time
import threading
import random
from io import BytesIO

# Flask imports
from flask import Flask, render_template, request, redirect, url_for, send_file

# Matplotlib for plotting
import matplotlib
matplotlib.use("Agg")  # For headless environments
import matplotlib.pyplot as plt

import logging



app = Flask(__name__)

# --------------------------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------------------------
global_state = {
    "message": "Hello from the server!"
}

plot_data = {
    "x": [],
    "y1": [],
    "y2": [],
    "max_points": 30
}

time_counter = 0
lock = threading.Lock()

# --------------------------------------------------------------------
# BACKGROUND THREAD: update the plot data every 2 seconds
# --------------------------------------------------------------------
def plot_updater():
    global time_counter
    while True:
        with lock:
            time_counter += 1

            # X values
            plot_data["x"].append(time_counter)

            # y1: random walk
            if not plot_data["y1"]:
                plot_data["y1"].append(random.randint(0, 5))
            else:
                prev_y1 = plot_data["y1"][-1]
                step = random.choice([-1, 0, 1])
                plot_data["y1"].append(max(0, prev_y1 + step))

            # y2: simple sine wave
            import math
            y2_val = 5 + 2 * math.sin(time_counter * 0.3)
            plot_data["y2"].append(y2_val)

            # discard oldest if beyond max_points
            if len(plot_data["x"]) > plot_data["max_points"]:
                plot_data["x"].pop(0)
                plot_data["y1"].pop(0)
                plot_data["y2"].pop(0)
        time.sleep(2)

threading.Thread(target=plot_updater, daemon=True).start()

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------

@app.route("/")
def home():
    # redirect to main clock page
    return redirect(url_for("clock_page"))

@app.route("/clock")
def clock_page():
    """
    Main page:
      - left menu
      - top clock widget (300px)
      - bottom plot widget (400px)
    Uses 'clock.html' which extends 'base.html'.
    """
    return render_template("clock.html")

@app.route("/clock_content")
def clock_content():
    """
    1-second meta refresh clock inside an iframe.
    Renders 'clock_content.html'.
    """
    # We'll compute time & message inside the template for simplicity
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = global_state["message"]
    return render_template("clock_content.html", now_str=now_str, message=msg)

@app.route("/plot_content")
def plot_content():
    """
    1-second meta refresh plot inside an iframe.
    Renders 'plot_content.html'.
    """
    return render_template("plot_content.html")

@app.route("/plot_image")
def plot_image():
    """
    Creates the PNG for the plot (dark theme, no grid, no legend).
    """
    with lock:
        xs = plot_data["x"]
        y1 = plot_data["y1"]
        y2 = plot_data["y2"]

    plt.style.use("dark_background")

    fig, ax = plt.subplots(figsize=(12, 3), dpi=100)

    ax.plot(xs, y1, color="#56B4E9", linewidth=2, marker='o')
    ax.plot(xs, y2, color="#F0E442", linewidth=2, marker='s')

    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Real-Time Plot", color="#fff")

    # No grid or legend
    ax.spines["bottom"].set_color("#888")
    ax.spines["top"].set_color("#888")
    ax.spines["right"].set_color("#888")
    ax.spines["left"].set_color("#888")
    ax.xaxis.label.set_color("#ccc")
    ax.yaxis.label.set_color("#ccc")
    ax.tick_params(axis='x', colors='#ccc')
    ax.tick_params(axis='y', colors='#ccc')

    if xs:
        ax.set_xlim([min(xs), max(xs)])

    png_image = BytesIO()
    fig.savefig(png_image, format="png", bbox_inches="tight")
    plt.close(fig)
    png_image.seek(0)
    return send_file(png_image, mimetype="image/png")

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    """
    Form for updating global_state["message"].
    Renders 'settings.html'.
    """
    if request.method == "POST":
        global_state["message"] = request.form.get("message", "")
        return redirect(url_for("settings_page"))

    return render_template("settings.html", message=global_state["message"])

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
if __name__ == "__main__":
    # Set Logging level to ERROR
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    # Run the app
    app.run(debug=False, threaded=True)
