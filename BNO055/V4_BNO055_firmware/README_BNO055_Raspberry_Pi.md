# Two BNO055 sensors in a Raspberry Pi terminal monitor

This starter uses Adafruit's [CircuitPython BNO055 Python driver](https://github.com/adafruit/Adafruit_CircuitPython_BNO055) through Blinka. The Pi reads two BNO055 sensors over one I²C bus, displays their live readings in its terminal, and appends timestamped samples to a CSV file that Excel can open; this is not firmware flashed onto the BNO055.

## Wiring (I²C)

With the Raspberry Pi powered off, connect:

| Raspberry Pi | Both BNO055 breakouts |
| --- | --- |
| 3.3 V | VIN/VCC (check each breakout's labeling) |
| GND | GND |
| GPIO 2 / SDA (pin 3) | SDA on both sensors |
| GPIO 3 / SCL (pin 5) | SCL on both sensors |

Connect both sensors in parallel to the same SDA, SCL, power, and ground lines. Use a 3.3 V I²C logic connection. Enable I²C in `raspi-config` (Interface Options → I2C), then reboot.

The two sensors must have different I²C addresses. Set one breakout to `0x28` and the other to `0x29` using its address-select jumper or pin; consult that breakout's labeling/documentation for how to select the alternate address. Run `i2cdetect -y 1`: both `28` and `29` should appear. If both boards are fixed at the same address, use an I²C multiplexer such as a TCA9548A and modify the program to select a channel for each sensor.

## Install and run

On the Pi, install the library and copy all three Python files—`bno055_terminal_monitor.py`, `bno055_csv_logger.py`, and `bno055_human_readable.py`—into the same folder. Run only `bno055_terminal_monitor.py`; it imports the other two helpers, displays raw readings and plain-language orientation/calibration labels, and logs the CSV. On current Raspberry Pi OS releases, use a virtual environment:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip i2c-tools
mkdir -p ~/bno055-monitor
cd ~/bno055-monitor
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install adafruit-circuitpython-bno055
```

Copy the script into `~/bno055-monitor`, then run:

```bash
python bno055_terminal_monitor.py
```

Press Ctrl+C to stop. The terminal display refreshes about five times per second. It shows raw angles plus easy-to-read body tilt and heading descriptions. These labels assume the sensor is mounted with its axes in the expected orientation; adjust the helper's axis interpretation if your mounting differs. The program creates `bno055_imu_data.csv` in the directory where it is run, with one row per sensor and a shared UTC timestamp for each refresh. It logs temperature, Euler orientation, quaternion, acceleration, linear acceleration, gravity, gyroscope, magnetometer, and calibration status. Excel can open the CSV directly. New readings append to an existing file. Keep all three Python files together in the same directory. The script expects sensor #1 at `0x28` and sensor #2 at `0x29`; change those `address=` values in the script if your wiring uses the reverse assignment.

## If I²C reads fail

Check the wiring, I²C enablement, and that both `0x28` and `0x29` appear in `i2cdetect -y 1`. Adafruit notes that BNO055 I²C can require a current Raspberry Pi OS/firmware and reduced I²C clock speed because of clock stretching. Follow [Adafruit's Raspberry Pi clock-stretching setup](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/i2c) if either sensor is detected inconsistently.

The monitor is set up for I²C. If your breakouts are configured for UART instead, the wiring, Pi serial-port setup, and Python initialization need to be changed.
