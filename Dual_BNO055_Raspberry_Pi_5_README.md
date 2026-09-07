# V3_two_sensor_IMU_code.py — Technical Documentation

This documents exactly what `V3_two_sensor_IMU_code.py` does as it
currently stands, including the sensor-stability indicator added on top
of the original script. For physical wiring, see `BNO055_Wiring_Guide.md`.
For a browser-based view of this same data, see `imu_web_dashboard.py`
(covered at the end of this document).

---

## 1. What this script does

Reads orientation from one or two Bosch BNO055 9-DOF IMU sensors on a
shared I2C bus, and for each sensor prints:

- **Roll, Pitch, Yaw** in human-readable degrees
- **Calibration status** (System / Gyro / Accel / Mag, each 0–3)
- **Stability status** — whether the sensor's output is currently steady
  or fluctuating (see [Section 5](#5-sensor-stability-indicator))

Every successful reading is also appended to a CSV log file for later
analysis.

---

## 2. Requirements

**Hardware**
- Raspberry Pi (any model with an I2C header — this was built/tested
  against a Raspberry Pi 5)
- One or two BNO055 breakout boards
- Jumper wires

**Software**
```bash
sudo pip3 install --break-system-packages \
    adafruit-circuitpython-bno055 \
    adafruit-blinka
```
I2C must be enabled first: `sudo raspi-config` → *Interface Options* →
*I2C* → *Enable*.

Confirm both sensors are visible before running the script:
```bash
i2cdetect -y 1
# Expect entries at 0x28 and 0x29
```

---

## 3. Configuration reference

All of these are constants near the top of the file — edit them directly
to change behavior, no command-line flags needed.

| Constant | Default | What it controls |
|---|---|---|
| `SENSOR_1_ADDRESS` | `0x28` | I2C address of the first sensor (ADR pin → GND) |
| `SENSOR_2_ADDRESS` | `0x29` | I2C address of the second sensor (ADR pin → 3.3V) |
| `SINGLE_SENSOR_MODE` | `False` | Set `True` to run with only sensor #1 connected |
| `READ_INTERVAL_S` | `0.1` | Poll rate — `0.1` = 10Hz |
| `READ_RETRIES` | `2` | Retries on a transient I2C read error before giving up that cycle |
| `RETRY_DELAY_S` | `0.01` | Delay between retries |
| `CALIBRATION_READ_EVERY_N_CYCLES` | `10` | How often calibration status is re-read (it changes far slower than orientation, so it isn't read every cycle) |
| `I2C_FREQUENCY_HZ` | `400000` | I2C bus speed (Fast Mode). Helps only marginally on the BNO055 specifically — see the comment in the script for why |
| `PRINT_EVERY_N_CYCLES` | `1` | How often a reading is printed to the console. Raise this (e.g. `5`) if console output is too fast to read |
| `CSV_FLUSH_EVERY_N_CYCLES` | `1` | How often the CSV file is flushed to disk |
| `CSV_LOG_DIR` | `"logs"` | Folder the CSV log is written into (relative to wherever you run the script from) |
| **`STABILITY_THRESHOLD_DEG`** | **`2.0`** | **Added.** Max allowed change (degrees) in Roll/Pitch/Yaw between two consecutive readings before a sensor is flagged `UNSTABLE` — see Section 5 |

---

## 4. How the read loop works

1. `validate_config()` — checks that none of the cycle-throttling
   constants above are set to `0` (which would crash the loop with a
   divide-by-zero); exits cleanly with a clear message if so.
2. `setup_sensors()` — opens the shared I2C bus and connects to
   whichever sensor(s) are configured. If neither sensor connects, the
   script exits with a message pointing at `i2cdetect -y 1`.
3. `run_read_loop()` — the main loop:
   - Reads each sensor (`BNO055Sensor.read_orientation()`), which
     retries transient I2C errors up to `READ_RETRIES` times before
     giving up for that cycle and returning `None`.
   - Computes each sensor's stability status (see Section 5).
   - Prints the reading + stability line (throttled by
     `PRINT_EVERY_N_CYCLES`).
   - Logs the reading to CSV (a failed/`None` reading is silently
     skipped — not written as a row).
   - Holds a fixed sample rate using `time.monotonic()`, so a slow
     cycle (e.g. one that hit a retry) doesn't cause the whole run to
     drift behind schedule.
4. On Ctrl+C, `main()` flushes and closes the CSV file and releases the
   I2C bus (`i2c.deinit()`) before exiting — skipping that release step
   is a known cause of the *next* run failing to reopen the I2C bus
   without a reboot.

---

## 5. Sensor stability indicator

This is the addition made on top of the original script. It answers a
different question than the calibration numbers do:

- **Calibration status** (`Cal S:_ G:_ A:_ M:_`) reports the sensor's own
  *internal* calibration state.
- **Stability status** (new) reports whether the *actual values coming
  out* are currently jumping around or holding steady — a more direct
  answer to "is this sensor behaving reliably right now?"

**How it works** (`get_stability_status()`): each cycle, the current
Roll/Pitch/Yaw is compared to that same sensor's previous reading.

- If **any** of Roll, Pitch, or Yaw changed by more than
  `STABILITY_THRESHOLD_DEG` (default `2.0°`) since the last reading, the
  sensor is reported `UNSTABLE (fluctuating)`.
- Otherwise it's `STABLE`.
- Three edge cases are handled explicitly:
  - **No data this cycle** → `N/A (no data)`
  - **No previous reading yet** (first cycle for that sensor) →
    `N/A (first reading)`
  - **Yaw wraparound**: Yaw is a 0–360° compass heading, so a change
    from 359° to 1° is really only a 2° rotation, not a 358° jump. The
    comparison corrects for this so a sensor sitting still near that
    boundary isn't falsely flagged as unstable.

**What you'll see in the console:**
```
[IMU-1 @ 0x28]  Roll:   -3.75°   Pitch:  177.56°   Yaw:  274.31°   (Cal S:3 G:3 A:0 M:3)
  -> IMU-1 status: STABLE
[IMU-2 @ 0x29]  Roll:    2.10°   Pitch:   45.03°   Yaw:  118.92°   (Cal S:0 G:1 A:0 M:0)
  -> IMU-2 status: UNSTABLE (fluctuating)
```

**Common cause of `UNSTABLE`, especially on Yaw specifically**: the
magnetometer hasn't calibrated yet (`Cal ... M:0`). Rotating the sensor
through a figure-8 motion, then holding it briefly in a few different
tilted orientations, is what raises magnetometer calibration — see
`BNO055_Wiring_Guide.md` for the full calibration procedure and
troubleshooting table.

**Design notes:**
- This is purely additive — nothing in `BNO055Sensor` or the original
  read/print/log logic was modified to add it.
- Stability is tracked per-sensor-name in a module-level dictionary
  (`_last_readings_for_stability`), independent of the calibration
  tracking already inside `BNO055Sensor`.
- The stability check runs every cycle (not just when printing), so the
  "previous reading" used for comparison always reflects the true
  previous cycle rather than the previous *printed* one.

---

## 6. CSV log format

Written to `logs/imu_log_<timestamp>.csv` by default (a fresh file per
run). Columns:

| Column | Meaning |
|---|---|
| `timestamp` | ISO 8601 timestamp (millisecond precision) of this reading |
| `sensor_name` | `IMU-1` or `IMU-2` |
| `address` | I2C address as hex string (e.g. `0x28`) |
| `roll_deg`, `pitch_deg`, `yaw_deg` | Orientation in degrees |
| `cal_system`, `cal_gyro`, `cal_accel`, `cal_mag` | Calibration status, 0–3 each |

Note: the stability status is **not** currently written to this CSV —
it's console-only. (The companion web dashboard, below, computes its own
stability independently from this same CSV, using the last two logged
rows for each sensor.)

---

## 7. Companion: web dashboard

`imu_web_dashboard.py` is a **separate script** that displays this same
data in a browser instead of the terminal — useful since SSH terminals
can be hard to read live, especially over a laggy connection.

- It only **reads** the CSV file this script writes — it never imports
  or talks to `V3_two_sensor_IMU_code.py` directly, so running,
  stopping, or crashing the dashboard has zero effect on the sensor
  script.
- It shows the same Roll/Pitch/Yaw/calibration data, plus its own
  independently-computed **STABLE / UNSTABLE** badge and a
  **live/STALE** indicator (stale = no new CSV row for that sensor in
  the last few seconds, meaning the main script likely stopped or that
  sensor disconnected).

**To run both together:**
```bash
# Terminal 1 — unchanged:
python3 V3_two_sensor_IMU_code.py

# Terminal 2:
python3 imu_web_dashboard.py
```
Then open `http://<pi-ip-address>:5000` from a phone or laptop browser
on the same network. Find the Pi's IP with `hostname -I`.

---

## 8. Known limitations

- Stability and calibration status are **not the same signal** and can
  disagree briefly — e.g. right after picking the sensor up to
  calibrate it, it will correctly show `UNSTABLE` even as calibration
  numbers are climbing, since it's genuinely moving at that moment.
- The stability check has no memory beyond one previous reading — it
  can't distinguish "briefly unstable due to one noisy sample" from
  "genuinely and persistently unstable." For that, watch the indicator
  over several consecutive cycles rather than a single one.
- `STABILITY_THRESHOLD_DEG` is a single fixed value for all three axes
  (Roll, Pitch, Yaw). Yaw is inherently noisier pre-calibration than
  Roll/Pitch, so it's the axis most likely to trip `UNSTABLE` first —
  this is expected, not a bug.
