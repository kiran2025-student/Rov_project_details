# ROV Motor and ESC Test Setup

## Components

- **Thruster:** ApisQueen U1 underwater brushless thruster, ducted propeller
- **ESC:** ApisQueen 45 A bidirectional ESC (the photos/listing show 45 A)
- **Battery:** LiPo, 3S, 5200 mAh, 35C (as read from the battery label)
- **Controller:** Arduino-compatible board sending servo-style PWM to the ESC
- **Power connector:** XT60 on the battery/ESC power input

The battery label's theoretical current rating is `5.2 Ah × 35C = 182 A`; this is a label-based maximum, not a promise of continuous real-world output. The ESC is marked 45 A, so the ESC rating is the limiting rating in this single-motor chain. Confirm ratings, connector condition, and wiring before further operation.

## Voltage and expected performance

The product listing states a 12–16 V operating range and recommends 16 V (4S LiPo). This setup uses 3S: 11.1 V nominal and 12.6 V fully charged. It is therefore at or slightly below the listed low end except when freshly charged, and should be expected to produce less thrust than the 4S figures.

The listing's performance table reports the following at full throttle:

| Supply voltage | Forward current | Forward thrust | Reverse current | Reverse thrust |
|---:|---:|---:|---:|---:|
| 10 V | 4 A | 0.90 kgf | 4 A | 0.70 kgf |
| 12 V | 5 A | 1.20 kgf | 5 A | 0.80 kgf |
| 14 V | 8 A | 1.50 kgf | 8 A | 0.90 kgf |
| 16 V | 9 A | 1.70 kgf | 8 A | 1.20 kgf |

These are manufacturer/listing figures; actual performance depends on the battery, water flow, mounting, and test conditions.

## Wiring

```text
LiPo XT60 positive  ───── ESC battery positive
LiPo XT60 negative  ───── ESC battery negative

ESC three phase wires ─── Thruster three motor wires

Arduino digital pin 9 ─── ESC PWM signal (usually white/yellow/orange)
Arduino GND          ─── ESC signal ground (usually black/brown)

ESC red BEC wire     ─── Leave disconnected and insulate when Arduino is USB powered
```

- The Arduino and ESC signal must share a ground.
- Do not connect the ESC's red BEC 5 V wire to the Arduino 5 V pin when the Arduino is powered through USB or another 5 V source. If powering the Arduino from the BEC instead, follow the board and ESC documentation and do not connect a second 5 V source.
- Disconnect the LiPo before changing wiring. Check polarity before connecting the XT60.
- The ESC's three motor phase wires can generally be connected in any order. If rotation direction is wrong, disconnect battery power and swap any two phase wires, or reverse direction with the controller if supported.

## PWM control

The product information describes a 2 ms servo-style PWM period (about 50 Hz):

- `1500 µs`: neutral/stop
- `1500–2000 µs`: forward
- `1000–1500 µs`: reverse

Start close to neutral and increase the command in small steps. Values below are approximate starting points; actual response depends on ESC calibration:

| Pulse width | Approximate command |
|---:|---|
| 1500 µs | Neutral/stop |
| 1550–1600 µs | Low forward |
| 1650–1700 µs | Moderate forward |
| 1800 µs | High forward |
| 2000 µs | Listing's maximum forward command |
| 1450–1400 µs | Low reverse |
| 1350–1300 µs | Moderate reverse |
| 1200 µs | High reverse |
| 1000 µs | Listing's maximum reverse command |

Do not assume the exact endpoints are calibrated. If operation is inconsistent, return to neutral and consult the ESC instructions for its arming/calibration procedure. Do not use Arduino `analogWrite()` for this signal; use a servo-style pulse generator such as `Servo.writeMicroseconds()`.

## Arduino bench-test sketch

This example holds neutral at startup, briefly commands low forward and reverse, then returns to neutral. The operator should supervise continuously. It is not a failsafe: if the Arduino resets or the signal wire disconnects, ESC behavior depends on its own signal-loss configuration.

```cpp
#include <Servo.h>

Servo esc;

const byte ESC_SIGNAL_PIN = 9;
const int NEUTRAL_US = 1500;
const int FORWARD_US = 1550;
const int REVERSE_US = 1450;

void setup() {
  esc.attach(ESC_SIGNAL_PIN, 1000, 2000);
  esc.writeMicroseconds(NEUTRAL_US);
  delay(3000); // allow ESC initialization at neutral
}

void loop() {
  esc.writeMicroseconds(NEUTRAL_US);
  delay(2000);

  esc.writeMicroseconds(FORWARD_US);
  delay(1000);

  esc.writeMicroseconds(NEUTRAL_US);
  delay(2000);

  esc.writeMicroseconds(REVERSE_US);
  delay(1000);

  esc.writeMicroseconds(NEUTRAL_US);
  delay(5000);
}
```

For more speed, increase the pulse width gradually (forward upward from 1500 µs, reverse downward from 1500 µs), in short supervised tests. Do not jump directly to an endpoint.

## Test procedure and safety

1. Remove the propeller or secure/guard the thruster so nobody can contact the propeller or be struck by the unit.
2. Check the thruster and ESC are dry externally, the shaft turns freely, wiring is insulated, and the battery is not swollen or damaged.
3. Upload the sketch with the battery disconnected. Power the Arduino so it is already outputting neutral.
4. Connect the battery and wait for ESC startup tones. Keep the command at neutral until ready.
5. Test brief low-power pulses. Stop immediately for stuttering, unexpected direction, excessive vibration, hot wiring/connectors, unusual ESC/motor heat, or battery voltage sag.
6. Disconnect the battery before touching wiring. Do not leave a LiPo unattended while connected or charging; charge with a compatible 3S balance charger.

Do not run the thruster dry for extended periods. For water testing, keep the ESC, connectors, and battery dry unless each component is specifically rated for submersion, and mount the thruster securely. The listing/manual describes the ESC as splash-proof rather than suitable for prolonged submersion.

## SimonK note

SimonK refers to firmware used by some brushless ESCs; it is not the name of a universal ESC hardware standard. The available ApisQueen product information describes this ESC as bidirectional, but does not identify its firmware. A SimonK ESC should only be substituted if its specific firmware and hardware support forward, neutral, and reverse operation with the required battery voltage and current. Do not assume a multirotor ESC will reverse.

## Source and uncertainty notes

This guide is based on the user-provided ApisQueen U1 product screenshots and battery photograph, plus the observed successful Arduino motor test. The specific ESC revision, Arduino board, exact LiPo condition, PWM calibration endpoints, and independent measured thrust/current are not confirmed. Verify those details against the labels/manual for the exact hardware before sustained or underwater operation.
