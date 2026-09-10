#!/usr/bin/env python3
"""
================================================================================
 Dual BNO055 IMU Reader — Roll / Pitch / Yaw (Human Readable)
================================================================================

WHAT THIS SCRIPT DOES
----------------------
Reads orientation data from ONE or TWO Bosch BNO055 9-DOF IMU sensors
connected on the same I2C bus, and prints/returns the orientation as
human-readable Roll, Pitch, and Yaw angles in degrees.

The BNO055 has an internal sensor-fusion processor, so it directly outputs
absolute orientation (no manual quaternion/DCM math required on the host).
We still show how to convert its quaternion output to Euler angles manually,
in case you ever need custom fusion or want to avoid gimbal-lock issues with
the sensor's built-in Euler output.

HARDWARE REQUIRED
------------------
  - Raspberry Pi (any model with an I2C-capable header, e.g. Raspberry Pi 5)
  - 2 x Adafruit/generic BNO055 breakout boards
  - Jumper wires
  - (Optional) External 3.3V/5V supply if powering more peripherals

WIRING / CONNECTION (see BNO055_Wiring_Guide.md for diagram + full detail)
----------------------------------------------------------------------------
  BNO055 #1 (Primary)          Raspberry Pi
  --------------------          -------------------
  VIN   ----------------------  3.3V or 5V (Pin 1 or 2 — check your board's
                                 regulator; Adafruit breakout accepts 3-5V)
  GND   ----------------------  GND (Pin 6)
  SDA   ----------------------  GPIO2 / SDA1 (Pin 3)
  SCL   ----------------------  GPIO3 / SCL1 (Pin 5)
  ADR   ----------------------  GND  -> I2C address 0x28 (default, ADR low)

  BNO055 #2 (Secondary)        Raspberry Pi
  --------------------          -------------------
  VIN   ----------------------  3.3V or 5V (shared rail with sensor #1)
  GND   ----------------------  GND (shared with sensor #1)
  SDA   ----------------------  GPIO2 / SDA1 (Pin 3)   <- SAME bus, shared
  SCL   ----------------------  GPIO3 / SCL1 (Pin 5)   <- SAME bus, shared
  ADR   ----------------------  3.3V -> I2C address 0x29 (ADR pulled HIGH)

  Both sensors share the same two I2C wires (SDA/SCL). The ADR pin is what
  gives them two different addresses (0x28 and 0x29) so the Pi can tell them
  apart on the same bus. This is the standard way to run 2 BNO055 units off
  one I2C controller without a multiplexer.

REQUIRED PYTHON LIBRARIES (install on the Raspberry Pi)
----------------------------------------------------------
  sudo pip3 install --break-system-packages \
      adafruit-circuitpython-bno055 \
      adafruit-blinka

  Also enable I2C first:
      sudo raspi-config  ->  Interface Options -> I2C -> Enable

  Verify both sensors are visible on the bus:
      i2cdetect -y 1
      (You should see devices at 0x28 and 0x29)

CSV LOGGING
------------
Every successful reading is appended to a timestamped CSV file (see
CSV_LOG_PATH below) with columns:
    timestamp, sensor_name, address, roll_deg, pitch_deg, yaw_deg,
    cal_system, cal_gyro, cal_accel, cal_mag
This gives you a permanent record you can open in Excel/Sheets or plot
later (e.g. to check drift over a test run), without changing the live
console output.

DEBUGGING NOTES (learned while building/testing this script)
----------------------------------------------------------------
- The BNO055_I2C constructor already sets NDOF_MODE by default (confirmed
  from the library source) — explicitly setting it again is redundant but
  harmless; kept here only for readability.
- sensor.euler returns (heading, roll, pitch) in that exact order — the
  register layout on the chip is Heading/Roll/Pitch, NOT Roll/Pitch/Yaw.
  Unpacking it in the wrong order silently swaps your axes.
- The library exposes sensor.calibrated (bool) directly — no need to
  re-derive calibration state from a second full read.
- I2C reads can fail transiently (loose wiring, electrical noise) even on
  a correctly-wired bus. A single OSError/RuntimeError shouldn't kill the
  whole session — retry a couple of times first.
- Reading calibration_status on every single loop cycle is wasted I2C
  traffic, since calibration state changes over seconds, not milliseconds.
================================================================================
"""

