"""Human-readable orientation labels for BNO055 monitor output."""


def describe_orientation(sensor):
    """Return plain-language tilt, turn, and calibration descriptions.

    The BNO055 Euler tuple is heading, roll, pitch (degrees). The labels assume
    the sensor's axes are mounted in the expected orientation; adjust the
    thresholds or axis interpretation for a different mounting arrangement.
    """
    euler = sensor.euler
    if euler is None:
        return "Orientation: unavailable", "Motion: unavailable", "Calibration: unavailable"

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
        turn = "Facing: near the 0° reference direction"
    elif heading < 180.0:
        turn = f"Facing: turned right about {heading:.0f}° from the 0° reference"
    else:
        turn = f"Facing: turned left about {360.0 - heading:.0f}° from the 0° reference"

    system, gyro, accelerometer, magnetometer = sensor.calibration_status
    if system == 3 and gyro == 3 and accelerometer == 3 and magnetometer == 3:
        calibration = "Calibration: fully calibrated"
    else:
        calibration = (
            "Calibration (0=low, 3=full): "
            f"system {system}, gyro {gyro}, accel {accelerometer}, mag {magnetometer}"
        )

    return tilt, turn, calibration

