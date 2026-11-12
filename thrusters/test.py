import time

import board
import busio
from adafruit_pca9685 import PCA9685

# Create the I2C bus and PCA9685 at its default address.
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

# ESC control pulse settings, in microseconds.
NEUTRAL_US = 1500
FORWARD_US = 1600

def send_esc_pulse(channel, pulse_us):
    # Convert the pulse length to the 16-bit duty cycle used by the library.
    duty = round(pulse_us * pca.frequency * 65535 / 1_000_000)
    pca.channels[channel].duty_cycle = duty

try:
    # Give the ESC neutral while it starts.
    send_esc_pulse(0, NEUTRAL_US)
    time.sleep(3)

    # Run the motor forward briefly, then return to neutral.
    send_esc_pulse(0, FORWARD_US)
    time.sleep(2)
    send_esc_pulse(0, NEUTRAL_US)

finally:
    # Leave the ESC at neutral if the program exits.
    send_esc_pulse(0, NEUTRAL_US)