import csv
import os
import time
import math
import sys
from datetime import datetime

import board
import busio
import adafruit_bno055


# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

# I2C addresses of the two BNO055 sensors, set via the ADR pin (see wiring
# guide above). 0x28 = ADR tied to GND (default). 0x29 = ADR tied to 3.3V.
SENSOR_1_ADDRESS = 0x28
SENSOR_2_ADDRESS = 0x29

# How often to poll the sensors, in seconds.
READ_INTERVAL_S = 0.1  # 10 Hz

# Set to True if you only have ONE sensor connected and want to skip sensor 2.
SINGLE_SENSOR_MODE = False

# How many I2C read retries to attempt before giving up on a single cycle.
# I2C errors are usually transient (noise, a loose wire) rather than fatal,
# so a couple of quick retries avoids dropping data unnecessarily.
READ_RETRIES = 2
RETRY_DELAY_S = 0.01

# Calibration status changes slowly (over seconds) compared to orientation
# (which changes every cycle), so we only re-read it every N cycles instead
# of on every single loop iteration. This cuts I2C bus traffic roughly in
# half per sensor without losing any meaningful information.
CALIBRATION_READ_EVERY_N_CYCLES = 10

# I2C bus clock speed. The BNO055 datasheet supports I2C Fast Mode
# (400kHz) on the bus, but the chip uses internal clock stretching, so
# real-world read cycles still take ~0.7-1.7ms regardless of bus speed,
# and its own sensor fusion only updates at 100Hz max either way. Bumping
# this to 400000 costs nothing and helps a little on the wire time, but
# don't expect it to meaningfully raise your achievable read rate.
I2C_FREQUENCY_HZ = 400000

# How often to print to the console. Printing every cycle (10Hz here) can
# itself become the loop's bottleneck, since terminal I/O is slower than
# the I2C reads it's reporting on. Logging to CSV stays at full rate
# regardless — this only throttles what's echoed to the screen.
PRINT_EVERY_N_CYCLES = 1  # set higher (e.g. 5) to print less often

