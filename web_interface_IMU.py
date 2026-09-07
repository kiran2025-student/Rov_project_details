#!/usr/bin/env python3
"""
================================================================================
 IMU Web Dashboard — view live sensor data in a browser instead of a terminal
================================================================================

WHAT THIS IS
-------------
A small, standalone Flask web server that reads the CSV log file your
V3_two_sensor_IMU_code.py script is ALREADY writing (in logs/), and shows
the latest reading for each sensor as a simple auto-refreshing web page.

IMPORTANT: this does NOT modify or import your sensor script in any way.
It only reads the CSV file from disk. You run this as a SEPARATE process,
alongside your existing script — if this dashboard crashes or you close
it, your sensor script keeps running completely unaffected.

WHY THIS INSTEAD OF THE TERMINAL
----------------------------------
- No SSH terminal ANSI/flicker issues at all — it's a normal web page.
- Viewable from your phone or laptop's browser on the same WiFi network,
  not just the SSH session you're currently in.
- Bigger, clearer display than a scrolling terminal.

HOW TO RUN
-----------
1. Install Flask (one-time):
       pip3 install flask --break-system-packages

2. Run your sensor script as normal, in one terminal:
       python3 V3_two_sensor_IMU_code.py

3. In a SECOND terminal (SSH session), run this dashboard:
       python3 imu_web_dashboard.py

4. Find your Pi's IP address if you don't already know it:
       hostname -I

5. On your phone or laptop (same WiFi network as the Pi), open a browser
   and go to:
       http://<your-pi's-ip-address>:5000
   For example: http://192.168.1.42:5000

The page auto-refreshes every second. If it says "STALE" next to a
sensor, that sensor hasn't logged a new reading recently — usually means
the main script has stopped, crashed, or that sensor disconnected.

CONFIGURATION
---------------
LOG_DIR must match CSV_LOG_DIR in your sensor script (currently "logs",
a relative path) — run this dashboard from the SAME directory you run
V3_two_sensor_IMU_code.py from, so both scripts agree on where "logs/" is.
================================================================================
"""

import csv
import glob
import io
import os
import time

from flask import Flask

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

# Must match CSV_LOG_DIR in V3_two_sensor_IMU_code.py. Run this dashboard
# from the same working directory as that script so "logs/" resolves to
# the same folder for both.
LOG_DIR = "logs"

# How often the browser page auto-refreshes (seconds).
REFRESH_SECONDS = 1

# If a sensor's last logged reading is older than this, it's shown as
# STALE instead of a normal reading — usually means the main script
# stopped, crashed, or that sensor disconnected.
STALE_THRESHOLD_SECONDS = 3

# How many bytes to read from the END of the log file to find the latest
# rows, instead of reading the whole (possibly large, hours-long) file on
# every single page refresh. 8KB comfortably contains the last several
# interleaved IMU-1/IMU-2 rows even at a fast log rate.
TAIL_READ_BYTES = 8192

# The exact column order V3_two_sensor_IMU_code.py's CSV_COLUMNS uses.
# Must match that file's CSV_COLUMNS exactly, or columns will be
# mislabeled here.
CSV_COLUMNS = [
    "timestamp", "sensor_name", "address",
    "roll_deg", "pitch_deg", "yaw_deg",
    "cal_system", "cal_gyro", "cal_accel", "cal_mag",
]

# Maximum allowed change (degrees) in Roll, Pitch, or Yaw between two
# consecutive logged readings for a sensor to be shown as "STABLE" here.
# Matches the same threshold/logic used in V3_two_sensor_IMU_code.py's
# own terminal stability indicator, so both agree on what "stable" means
# — but this dashboard computes it independently from the CSV file, since
# it never imports or talks to that script directly.
STABILITY_THRESHOLD_DEG = 2.0

app = Flask(__name__)


