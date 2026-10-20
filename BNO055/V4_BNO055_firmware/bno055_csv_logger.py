"""CSV formatting and logging helpers for the BNO055 monitor."""

import csv
from datetime import datetime, timezone
from pathlib import Path


FIELDS = (
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
        self._writer = csv.DictWriter(self._file, fieldnames=FIELDS)
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
