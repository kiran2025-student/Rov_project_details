# Dual BNO055 Orientation System — Raspberry Pi 5

This project uses two BNO055 IMU sensors with a Raspberry Pi 5 through the I²C interface.

The system reads:
- Heading
- Roll
- Pitch
- Compass direction
- Roll status
- Pitch status

The two BNO055 sensors use different I²C addresses:

| Sensor | I²C Address | ADR Connection |
|---|---:|---|
| BNO055 Sensor 1 | `0x28` | ADR → GND |
| BNO055 Sensor 2 | `0x29` | ADR → 3.3V |

---

## 1. Hardware Required

- Raspberry Pi 5
- 2 × BNO055 IMU sensors
- Jumper wires
- Raspberry Pi OS
- Raspberry Pi 5 power supply

---

## 2. Raspberry Pi 5 I²C Pins

| Raspberry Pi 5 | Physical Pin | Function |
|---|---:|---|
| 3.3V | Pin 1 | 3.3V Power |
| GND | Pin 6 | Ground |
| GPIO 2 | Pin 3 | SDA |
| GPIO 3 | Pin 5 | SCL |

---

## 3. BNO055 Sensor 1 — Address `0x28`

| BNO055 Sensor 1 | Raspberry Pi 5 |
|---|---|
| VCC/VIN* | 3.3V / appropriate supply |
| GND | GND |
| SDA | GPIO 2 / Pin 3 |
| SCL | GPIO 3 / Pin 5 |
| ADR | GND |

ADR connected to GND sets:

```text
BNO055 Sensor 1 = 0x28
```

---

## 4. BNO055 Sensor 2 — Address `0x29`

| BNO055 Sensor 2 | Raspberry Pi 5 |
|---|---|
| VCC/VIN* | 3.3V / appropriate supply |
| GND | GND |
| SDA | GPIO 2 / Pin 3 |
| SCL | GPIO 3 / Pin 5 |
| ADR | 3.3V |

ADR connected to 3.3V sets:

```text
BNO055 Sensor 2 = 0x29
```

> **Important:** Check the exact BNO055 breakout-board specifications before connecting power. Some breakout boards have a `VIN` pin with onboard regulation, while bare BNO055 devices require 3.3V.

---

## 5. Complete Wiring

Both BNO055 sensors are connected in parallel to the Raspberry Pi 5 I²C bus.

```text
                         Raspberry Pi 5
                     ┌──────────────────┐
                     │                  │
       3.3V Pin 1 ───┼─────────────┬────┼─── BNO055 #1 VCC
                     │             │    │
                     │             └────┼─── BNO055 #2 VCC
                     │                  │
        GND Pin 6 ───┼─────────────┬────┼─── BNO055 #1 GND
                     │             │    │
                     │             └────┼─── BNO055 #2 GND
                     │                  │
 GPIO 2 Pin 3 SDA ───┼─────────────┬────┼─── BNO055 #1 SDA
                     │             │    │
                     │             └────┼─── BNO055 #2 SDA
                     │                  │
 GPIO 3 Pin 5 SCL ───┼─────────────┬────┼─── BNO055 #1 SCL
                     │             │    │
                     │             └────┼─── BNO055 #2 SCL
                     │                  │
                     └──────────────────┘

 BNO055 #1 ADR ─────────────── GND
 BNO055 #2 ADR ─────────────── 3.3V
```

### Connection Summary

```text
3.3V ──→ Both BNO055 VCC
GND  ──→ Both BNO055 GND
SDA  ──→ Both BNO055 SDA
SCL  ──→ Both BNO055 SCL

Sensor 1 ADR → GND
Sensor 2 ADR → 3.3V
```

---

## 6. Enable I²C

Open Raspberry Pi configuration:

```bash
sudo raspi-config
```

Go to:

```text
Interface Options
    ↓
I2C
    ↓
Enable
```

Then reboot:

```bash
sudo reboot
```

---

## 7. Install I²C Tools

```bash
sudo apt update
sudo apt install -y i2c-tools
```

Check the I²C interface:

```bash
ls /dev/i2c*
```

Normally:

```text
/dev/i2c-1
```

---

## 8. Detect Both BNO055 Sensors

Run:

```bash
sudo i2cdetect -y 1
```

Expected addresses:

```text
0x28
0x29
```

Example:

```text
     0 1 2 3 4 5 6 7 8 9 a b c d e f
00: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- 28 29 -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

If both `28` and `29` appear, the I²C wiring and address configuration are correct.

---

## 9. Software Requirements

The Raspberry Pi 5 version should use Python rather than Arduino code.

Recommended software:

```text
Python 3
I²C
smbus2
Adafruit Blinka
Adafruit BNO055 library
```

Create the project directory:

```bash
mkdir -p ~/dual-bno055
cd ~/dual-bno055
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the required Python packages according to the Python implementation used by the project.

