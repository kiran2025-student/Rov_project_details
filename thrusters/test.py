import time
from motor_control import MotorController

motors = MotorController(i2c)  # Sends neutral to all configured ESCs
time.sleep(3)                   # Allow ESCs to arm

motors.set_motor("motor_1", 0.20)  # Forward, low test speed
motors.set_motor("motor_2", -0.20) # Reverse, low test speed
motors.stop_motor("motor_1")       # Stop only motor 1
motors.stop_all()                  # Stop all motors