# How often to flush the CSV file to disk (in cycles). Flushing every
# cycle guarantees minimal data loss on a hard crash but adds disk I/O
# every 100ms. Flushing less often trades a little crash-safety for less
# I/O overhead — reasonable to raise if you're logging for hours.
CSV_FLUSH_EVERY_N_CYCLES = 1
CSV_LOG_DIR = "logs"
CSV_LOG_PATH = os.path.join(
    CSV_LOG_DIR, f"imu_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)
CSV_COLUMNS = [
    "timestamp", "sensor_name", "address",
    "roll_deg", "pitch_deg", "yaw_deg",
    "cal_system", "cal_gyro", "cal_accel", "cal_mag",
]

# --- ADDED: threshold used by the new sensor-stability indicator -------
# Maximum allowed change (in degrees) in Roll, Pitch, or Yaw between two
# CONSECUTIVE readings for a sensor to be considered "STABLE". A sensor
# that is uncalibrated, loose, or picking up magnetic interference will
# show larger frame-to-frame jumps than this, especially in Yaw (which
# depends on the magnetometer) — see get_stability_status() below.
STABILITY_THRESHOLD_DEG = 2.0


# --------------------------------------------------------------------------
# QUATERNION -> EULER (ROLL / PITCH / YAW) CONVERSION
# --------------------------------------------------------------------------
def quaternion_to_euler(w, x, y, z):
    """
    Convert a quaternion (w, x, y, z) into Roll, Pitch, Yaw angles in degrees.

    This is provided as a manual reference / fallback. The BNO055 also
    exposes `sensor.euler` directly (its own onboard fusion output), which
    is what this script uses by default since it's more robust to gimbal
    lock than a naive quaternion->Euler conversion. Both are shown so you
    can compare or substitute one for the other.

    Convention used: aerospace / body-frame standard
      Roll  (phi)   -> rotation about the X axis (tilt left/right)
      Pitch (theta) -> rotation about the Y axis (tilt forward/back)
      Yaw   (psi)   -> rotation about the Z axis (compass heading)
    """
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # clamp at +/-90 deg (gimbal lock)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


# --------------------------------------------------------------------------
# SENSOR WRAPPER CLASS
# --------------------------------------------------------------------------
class BNO055Sensor:
    """
    Thin wrapper around adafruit_bno055.BNO055_I2C that gives back clean,
    human-readable Roll/Pitch/Yaw plus basic health/status info.
    """

    def __init__(self, i2c_bus, address, name="IMU"):
        self.name = name
        self.address = address
        self.address_hex = hex(address)  # cached — computed once, not every read
        self._cycle_count = 0
        # Last-known calibration tuple, reused between throttled re-reads
        # (see CALIBRATION_READ_EVERY_N_CYCLES). Starts at all-zero
        # (uncalibrated) until the first real read comes in.
        self._last_calibration = (0, 0, 0, 0)
        try:
            self.sensor = adafruit_bno055.BNO055_I2C(i2c_bus, address=address)
            # NOTE: BNO055_I2C already sets NDOF_MODE by default in its own
            # constructor (confirmed from the library source) — this line
            # is redundant in practice, kept only so the intent ("we want
            # full 9-DOF fusion") is explicit in this file too.
            self.sensor.mode = adafruit_bno055.NDOF_MODE
            self.connected = True
        except (OSError, ValueError, RuntimeError) as e:
            # OSError: no device answered at this address (bad wiring).
            # RuntimeError: a device answered but its chip ID didn't match
            # BNO055 (confirmed from the library source — it raises
            # RuntimeError, not OSError, on a bad chip ID). Both mean
            # "this sensor isn't usable," so both are handled the same way
            # here instead of crashing the whole script.
            print(f"[{self.name}] ERROR: could not connect at address "
                  f"0x{address:02X} -> {e}")
            self.sensor = None
            self.connected = False

    def read_orientation(self):
        """
        Returns a dict with roll, pitch, yaw (degrees, human-readable),
        plus the calibration status of the sensor.

        Returns None if the sensor is not connected or every retry fails.

        Includes a couple of I2C-specific debugging lessons learned:
          - Retries a transient bus error a few times before giving up,
            since a single OSError on I2C is often noise/a loose wire
            rather than a real fault.
          - Only re-reads calibration_status every N cycles instead of on
            every call, since calibration changes far slower than
            orientation does. This halves I2C traffic per sensor with no
            real loss of information.
        """
        if not self.connected or self.sensor is None:
            return None

        self._cycle_count += 1
        should_read_calibration = (
            self._cycle_count == 1
            or self._cycle_count % CALIBRATION_READ_EVERY_N_CYCLES == 0
        )

        for attempt in range(READ_RETRIES + 1):
            try:
                # sensor.euler returns (heading, roll, pitch) in degrees —
                # this exact order matches the chip's register layout
                # (Heading, then Roll, then Pitch). Unpacking it in the
                # "obvious" Roll/Pitch/Yaw order silently swaps two axes.
                heading, roll, pitch = self.sensor.euler

                if heading is None or roll is None or pitch is None:
                    return None  # sensor hasn't produced a valid fusion reading yet

                if should_read_calibration:
                    # calibration_status: 0 (uncalibrated) - 3 (fully
                    # calibrated) for (system, gyro, accelerometer,
                    # magnetometer) — same order the library returns.
                    self._last_calibration = self.sensor.calibration_status

                sys_cal, gyro_cal, accel_cal, mag_cal = self._last_calibration

                return {
                    "name": self.name,
                    "address": self.address_hex,
                    "roll_deg": round(roll, 2),
                    "pitch_deg": round(pitch, 2),
                    "yaw_deg": round(heading, 2),
                    "calibration": {
                        "system": sys_cal,
                        "gyro": gyro_cal,
                        "accel": accel_cal,
                        "mag": mag_cal,
                    },
                }
            except (OSError, RuntimeError) as e:
                if attempt == READ_RETRIES:
                    print(f"[{self.name}] Read failed after "
                          f"{READ_RETRIES} retries: {e}")
                    return None
                time.sleep(RETRY_DELAY_S)

        return None  # unreachable, but keeps linters happy

    def is_calibrated(self):
        """
        Returns True once the sensor reports full calibration.

        Uses the library's own `sensor.calibrated` property directly
        (a single cheap register read) instead of re-deriving it from a
        full read_orientation() call, which would waste an extra I2C
        transaction just to check one boolean.
        """
        if not self.connected or self.sensor is None:
            return False
        try:
            return bool(self.sensor.calibrated)
        except (OSError, RuntimeError):
            return False


# --------------------------------------------------------------------------
# ADDED: SENSOR STABILITY INDICATOR
# This whole section is new. It does not modify BNO055Sensor above in any
# way — it works entirely from the reading dicts that read_orientation()
# already returns, by comparing the current reading to the previous one.
# --------------------------------------------------------------------------

# ADDED: remembers each sensor's most recent reading (keyed by sensor
# name) so the next reading can be compared against it. Kept outside the
# class on purpose, so BNO055Sensor itself doesn't need any changes.
_last_readings_for_stability = {}


def get_stability_status(sensor_name, current_reading):
    """
    ADDED FUNCTION: reports whether a sensor's orientation output is
    currently STABLE or UNSTABLE, by comparing the current reading to the
    previous reading from that same sensor.

    This is a different, more direct check than the sensor's own
    calibration numbers (already shown by format_reading()) — those
    report the sensor's internal calibration STATE, while this reports
    the actual frame-to-frame BEHAVIOR of the values it's producing.
    An uncalibrated sensor, magnetic interference, a loose I2C
    connection, or electrical noise all tend to show up here as
    "UNSTABLE" even before/without looking at the calibration numbers.

    Returns one of:
      "N/A (no data)"          - this cycle's read failed, nothing to
                                  compare
      "N/A (first reading)"    - no previous reading yet for this sensor
      "STABLE"                 - Roll, Pitch, and Yaw all changed less
                                  than STABILITY_THRESHOLD_DEG since the
                                  last reading
      "UNSTABLE (fluctuating)" - at least one of Roll/Pitch/Yaw changed
                                  by more than STABILITY_THRESHOLD_DEG
    """
    # ADDED: no reading this cycle -> nothing to evaluate.
    if current_reading is None:
        return "N/A (no data)"

    # ADDED: look up this sensor's last reading (None if this is the
    # very first one we've seen for it).
    previous_reading = _last_readings_for_stability.get(sensor_name)

    # ADDED: always remember the latest reading for the NEXT comparison,
    # including on this very first call.
    _last_readings_for_stability[sensor_name] = current_reading

    # ADDED: nothing to compare against yet on the first ever reading.
    if previous_reading is None:
        return "N/A (first reading)"

    # ADDED: how much Roll and Pitch changed since the last reading.
    delta_roll = abs(current_reading["roll_deg"] - previous_reading["roll_deg"])
    delta_pitch = abs(current_reading["pitch_deg"] - previous_reading["pitch_deg"])

    # ADDED: Yaw wraps around at 0/360 degrees (e.g. 359 -> 1 is really
    # only a 2-degree change, not a 358-degree jump), so the raw
    # difference is corrected for that wraparound before comparing it
    # against the threshold — otherwise a stable sensor sitting right at
    # the 0/360 boundary would be wrongly flagged as UNSTABLE.
    raw_delta_yaw = abs(current_reading["yaw_deg"] - previous_reading["yaw_deg"])
    delta_yaw = min(raw_delta_yaw, 360 - raw_delta_yaw)

    # ADDED: if ANY of the three axes jumped more than the threshold,
    # call it unstable; otherwise it's stable.
    if max(delta_roll, delta_pitch, delta_yaw) > STABILITY_THRESHOLD_DEG:
        return "UNSTABLE (fluctuating)"
    return "STABLE"


# --------------------------------------------------------------------------
# HUMAN-READABLE PRINTING
# --------------------------------------------------------------------------
def format_reading(data):
    """Turn a sensor reading dict into a clean one-line human-readable string."""
    if data is None:
        return "No data (sensor not connected or not ready)"

    cal = data["calibration"]
    return (
        f"[{data['name']} @ {data['address']}]  "
        f"Roll: {data['roll_deg']:7.2f}°   "
        f"Pitch: {data['pitch_deg']:7.2f}°   "
        f"Yaw: {data['yaw_deg']:7.2f}°   "
        f"(Cal S:{cal['system']} G:{cal['gyro']} A:{cal['accel']} M:{cal['mag']})"
    )


# --------------------------------------------------------------------------
# CSV LOGGING
# --------------------------------------------------------------------------
def init_csv_log(path):
    """
    Creates the log directory and CSV file (with header row) if needed.
    Returns the open file handle and a csv.writer bound to it.

    Opened once at startup and kept open for the whole run — repeatedly
    opening/closing the file on every reading would add unnecessary disk
    I/O to a loop that's already doing I2C I/O every cycle.

    NOTE: a linter may suggest a `with open(...) as f:` block here.
    That pattern doesn't fit this case — the file needs to stay open for
    the entire program run, not just for one operation, so the caller
    (main()) is responsible for closing it in a `finally` block instead.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    file_exists = os.path.isfile(path)

    f = open(path, mode="a", newline="", encoding="utf-8")
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(CSV_COLUMNS)
        f.flush()

    return f, writer


def log_reading_to_csv(writer, data):
    """Appends one sensor reading (dict from read_orientation) as a CSV row."""
    if data is None:
        return
    cal = data["calibration"]
    writer.writerow([
        datetime.now().isoformat(timespec="milliseconds"),
        data["name"],
        data["address"],
        data["roll_deg"],
        data["pitch_deg"],
        data["yaw_deg"],
        cal["system"],
        cal["gyro"],
        cal["accel"],
        cal["mag"],
    ])


# --------------------------------------------------------------------------
# MAIN LOOP  (split into focused helpers — see main() at the bottom, which
# just calls these in order. Splitting it up this way keeps each function
# doing one job, which is easier to read/learn from than one long main().)
# --------------------------------------------------------------------------
def validate_config():
    """
    Guards against modulo-by-zero if someone sets one of the throttling
    constants to 0 thinking it means "disable" — that would crash the
    loop on the very first cycle instead. Minimum valid value is 1
    ("do it every cycle"). Exits the program with a clear message rather
    than letting a confusing ZeroDivisionError surface later.
    """
    for name, value in (
        ("CALIBRATION_READ_EVERY_N_CYCLES", CALIBRATION_READ_EVERY_N_CYCLES),
        ("PRINT_EVERY_N_CYCLES", PRINT_EVERY_N_CYCLES),
        ("CSV_FLUSH_EVERY_N_CYCLES", CSV_FLUSH_EVERY_N_CYCLES),
    ):
        if value < 1:
            print(f"ERROR: {name} must be >= 1 (got {value}). "
                  f"Use 1 for 'every cycle', not 0.")
            sys.exit(1)


def setup_sensors():
    """
    Opens the shared I2C bus and connects to one or both BNO055 sensors.
    Exits the program if neither sensor is reachable, since there'd be
    nothing left for the read loop to do.

    Returns (i2c, imu1, imu2) — imu2 is None in SINGLE_SENSOR_MODE.
    """
    # frequency=I2C_FREQUENCY_HZ requests Fast Mode (400kHz) instead of
    # the busio default of 100kHz — see the note above CONFIGURATION for
    # why this helps only marginally on the BNO055 specifically.
    i2c = busio.I2C(board.SCL, board.SDA, frequency=I2C_FREQUENCY_HZ)

    imu1 = BNO055Sensor(i2c, SENSOR_1_ADDRESS, name="IMU-1")

    imu2 = None
    if not SINGLE_SENSOR_MODE:
        imu2 = BNO055Sensor(i2c, SENSOR_2_ADDRESS, name="IMU-2")

    if not imu1.connected and (imu2 is None or not imu2.connected):
        print("No BNO055 sensors detected. Check wiring and run "
              "'i2cdetect -y 1' to confirm addresses 0x28 / 0x29 are present.")
        sys.exit(1)

    return i2c, imu1, imu2


def run_read_loop(imu1, imu2, csv_file, csv_writer):
    """
    The live loop: reads both sensors, prints (throttled), logs to CSV
    (throttled flush), and holds a fixed sample rate. Runs until Ctrl+C.
    """
    cycle = 0
    try:
        while True:
            # Fixed-rate scheduling: anchor to the time BEFORE this
            # cycle's work starts, then sleep only the remaining time.
            # A plain time.sleep(READ_INTERVAL_S) after the reads drifts
            # whenever a retry adds extra delay — this keeps the actual
            # sample rate close to READ_INTERVAL_S over a long run instead
            # of slowly falling behind.
            cycle_start = time.monotonic()
            cycle += 1
            should_print = cycle % PRINT_EVERY_N_CYCLES == 0

            reading1 = imu1.read_orientation()
            # ADDED: check IMU-1's stability every cycle (not just when
            # printing), so the "previous reading" used for comparison
            # stays up to date even on cycles where nothing is displayed.
            stability1 = get_stability_status("IMU-1", reading1)
            if should_print:
                print(format_reading(reading1))
                # ADDED: show IMU-1's stability right under its reading.
                print(f"  -> IMU-1 status: {stability1}")
            log_reading_to_csv(csv_writer, reading1)

            if imu2 is not None:
                reading2 = imu2.read_orientation()
                # ADDED: same stability check for IMU-2.
                stability2 = get_stability_status("IMU-2", reading2)
                if should_print:
                    print(format_reading(reading2))
                    # ADDED: show IMU-2's stability right under its reading.
                    print(f"  -> IMU-2 status: {stability2}")
                log_reading_to_csv(csv_writer, reading2)

            if cycle % CSV_FLUSH_EVERY_N_CYCLES == 0:
                csv_file.flush()  # ensure rows are on disk periodically,
                                   # even if the script is killed rather
                                   # than exited cleanly

            if should_print:
                print("-" * 70)

            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0.0, READ_INTERVAL_S - elapsed))

    except KeyboardInterrupt:
        print("\nStopped by user.")


def main():
    """Wires the helpers above together: validate -> connect -> run -> clean up."""
    validate_config()
    i2c, imu1, imu2 = setup_sensors()

    csv_file, csv_writer = init_csv_log(CSV_LOG_PATH)
    print(f"Logging readings to: {CSV_LOG_PATH}")
    print("Starting IMU read loop. Press Ctrl+C to stop.\n")

    try:
        run_read_loop(imu1, imu2, csv_file, csv_writer)
    finally:
        csv_file.flush()
        csv_file.close()
        print(f"CSV log saved: {CSV_LOG_PATH}")
        # Release the I2C peripheral. On Raspberry Pi + Blinka, skipping
        # this can leave the bus in a state where the NEXT run of this
        # script (or another script) fails to open it again without a
        # reboot — a known Blinka gotcha, not a BNO055-specific one.
        try:
            i2c.deinit()
        except (AttributeError, RuntimeError):
            pass  # some Blinka backends don't implement deinit(); safe to ignore


if __name__ == "__main__":
    main()