# --------------------------------------------------------------------------
# CSV READING (tail-based, so this stays fast even on an hours-long log)
# --------------------------------------------------------------------------
def find_latest_log_file():
    """Returns the path to the most recently modified imu_log_*.csv file, or None."""
    pattern = os.path.join(LOG_DIR, "imu_log_*.csv")
    matches = glob.glob(pattern)
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def read_latest_readings(csv_path):
    """
    Reads only the last TAIL_READ_BYTES of the CSV file (not the whole
    file — important once the log has been running for hours) and
    returns, for each sensor name found in that tail:
        {sensor_name: {"latest": {...row...}, "previous": {...row...} or None}}

    Keeping the previous row (not just the latest) is what lets
    compute_stability() below compare two consecutive readings, the same
    way the terminal script's own stability indicator does.
    """
    file_size = os.path.getsize(csv_path)
    read_size = min(TAIL_READ_BYTES, file_size)

    with open(csv_path, "rb") as f:
        f.seek(file_size - read_size)
        tail_bytes = f.read()

    # Decode and drop the first line, since seeking mid-file likely lands
    # inside a row rather than exactly on a line boundary.
    text = tail_bytes.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    if file_size > read_size and lines:
        lines = lines[1:]  # drop the probably-partial first line

    reader = csv.reader(io.StringIO("\n".join(lines)))
    history_by_sensor = {}  # sensor_name -> [row_dict, row_dict, ...] in file order
    for row in reader:
        if len(row) != len(CSV_COLUMNS):
            continue  # skip the header row or any malformed/partial line
        row_dict = dict(zip(CSV_COLUMNS, row))
        history_by_sensor.setdefault(row_dict["sensor_name"], []).append(row_dict)

    result = {}
    for sensor_name, rows in history_by_sensor.items():
        result[sensor_name] = {
            "latest": rows[-1],
            "previous": rows[-2] if len(rows) >= 2 else None,
        }
    return result


def compute_stability(latest_row, previous_row):
    """
    Compares two consecutive readings for the SAME sensor and returns
    "STABLE", "UNSTABLE (fluctuating)", or "N/A (not enough data yet)".

    Mirrors the logic of get_stability_status() in
    V3_two_sensor_IMU_code.py exactly (same threshold, same yaw-wraparound
    handling) — but reimplemented here to work from CSV row dicts (string
    values) instead of the script's in-memory reading dicts, since this
    dashboard only ever reads the CSV file and never imports that script.
    """
    if previous_row is None:
        return "N/A (not enough data yet)"

    delta_roll = abs(float(latest_row["roll_deg"]) - float(previous_row["roll_deg"]))
    delta_pitch = abs(float(latest_row["pitch_deg"]) - float(previous_row["pitch_deg"]))

    # Yaw wraps at 0/360 degrees (359 -> 1 is really only a 2-degree
    # change, not 358) -- corrected the same way the terminal script does,
    # so a sensor sitting still near that boundary isn't falsely flagged.
    raw_delta_yaw = abs(float(latest_row["yaw_deg"]) - float(previous_row["yaw_deg"]))
    delta_yaw = min(raw_delta_yaw, 360 - raw_delta_yaw)

    if max(delta_roll, delta_pitch, delta_yaw) > STABILITY_THRESHOLD_DEG:
        return "UNSTABLE (fluctuating)"
    return "STABLE"


# --------------------------------------------------------------------------
# WEB PAGE
# --------------------------------------------------------------------------
def render_sensor_block(sensor_name, entry):
    """
    Builds the HTML block for one sensor's latest reading, or a
    placeholder if no data has been seen for it yet.

    `entry` is {"latest": row_dict, "previous": row_dict or None} — see
    read_latest_readings() — or None if this sensor hasn't appeared in
    the log at all yet.
    """
    if entry is None:
        return f"""
        <div class="sensor-card waiting">
            <h2>{sensor_name}</h2>
            <p class="status">Waiting for data...</p>
        </div>"""

    row = entry["latest"]

    # Check staleness: how long ago was this row logged?
    from datetime import datetime
    try:
        logged_at = datetime.fromisoformat(row["timestamp"])
        age_seconds = (datetime.now() - logged_at).total_seconds()
    except ValueError:
        age_seconds = None

    is_stale = age_seconds is not None and age_seconds > STALE_THRESHOLD_SECONDS
    status_class = "stale" if is_stale else "live"
    status_text = (
        f"STALE (last update {age_seconds:.1f}s ago)" if is_stale
        else f"Live (updated {age_seconds:.1f}s ago)" if age_seconds is not None
        else "Live"
    )

    # Stability badge: compares this reading to the one before it. Skipped
    # entirely while the sensor is already stale -- a frozen/dead sensor
    # will trivially look "STABLE" (nothing is changing because nothing
    # is arriving), which would be misleading to show next to a red
    # STALE badge, so stability is only meaningful while data is live.
    if is_stale:
        stability_html = ""
    else:
        stability = compute_stability(row, entry["previous"])
        stability_class = (
            "stable" if stability == "STABLE"
            else "unstable" if stability.startswith("UNSTABLE")
            else "unknown"
        )
        stability_html = f'<p class="stability {stability_class}">{stability}</p>'

    return f"""
    <div class="sensor-card {status_class}">
        <h2>{sensor_name} <span class="addr">@ {row['address']}</span></h2>
        <p class="status">{status_text}</p>
        {stability_html}
        <table>
            <tr><td>Roll</td><td>{row['roll_deg']}&deg;</td></tr>
            <tr><td>Pitch</td><td>{row['pitch_deg']}&deg;</td></tr>
            <tr><td>Yaw</td><td>{row['yaw_deg']}&deg;</td></tr>
        </table>
        <p class="cal">
            Cal &mdash; System: {row['cal_system']}
            Gyro: {row['cal_gyro']}
            Accel: {row['cal_accel']}
            Mag: {row['cal_mag']}
        </p>
    </div>"""


