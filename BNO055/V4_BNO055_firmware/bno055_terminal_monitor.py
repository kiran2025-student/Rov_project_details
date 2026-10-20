#!/usr/bin/env python3
"""Live two-sensor BNO055 monitor for a Raspberry Pi terminal."""

import time

import board
import adafruit_bno055
from bno055_csv_logger import BNO055CSVLogger
from bno055_human_readable import describe_orientation


def fmt(vector, unit=""):
    """Format a tuple of sensor values, handling unavailable readings."""
    if vector is None:
        return "unavailable"
    return "(" + ", ".join(f"{value:8.3f}" for value in vector) + f") {unit}"


def main():
    # On Raspberry Pi, board.I2C() selects the primary I2C bus (GPIO 2/3).
    i2c = board.I2C()

    # Set the address-selection jumper/pin differently on each breakout.
    sensor1 = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
    sensor2 = adafruit_bno055.BNO055_I2C(i2c, address=0x29)
    sensors = (("BNO055 #1 (0x28)", sensor1), ("BNO055 #2 (0x29)", sensor2))

    csv_logger = BNO055CSVLogger()
    print(f"Two BNO055 live monitor — Ctrl+C to quit | CSV: {csv_logger.path.resolve()}")
    try:
        while True:
            timestamp = csv_logger.timestamp_utc()
            # Clear and redraw the same terminal area for a serial-monitor feel.
            print("\033[2J\033[H", end="")
            print("TWO BNO055 LIVE MONITOR                         Ctrl+C to quit")
            print(f"CSV: {csv_logger.path.name} | UTC: {timestamp}")
            print("=" * 76)
            for label, sensor in sensors:
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
                address = 0x28 if label.endswith("#1 (0x28)") else 0x29
                csv_logger.write_sensor(timestamp, label, address, sensor)
            csv_logger.flush()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    finally:
        csv_logger.close()
        i2c.deinit()


if __name__ == "__main__":
    main()
