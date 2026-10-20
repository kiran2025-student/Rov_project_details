# PH-4502C pH Sensor — Arduino Firmware

## Overview

`Ph_sensor.ino` reads the analog output of a PH-4502C pH module on an Arduino Uno, averages 15 ADC samples, estimates the voltage and pH, and prints one CSV row to the Serial Monitor every 1.5 seconds.

| Property | Value |
|---|---|
| Microcontroller | Arduino Uno |
| Sensor module | PH-4502C |
| Analog output | A0 |
| Serial baud rate | 9600 |
| Samples per reading | 15, spaced 10 ms apart |
| Report interval | 1.5 seconds |

## Wiring

| Module | Arduino Uno |
|---|---|
| VCC | 5V |
| GND | GND |
| Analog output (PO/AO) | A0 |

Use the module's analog output. Keep the probe and electronics dry; only the probe tip belongs in the solution.

## Calibration

The sketch starts with these constants:

| Name | Value | Purpose |
|---|---:|---|
| `VREF_VOLTS` | 5.0 | Nominal Uno ADC reference voltage |
| `ADC_MAX_COUNT` | 1023 | Maximum count for the Uno's 10-bit ADC |
| `PH_SLOPE` | -5.56 | Voltage-to-pH slope |
| `PH_OFFSET` | 20.89 | Voltage-to-pH offset |

The estimate is calculated as:

```
voltage = average_adc * (VREF_VOLTS / ADC_MAX_COUNT)
estimated_ph = PH_SLOPE * voltage + PH_OFFSET
```

These slope and offset values are starting values, not a guaranteed calibration for every module and probe. Calibrate with pH 4.0, 7.0, and 10.0 buffer solutions. Measure the actual ADC reference voltage if accurate voltage conversion is required. The probe also needs time to stabilize after power-up and when moved to a new solution. Temperature affects pH readings; this sketch does not compensate for temperature.

## Sampling and serial output

Each reading averages 15 calls to `analogRead(A0)), separated by 10 ms. The sketch then prints a CSV row with the header:

```text
sample,raw_adc_avg,voltage_v,estimated_ph
```

For example:

```text
1,512.3,2.503,6.97
```

Open the Serial Monitor at 9600 baud. The firmware is an Arduino C++ sketch and is named `Ph_sensor.ino` so the `Ph_sensor` sketch folder can be compiled directly by Arduino CLI or opened in the Arduino IDE.

## Safety and use

- Verify the module pinout and operating voltage for the specific board before wiring.
- Rinse the probe with distilled water between buffer solutions; avoid wiping the glass bulb dry.
- Store the probe according to its manufacturer's instructions and keep the electronics out of water.
- Do not treat an uncalibrated value as a reliable water-quality or safety measurement.

## Calibration reference

The initial slope and offset were based on the [PH-4502C Arduino pH meter reference](https://cimpleo.com/blog/arduino-ph-meter-using-ph-4502c/). Recalibrate against known buffer solutions for the particular module and probe.
