# BNO055 Dual-IMU Connection Guide (I2C)

This document explains how to physically wire **two BNO055 IMU sensors** to
a Raspberry Pi (or any I2C host, e.g. Arduino/ESP32) on a **single shared
I2C bus**, and how the accompanying `bno055_dual_imu.py` script reads
Roll / Pitch / Yaw from both of them.

---

## 1. Why two sensors can share one I2C bus

I2C allows multiple devices on the same two wires (SDA/SCL) as long as each
device has a **unique 7-bit address**. The BNO055 supports exactly two
addresses, selected by its `ADR` (address) pin:

| ADR pin state | I2C Address |
|----------------|-------------|
| LOW (tied to GND) | `0x28` (default) |
| HIGH (tied to 3.3V) | `0x29` |

By tying one sensor's `ADR` pin to GND and the other's to 3.3V, both can sit
on the same SDA/SCL lines without conflicting.

---

## 2. Pinout Reference (BNO055 breakout, e.g. Adafruit #4646)

| BNO055 Pin | Function |
|------------|----------|
| VIN | Power input (3.3–5V depending on board's onboard regulator) |
| 3Vo | 3.3V output from onboard regulator (not used here) |
| GND | Ground |
| SDA | I2C data line |
| SCL | I2C clock line |
| RST | Reset (active low) — optional, can leave unconnected |
| INT | Interrupt output — optional, not used in this script |
| PS0 / PS1 | Protocol select — leave floating/GND for I2C mode (default) |
| ADR | Address select — GND = 0x28, 3.3V = 0x29 |

---

## 3. Wiring Diagram (Raspberry Pi 40-pin header)

```
                        Raspberry Pi
                    ┌───────────────────┐
        3.3V  Pin1  │ ●                 │
                     │                   │
   SDA1  Pin3 (GPIO2)│ ●─────────────┬───┼──── SDA ──── BNO055 #1
                     │               │   │              │
   SCL1  Pin5 (GPIO3)│ ●───────────┬─┼───┼──── SCL ──── BNO055 #1
                     │             │ │   │              │
         GND  Pin6   │ ●───────┬───┼─┼───┼──── GND ──── BNO055 #1
                     │         │   │ │   │              │
                     │         │   │ │   │        ADR ── GND (0x28)
                     │         │   │ │   │              │
                     │         │   └─┼───┼──── SDA ──── BNO055 #2
                     │         │     │   │              │
                     │         └─────┼───┼──── SCL ──── BNO055 #2  [same
                     │               │   │              │           bus]
                     │               │   │        GND ── (shared with above)
                     │               │   │              │
                     │               └───┼──── VIN ──── BNO055 #2
                     │                   │        ADR ── 3.3V (0x29)
                     └───────────────────┘
```

### Summary table

| Signal | Raspberry Pi Pin | BNO055 #1 | BNO055 #2 |
|--------|------------------|-----------|-----------|
| Power (VIN) | Pin 1 (3.3V) or Pin 2 (5V) | VIN | VIN (shared rail) |
| Ground | Pin 6 (GND) | GND | GND (shared) |
| I2C Data | Pin 3 (GPIO2 / SDA1) | SDA | SDA (shared bus) |
| I2C Clock | Pin 5 (GPIO3 / SCL1) | SCL | SCL (shared bus) |
| Address select | — | ADR → GND (addr `0x28`) | ADR → 3.3V (addr `0x29`) |

> **Note:** Both sensors connect to the *same* SDA and SCL pins on the Pi —
> you are not using two separate I2C buses, just wiring in parallel. This is
> the standard multi-device I2C topology.

> **Pull-up resistors:** The Raspberry Pi's I2C pins have onboard pull-ups
> enabled by default, so no external resistors are normally required for two
> short-wired BNO055 boards. If you see intermittent bus errors over longer
> wire runs, add 4.7kΩ pull-ups from SDA and SCL to 3.3V.

---

## 4. Software Setup

```bash
# 1. Enable I2C on the Raspberry Pi
sudo raspi-config
#   -> Interface Options -> I2C -> Enable -> Reboot

# 2. Install required Python libraries
sudo pip3 install --break-system-packages adafruit-circuitpython-bno055 adafruit-blinka

# 3. Confirm both sensors are detected on the bus
i2cdetect -y 1
#   Expect to see entries at 0x28 and 0x29 in the grid output
```

---

## 5. Running the script

```bash
python3 bno055_dual_imu.py
```

Example output:
```
[IMU-1 @ 0x28]  Roll:    1.25°   Pitch:   -0.42°   Yaw:  183.60°   (Cal S:3 G:3 A:3 M:2)
[IMU-2 @ 0x29]  Roll:   -3.10°   Pitch:    2.05°   Yaw:   45.90°   (Cal S:2 G:3 A:2 M:1)
----------------------------------------------------------------------
```

- **Roll** — rotation about the X axis (tilting side to side)
- **Pitch** — rotation about the Y axis (tilting forward/back)
- **Yaw** — rotation about the Z axis (compass heading, 0–360°)
- **Calibration (S/G/A/M)** — System/Gyroscope/Accelerometer/Magnetometer,
  each 0 (uncalibrated) to 3 (fully calibrated). For reliable Yaw readings,
  move the sensor in a figure-8 pattern until the Magnetometer value reaches 3.

---

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `i2cdetect` shows nothing | Wiring or I2C not enabled | Recheck SDA/SCL, re-run `raspi-config` |
| Only one address shows (e.g. only `0x28`) | Second sensor's ADR pin not tied HIGH, or not powered | Confirm ADR → 3.3V, confirm VIN has power |
| Yaw drifts / jumps randomly | Magnetometer near motors, magnets, or metal | Mount IMU away from motors/thrusters and ferrous parts, recalibrate |
| `OSError: [Errno 121] Remote I/O error` | Loose wiring or bus contention | Reseat connections, add pull-up resistors, shorten wires |
| Pitch stuck at ±90° | Gimbal lock in manual quaternion math | Use the built-in `sensor.euler` (already default in the script) instead of the manual `quaternion_to_euler()` fallback |