@app.route("/")
def dashboard():
    log_path = find_latest_log_file()

    if log_path is None:
        body = """
        <div class="sensor-card waiting">
            <h2>No log file found yet</h2>
            <p>Make sure V3_two_sensor_IMU_code.py is running, and that
            this dashboard is started from the SAME directory as that
            script (so both agree on where the "logs" folder is).</p>
        </div>"""
    else:
        readings = read_latest_readings(log_path)
        body = render_sensor_block("IMU-1", readings.get("IMU-1"))
        body += render_sensor_block("IMU-2", readings.get("IMU-2"))

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="{REFRESH_SECONDS}">
    <title>IMU Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, sans-serif;
            background: #111;
            color: #eee;
            margin: 0;
            padding: 20px;
        }}
        h1 {{ text-align: center; }}
        .sensor-card {{
            background: #1c1c1c;
            border-radius: 12px;
            padding: 20px;
            margin: 16px auto;
            max-width: 420px;
            border-left: 6px solid #444;
        }}
        .sensor-card.live {{ border-left-color: #2ecc71; }}
        .sensor-card.stale {{ border-left-color: #e74c3c; }}
        .sensor-card.waiting {{ border-left-color: #f39c12; }}
        .sensor-card h2 {{ margin: 0 0 4px 0; }}
        .addr {{ color: #888; font-size: 0.7em; font-weight: normal; }}
        .status {{ color: #aaa; font-size: 0.85em; margin-top: 0; }}
        table {{ width: 100%; font-size: 1.4em; margin-top: 10px; }}
        table td:first-child {{ color: #999; }}
        table td:last-child {{ text-align: right; font-weight: bold; }}
        .cal {{ color: #888; font-size: 0.85em; margin-top: 12px; }}
        .stability {{
            display: inline-block;
            font-size: 0.85em;
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 20px;
            margin: 4px 0 0 0;
        }}
        .stability.stable {{ background: #1e4620; color: #4ade80; }}
        .stability.unstable {{ background: #4a1e1e; color: #f87171; }}
        .stability.unknown {{ background: #3a3220; color: #facc15; }}
    </style>
</head>
<body>
    <h1>ROV IMU Dashboard</h1>
    {body}
</body>
</html>"""


if __name__ == "__main__":
    if not os.path.isdir(LOG_DIR):
        print(f"WARNING: '{LOG_DIR}' directory not found from here. "
              f"Run this dashboard from the same folder as "
              f"V3_two_sensor_IMU_code.py, or update LOG_DIR above.")

    print("Starting IMU web dashboard...")
    print("Open this from your phone/laptop browser (same WiFi network):")
    print("  http://<this-pi's-ip-address>:5000")
    print("Find the Pi's IP with: hostname -I")
    # host="0.0.0.0" is required to be reachable from OTHER devices on the
    # network -- the Flask default (127.0.0.1) only accepts connections
    # from the Pi itself, which would make this useless for viewing on
    # your phone/laptop.
    app.run(host="0.0.0.0", port=5000, debug=False)
