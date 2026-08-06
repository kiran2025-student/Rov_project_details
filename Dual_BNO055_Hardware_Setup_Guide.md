# Dual BNO055 IMU Hardware Setup & Wiring Guide

This document provides a comprehensive hardware setup guide for connecting and configuring **two Adafruit BNO055 9-DOF Orientation Sensors** on a single microcontroller using the **I2C interface**.

---

## 1. Overview & Operating Principle

The BNO055 is a System-in-Package (SiP) integrating a triaxial 14-bit accelerometer, a triaxial 16-bit gyroscope, a triaxial geomagnetic sensor, and a 32-bit Cortex M0+ microcontroller running Bosch Sensortec sensor fusion software.

To run two BNO055 sensors on the same I2C bus:
- **Shared Lines:** Both sensors share the same **SDA (Data)** and **SCL (Clock)** lines.
- **Address Selection:** The `ADR` (or `ADD`) pin determines the 7-bit I2C slave address:
  - **Sensor 1 (`0x28`):** `ADR` connected to **GND** (or left disconnected; internal pull-down).
  - **Sensor 2 (`0x29`):** `ADR` connected to **3.3V / VCC** (HIGH state).

---

## 2. Pinout & I2C Address Reference

| BNO055 Pin | Function | Sensor 1 Connection (`0x28`) | Sensor 2 Connection (`0x29`) |
| :--- | :--- | :--- | :--- |
| **VIN** | Power Supply Input | 3.3V or 5V (Board Dependent) | 3.3V or 5V (Board Dependent) |
| **GND** | Ground | Common System GND | Common System GND |
| **SDA** | I2C Serial Data | Microcontroller SDA Pin | Microcontroller SDA Pin |
| **SCL** | I2C Serial Clock | Microcontroller SCL Pin | Microcontroller SCL Pin |
| **ADR / ADD** | Address Select Pin | **GND** (or Unconnected) | **3.3V / VCC** |
| **RST** | Hardware Reset Pin | Optional (Pull HIGH or leave NC) | Optional (Pull HIGH or leave NC) |
| **INT** | Interrupt Output | Optional (Leave NC if unused) | Optional (Leave NC if unused) |

---

## 3. Microcontroller Connection Wiring Diagrams

### A. Arduino Uno / Nano / Pro Mini (5V Logic)
> **Note:** Adafruit BNO055 breakouts include an onboard 3.3V voltage regulator and level shifters, making them 5V safe on `VIN`, `SDA`, and `SCL`.

```
           +----------------------------------+
           |       Arduino Uno / Nano         |
           |  [5V]   [GND]   [A4/SDA] [A5/SCL]|
           +--+-------+---------+--------+----+
              |       |         |        |
    +---------+-------+---------+--------+--------+
    |         |       |         |        |        |
+---+---+ +---+---+ +-+-----+ +-+-----+  |        |
|  VIN  | |  GND  | |  SDA  | |  SCL  |  |        |
|       | |       | |       | |       |  |        |
|  SENSOR 1       | |  SENSOR 2       |  |        |
|  (Address 0x28) | |  (Address 0x29) |  |        |
|  ADR -----> GND | |  ADR -----> 3.3V|  |        |
+-------+ +-------+ +-------+ +-------+  |        |
                                         |        |
```

* **VIN:** Connect both BNO055 `VIN` pins to **5V**.
* **GND:** Connect both BNO055 `GND` pins to **GND**.
* **SDA:** Connect both BNO055 `SDA` pins to **A4** (Uno) or dedicated SDA pin.
* **SCL:** Connect both BNO055 `SCL` pins to **A5** (Uno) or dedicated SCL pin.
* **Sensor 1 ADR:** Connect to **GND**.
* **Sensor 2 ADR:** Connect to **3.3V**.

---

### B. Arduino Mega 2560

| Connection | Sensor 1 (`0x28`) | Sensor 2 (`0x29`) | Arduino Mega Pin |
| :--- | :--- | :--- | :--- |
| Power | VIN | VIN | **5V** |
| Ground | GND | GND | **GND** |
| Data Line | SDA | SDA | **Pin 20 (SDA)** |
| Clock Line | SCL | SCL | **Pin 21 (SCL)** |
| Address Select | ADR | - | **GND** |
| Address Select | - | ADR | **3.3V / 5V** |

---

### C. ESP32 (3.3V Native Logic)

| Connection | Sensor 1 (`0x28`) | Sensor 2 (`0x29`) | ESP32 Pin |
| :--- | :--- | :--- | :--- |
| Power | VIN | VIN | **3.3V** |
| Ground | GND | GND | **GND** |
| Data Line | SDA | SDA | **GPIO 21 (SDA)** |
| Clock Line | SCL | SCL | **GPIO 22 (SCL)** |
| Address Select | ADR | - | **GND** |
| Address Select | - | ADR | **3.3V** |

---

## 4. Hardware Optimization & Best Practices

### 1. I2C Pull-Up Resistors
* Official Adafruit BNO055 breakout boards include onboard `10kΩ` pull-up resistors on the `SDA` and `SCL` lines.
* When connecting two modules in parallel, the effective pull-up resistance becomes `5kΩ` (`10kΩ || 10kΩ`), which is well within the ideal standard range (`2.2kΩ` to `10kΩ`) for standard mode (100kHz) and fast mode (400kHz) I2C.
* **No external pull-up resistors are required** unless cable lengths exceed 30 cm.

### 2. Cable Length & Noise Reduction
* Keep I2C signal wires as **short as possible** (ideally < 20 cm / 8 inches).
* If using longer cabling (e.g., in ROVs or robotics arms):
  * Use twisted pair wire (twist `SDA` with `GND`, and `SCL` with `GND`).
  * Lower the I2C clock frequency in your Arduino code setup:
    ```cpp
    Wire.setClock(100000); // 100 kHz Standard Speed
    ```
  * Add external `2.2kΩ` pull-up resistors between SDA/SCL and 3.3V near the microcontroller.

### 3. Decoupling & Power Stability
* The BNO055 requires clean power. If running in high-EMI environments (near motor drivers or thrusters):
  * Place a `0.1µF` ceramic capacitor and a `10µF` electrolytic capacitor across `VIN` and `GND` close to each sensor breakout.

---

## 5. Summary Checklist Before Powering Up

- [ ] Sensor 1 `ADR` pin connected to **GND** (I2C address: `0x28`).
- [ ] Sensor 2 `ADR` pin connected to **3.3V** (I2C address: `0x29`).
- [ ] Both `SDA` pins tied together and connected to board's SDA pin.
- [ ] Both `SCL` pins tied together and connected to board's SCL pin.
- [ ] Common ground established across all devices and power sources.
- [ ] Correct library installed: **Adafruit BNO055** & **Adafruit Unified Sensor**.

---

## 6. Troubleshooting Hardware Issues

| Symptom | Probable Cause | Recommended Fix |
| :--- | :--- | :--- |
| **"Sensor 1 or 2 not detected!"** | Incorrect `ADR` wiring or wrong I2C address specified in code. | Verify `ADR` voltage using a multimeter (`0V` for `0x28`, `3.3V` for `0x29`). |
| **I2C Bus Lockup / Freeze** | Loose GND or missing common ground connection. | Ensure all grounds are tied together solidly. |
| **Data drops over long wires** | High bus capacitance or noise from motors. | Reduce I2C clock speed, use shielded/twisted wire, or add lower-value pull-up resistors (`2.2kΩ`). |
