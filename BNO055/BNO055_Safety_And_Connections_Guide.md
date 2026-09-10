# BNO055 IMU Hardware Safety & Wiring Reference Manual

This document provides hardware wiring specs, electrical operating limits, physical handling procedures, and safety protocols for deploying single and dual **BNO055 9-DOF Orientation Sensors** across microcontrollers and single-board computers.

---

## 1. Electrical & Thermal Operating Limits

Operating the BNO055 outside these absolute maximum ratings can cause permanent hardware degradation, I2C bus latch-ups, or premature sensor failure.

| Parameter | Minimum | Nominal | Maximum | Notes / Units |
| :--- | :--- | :--- | :--- | :--- |
| **Supply Voltage (`VIN`)** | 3.3 V | 3.3V – 5.0V | 5.5 V | Dependent on breakout regulator |
| **Logic I/O Voltage (`SDA`, `SCL`, `ADR`)** | -0.3 V | 3.3 V | 3.6 V | Absolute max for raw chip pins |
| **Operating Current (`IDD`)** | 12.3 mA | 12.5 mA | 30.0 mA | During full fusion mode |
| **Operating Temperature** | -40 °C | +25 °C | +85 °C | Sensor fusion degradation above 70°C |
| **I2C Clock Frequency** | 10 kHz | 100 kHz | 400 kHz | Clock stretching support required |

---

## 2. Hardware Wiring Matrix & Pinouts

To operate **two BNO055 sensors** on a single I2C bus without address collisions:
* **Sensor 1 (`0x28`):** Connect `ADR` to **GND** (0V logic).
* **Sensor 2 (`0x29`):** Connect `ADR` to **3.3V** (HIGH logic).

### System Connection Table

| BNO055 Pin | Pin Function | Sensor 1 (`0x28`) | Sensor 2 (`0x29`) | Arduino Uno / Nano | Arduino Mega | ESP32 | Raspberry Pi (Physical Pin) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **VIN** | Main Power Input | Power Source | Power Source | 5V Pin | 5V Pin | 3.3V Pin | **Pin 1 (3.3V Power)** |
| **GND** | System Ground | Common GND | Common GND | GND Pin | GND Pin | GND Pin | **Pin 6 (Ground)** |
| **SDA** | I2C Serial Data | Shared SDA | Shared SDA | A4 | Pin 20 | GPIO 21 | **Pin 3 (GPIO 2 / SDA1)** |
| **SCL** | I2C Serial Clock | Shared SCL | Shared SCL | A5 | Pin 21 | GPIO 22 | **Pin 5 (GPIO 3 / SCL1)** |
| **ADR / ADD** | Address Select | **GND** | **3.3V / VCC** | GND | GND | GND / 3.3V | **Pin 9 (GND) / Pin 17 (3.3V)** |
| **RST** | Hardware Reset | Optional | Optional | Digital Pin | Digital Pin | GPIO Pin | GPIO Pin (NC if unused) |
| **INT** | Hardware Interrupt | Optional | Optional | Interrupt Pin | Interrupt Pin | GPIO Pin | GPIO Pin (NC if unused) |

---

## 3. Essential Electrical & Physical Safety Protocols

### A. Voltage Level Matching & Logic Protection
* **3.3V Native Logic Hosts (ESP32, Raspberry Pi):**
  * GPIO lines on Raspberry Pi and ESP32 are **not 5V tolerant**. Always power the BNO055 from a **3.3V rail**.
  * Never feed 5V into the `SDA`, `SCL`, or `ADR` pins on 3.3V microcontrollers/SBCs.
* **5V Logic Hosts (Arduino Uno, Mega):**
  * Ensure your BNO055 module is an Adafruit or similar breakout board equipped with onboard **3.3V regulators** and **bi-directional level shifters**.
  * If using raw bare BNO055 ICs, external MOSFET logic level converters are mandatory on `SDA` and `SCL`.

### B. Hot-Plugging & Power Order Hazards
* **Do Not Hot-Plug:** Never connect or disconnect the sensor while the microcontroller or power supply is energized. Voltage spikes or transient ground loops during hot-plugging can instantly blow out internal CMOS gates.
* **Common Ground First:** Always ensure a solid, shared **GND connection** between the host board, sensors, and any external power supply prior to applying power to `VIN`.

### C. ESD (Electrostatic Discharge) Handling
* The BNO055 contains highly sensitive MEMS structures and CMOS electronics with ESD tolerance rated up to 2 kV (HBM).
* Always handle breakout boards by the edges, avoiding direct finger contact with bare chip surfaces, headers, or exposed solder pads.
* Use anti-static wrist straps or ground yourself on a metal surface prior to handling the hardware in low-humidity environments.

---

## 4. Signal Integrity & Environment Hardening

### A. Cable Length & I2C Bus Pull-Ups
* **Pull-Up Resistors:** Adafruit BNO055 breakout boards feature onboard `10 kΩ` pull-up resistors on `SDA` and `SCL`.
  * Paralleling two breakout boards on the same bus yields an effective resistance of `5 kΩ` (`10 kΩ || 10 kΩ`), which is optimal for short wires (< 20 cm).
* **Long Cabling (Robotic Arms / ROV Tether Cables):**
  * Wire lengths exceeding 30 cm introduce high bus capacitance, leading to corrupt sensor data or `I2C Remote I/O Error`.
  * Use **twisted-pair cabling** (twist `SDA` with `GND`, and `SCL` with `GND`).
  * Add external `2.2 kΩ` pull-up resistors to 3.3V near the host controller if wire length exceeds 50 cm.

### B. Magnetic Interference & Placement Safety
* **Keep Away from Motors & High Currents:** The BNO055 uses a sensitive triaxial geomagnetic sensor for compass heading fusion.
* **Minimum Clearances:**
  * Maintain at least **10 cm to 15 cm distance** from DC motors, stepper motors, solenoids, thrusters, high-current power distribution boards, and battery packs.
  * Avoid mounting the sensor directly onto ferrous metal frames (iron, steel). Use non-magnetic standoffs (nylon, brass, or 3D-printed PLA/PETG).

### C. Mechanical Shock & Vibration Isolation
* **MEMS Gyroscope Protection:** Heavy mechanical vibration (e.g., from drone propellers or underwater thrusters) creates high-frequency noise that saturates the sensor fusion algorithms.
* Use **silicone anti-vibration damping mounts** or rubber grommets between the sensor PCB and the robot frame.
* Do not apply excessive mechanical torque when screwing down the PCB mounting holes to prevent warping or micro-fracturing the chip package.

---

## 5. Pre-Power Safety Checklist

- [ ] `VIN` power supply voltage verified with a multimeter before plugging into the board.
- [ ] Raspberry Pi/ESP32 power connected to **3.3V**, NOT 5V.
- [ ] Common ground (`GND`) firmly established across all sensors, hosts, and power supplies.
- [ ] Sensor 1 `ADR` tied to **GND** (`0x28`).
- [ ] Sensor 2 `ADR` tied to **3.3V** (`0x29`).
- [ ] No exposed bare copper wires or uninsulated header pins touching metal chassis/frame.
- [ ] Sensors mounted at least 10 cm away from high-current cables, motors, and magnets.