---

## 10. Sensor Data

Each BNO055 provides:

```text
Heading
Roll
Pitch
```

Example:

```text
Sensor 1
Heading : 342.7°
Roll    : -2.3°
Pitch   : 4.1°

Sensor 2
Heading : 180.2°
Roll    : 8.5°
Pitch   : -12.4°
```

---

## 11. Direction Calculation

| Heading Range | Direction |
|---:|---|
| 337.5°–360° / 0°–22.5° | North |
| 22.5°–67.5° | North-East |
| 67.5°–112.5° | East |
| 112.5°–157.5° | South-East |
| 157.5°–202.5° | South |
| 202.5°–247.5° | South-West |
| 247.5°–292.5° | West |
| 292.5°–337.5° | North-West |

---

## 12. Roll Status

The system uses a ±5° threshold:

```text
Roll > +5°  → Right Roll
Roll < -5°  → Left Roll
Otherwise   → Level
```

---

## 13. Pitch Status

The system uses a ±5° threshold:

```text
Pitch > +5°  → Nose Up
Pitch < -5°  → Nose Down
Otherwise    → Level
```

---

## 14. CSV Telemetry

The telemetry format is:

```text
H1,R1,P1,H2,R2,P2
```

Where:

| Column | Description |
|---|---|
| H1 | Sensor 1 Heading |
| R1 | Sensor 1 Roll |
| P1 | Sensor 1 Pitch |
| H2 | Sensor 2 Heading |
| R2 | Sensor 2 Roll |
| P2 | Sensor 2 Pitch |

Example:

```text
342.70,-2.30,4.10,180.20,8.50,-12.40
```

The Raspberry Pi version can save this data directly to a CSV file.

Recommended location:

```text
data/
└── orientation_log.csv
```

---

## 15. Recommended Project Structure

```text
dual-bno055/
│
├── .venv/
├── bno055_dual.py
├── data/
│   └── orientation_log.csv
├── README.md
└── requirements.txt
```

---

## 16. Troubleshooting

### Only `0x28` appears

Check Sensor 2:

```text
ADR → 3.3V
```

Also check SDA, SCL, VCC, and GND.

### Only `0x29` appears

Check Sensor 1:

```text
ADR → GND
```

### Neither sensor appears

Check:

- I²C is enabled.
- SDA → GPIO 2 / Pin 3.
- SCL → GPIO 3 / Pin 5.
- GND is connected.
- Sensors are powered correctly.
- Jumper wires are secure.

Run:

```bash
sudo i2cdetect -y 1
```

### Both sensors show the same address

Check the ADR connections:

```text
Sensor 1 ADR → GND
Sensor 2 ADR → 3.3V
```

Expected:

```text
Sensor 1 → 0x28
Sensor 2 → 0x29
```

---

## 17. Raspberry Pi 5 Safety Notes

Raspberry Pi 5 GPIO pins use **3.3V logic**.

Do not apply 5V directly to:

```text
GPIO 2
GPIO 3
or other GPIO pins
```

Always ensure a common ground:

```text
Raspberry Pi GND
      │
      ├── BNO055 #1 GND
      │
      └── BNO055 #2 GND
```

---

## 18. Data Flow

```text
       BNO055 #1
         0x28
           │
           │
           ├──── SDA ─────┐
           │              │
           └──── SCL ─────┤
                          │
                    Raspberry Pi 5
                          │
                          │ I²C Bus
                          │
           ┌──────────────┴──────────────┐
           │                             │
       BNO055 #1                     BNO055 #2
         0x28                           0x29
           │                             │
           └──────── Orientation ────────┘
                          │
                          ▼
                    Python Program
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Heading       Roll       Pitch
              │           │           │
              └───────────┼───────────┘
                          ▼
                    Direction Status
                          │
                          ▼
                   CSV Telemetry
```

---

## 19. Quick Setup

### Hardware

```text
BNO055 #1:
ADR → GND
Address → 0x28

BNO055 #2:
ADR → 3.3V
Address → 0x29

Both sensors:
SDA → GPIO 2 / Pin 3
SCL → GPIO 3 / Pin 5
GND → GND
VCC → Appropriate supply
```

### Raspberry Pi

Enable I²C:

```bash
sudo raspi-config
```

Install I²C tools:

```bash
sudo apt update
sudo apt install -y i2c-tools
```

Check sensors:

```bash
sudo i2cdetect -y 1
```

Expected:

```text
0x28
0x29
```

---

## 20. Project Application

This dual-BNO055 system can be used for:

- ROV orientation monitoring
- Robotics
- Motion tracking
- Platform stabilization
- Dual-IMU comparison
- Experimental navigation systems
- Underwater robotics telemetry

