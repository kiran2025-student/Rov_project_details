#!/usr/bin/env python3
"""Standalone V4 dual-BNO055 monitor, CSV logger, and readable display.

Run this one file from the Raspberry Pi. It reads sensors at I2C addresses
0x28 and 0x29, prints live measurements and human-readable orientation labels,
and appends timestamped samples to bno055_imu_data.csv.
"""

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import board
import adafruit_bno055


CSV_FIELDS = (
    "timestamp_utc", "sensor", "i2c_address", "temperature_c",
    "heading_deg", "roll_deg", "pitch_deg",
    "quaternion_w", "quaternion_x", "quaternion_y", "quaternion_z",
    "accel_x_m_s2", "accel_y_m_s2", "accel_z_m_s2",
    "linear_accel_x_m_s2", "linear_accel_y_m_s2", "linear_accel_z_m_s2",
    "gravity_x_m_s2", "gravity_y_m_s2", "gravity_z_m_s2",
    "gyro_x_deg_s", "gyro_y_deg_s", "gyro_z_deg_s",
    "magnetic_x_uT", "magnetic_y_uT", "magnetic_z_uT",
    "calibration_system", "calibration_gyroscope",
    "calibration_accelerometer", "calibration_magnetometer",
)


class BNO055CSVLogger:
    """Append timestamped sensor rows to a CSV file Excel can open."""

    def __init__(self, path="bno055_imu_data.csv"):
        self.path = Path(path)
        has_data = self.path.exists() and self.path.stat().st_size > 0
        self._file = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS)
        if not has_data:
            self._writer.writeheader()
            self._file.flush()

    @staticmethod
    def timestamp_utc():
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def write_sensor(self, timestamp, label, address, sensor):
        euler = sensor.euler or (None, None, None)
        quaternion = sensor.quaternion or (None, None, None, None)
        acceleration = sensor.acceleration or (None, None, None)
        linear_acceleration = sensor.linear_acceleration or (None, None, None)
        gravity = sensor.gravity or (None, None, None)
        gyro = sensor.gyro or (None, None, None)
        magnetic = sensor.magnetic or (None, None, None)
        calibration = sensor.calibration_status
        self._writer.writerow({
            "timestamp_utc": timestamp,
            "sensor": label,
            "i2c_address": f"0x{address:02X}",
            "temperature_c": sensor.temperature,
            "heading_deg": euler[0], "roll_deg": euler[1], "pitch_deg": euler[2],
            "quaternion_w": quaternion[0], "quaternion_x": quaternion[1],
            "quaternion_y": quaternion[2], "quaternion_z": quaternion[3],
            **{f"accel_{axis}_m_s2": value for axis, value in zip("xyz", acceleration)},
            **{f"linear_accel_{axis}_m_s2": value for axis, value in zip("xyz", linear_acceleration)},
            **{f"gravity_{axis}_m_s2": value for axis, value in zip("xyz", gravity)},
            **{f"gyro_{axis}_deg_s": value for axis, value in zip("xyz", gyro)},
            **{f"magnetic_{axis}_uT": value for axis, value in zip("xyz", magnetic)},
            "calibration_system": calibration[0],
            "calibration_gyroscope": calibration[1],
            "calibration_accelerometer": calibration[2],
            "calibration_magnetometer": calibration[3],
        })

    def flush(self):
        self._file.flush()

    def close(self):
        self._file.close()


def describe_orientation(sensor):
    """Return plain-language tilt, turn, and calibration descriptions.

    The BNO055 Euler tuple is heading, roll, pitch (degrees). The labels assume
    the sensor's axes are mounted in the expected orientation; adjust these
    thresholds or axis interpretation for a different mounting arrangement.
    """
    euler = sensor.euler
    if euler is None:
        return (
            "Body position: unavailable",
            "Facing: unavailable",
            "Calibration: unavailable",
        )

    heading, roll, pitch = euler
    tilt_threshold = 10.0
    turn_threshold = 15.0

    if abs(roll) < tilt_threshold and abs(pitch) < tilt_threshold:
        tilt = "Body position: mostly upright / level"
    elif abs(pitch) >= abs(roll):
        tilt = "Body position: leaning forward" if pitch > 0 else "Body position: leaning backward"
    else:
        tilt = "Body position: leaning right" if roll > 0 else "Body position: leaning left"

    if abs(heading) < turn_threshold or abs(heading - 360.0) < turn_threshold:
        turn = "Facing: near the 0-degree reference direction"
    elif heading < 180.0:
        turn = f"Facing: turned right about {heading:.0f} degrees from the 0-degree reference"
    else:
        turn = f"Facing: turned left about {360.0 - heading:.0f} degrees from the 0-degree reference"

    system, gyro, accelerometer, magnetometer = sensor.calibration_status
    if system == gyro == accelerometer == magnetometer == 3:
        calibration_text = "Calibration: fully calibrated"
    else:
        calibration_text = (
            "Calibration (0=low, 3=full): "
            f"system {system}, gyro {gyro}, accel {accelerometer}, mag {magnetometer}"
        )
    return tilt, turn, calibration_text


def fmt(vector, unit=""):
    """Format sensor values for readable terminal output."""
    if vector is None:
        return "unavailable"
    return "(" + ", ".join(f"{value:8.3f}" for value in vector) + f") {unit}"


def main():
    # On Raspberry Pi, board.I2C() selects the primary I2C bus (GPIO 2/3).
    i2c = board.I2C()
    csv_logger = None
    try:
        # Set the address-selection jumper/pin differently on each breakout.
        sensor1 = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
        sensor2 = adafruit_bno055.BNO055_I2C(i2c, address=0x29)
        sensors = (
            ("BNO055 #1 (0x28)", 0x28, sensor1),
            ("BNO055 #2 (0x29)", 0x29, sensor2),
        )

        csv_logger = BNO055CSVLogger()
        print(
            "Two BNO055 live monitor — Ctrl+C to quit | "
            f"CSV: {csv_logger.path.resolve()}"
        )
        while True:
            timestamp = csv_logger.timestamp_utc()
            # Clear and redraw the same terminal area for a serial-monitor feel.
            print("\033[2J\033[H", end="")
            print("TWO BNO055 LIVE MONITOR                         Ctrl+C to quit")
            print(f"CSV: {csv_logger.path.name} | UTC: {timestamp}")
            print("=" * 76)
            for label, address, sensor in sensors:
                print(f"\n{label}")
                print("-" * 76)
                print(f"Temperature : {sensor.temperature} °C")
                print(f"Euler angles: {fmt(sensor.euler, 'degrees (heading, roll, pitch)')}")
                for description in describe_orientation(sensor):
                    print(description)
                print(f"Quaternion  : {fmt(sensor.quaternion)}")
                print(f"Accel       : {fmt(sensor.acceleration, 'm/s²')}")
                print(f"Linear accel: {fmt(sensor.linear_acceleration, 'm/s²')}")
                print(f"Gravity     : {fmt(sensor.gravity, 'm/s²')}")
                print(f"Gyroscope   : {fmt(sensor.gyro, 'degrees/s')}")
                print(f"Magnetometer: {fmt(sensor.magnetic, 'µT')}")
                print(f"Calibration : {sensor.calibration_status}")
                csv_logger.write_sensor(timestamp, label, address, sensor)
            csv_logger.flush()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    finally:
        if csv_logger is not None:
            csv_logger.close()
        i2c.deinit()


if __name__ == "__main__":
    main()
