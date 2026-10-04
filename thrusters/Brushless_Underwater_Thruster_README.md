# Brushless Underwater Thruster --- README

## 1. Product Identification

**Product:** Brushless Underwater Thruster\
**Type:** Brushless underwater propulsion motor / thruster\
**Propeller:** 3-blade enclosed propeller\
**Propeller variants shown on packaging:** CW / CCW\
**Advertised waterproof depth on packaging:** 2000 m\
**Intended use:** Underwater propulsion for ROVs, underwater robots,
boats, and similar projects.

> **Important:** The 2000 m depth figure is the manufacturer's/package
> claim visible in the supplied photographs. It should not be treated as
> a verified operating depth for your complete ROV system. Connectors,
> cables, seals, housing, and other components may have much lower
> pressure ratings.

------------------------------------------------------------------------

## 2. Important Electrical Requirement

This is a **brushless motor** and must **not be connected directly to a
battery**.

The package specifically states:

> "This product can't use battery directly, it must be used with
> brushless motor driver."

Therefore, the electrical chain should be:

**Battery → Fuse/Protection → Power Distribution → Brushless ESC/Motor
Driver → Thruster**

The controller sends the required control signal to the ESC/motor
driver.

### Do not do this

**Battery → Thruster directly**

Direct battery connection can cause excessive current, uncontrolled
operation, overheating, or damage to the motor.

### ESC selection

The exact motor voltage, current, KV/rating, and maximum power are **not
visible on the supplied packaging photographs**. Do not select an ESC
only from the motor's physical appearance.

Before final installation, confirm the following from the
seller/datasheet:

-   Rated voltage
-   Maximum operating voltage
-   Maximum continuous current
-   Peak current
-   Motor power
-   KV or RPM rating, if specified
-   Required ESC type
-   Recommended battery cell count
-   Propeller rotation direction
-   Maximum allowable operating temperature

Select the ESC based on the manufacturer's electrical specifications.

------------------------------------------------------------------------

## 3. Specifications Visible from the Packaging

  Parameter                Specification / Observation
  ------------------------ ------------------------------------------
  Motor type               Brushless underwater thruster
  Propeller                3-blade enclosed propeller
  Rotation options         CW / CCW shown on package
  Waterproof depth claim   2000 m
  Battery connection       Direct battery connection NOT allowed
  Required driver          Brushless motor driver / ESC
  Dry running              Avoid prolonged operation without water
  Mechanical safety        Thruster must be securely fixed
  Propeller safety         Check the red propeller screw before use
  Exact voltage            Not specified on supplied photos
  Exact current            Not specified on supplied photos
  Exact power              Not specified on supplied photos
  Exact KV                 Not specified on supplied photos

------------------------------------------------------------------------

## 4. Operating Procedure

### Before powering the system

1.  Inspect the thruster body for cracks, damage, corrosion, or loose
    parts.
2.  Check the propeller for cracks, deformation, or foreign objects.
3.  Check that the **red propeller screw is tight**.
4.  Confirm that the thruster is firmly mounted to the ROV frame.
5.  Check all electrical connections and insulation.
6.  Confirm correct ESC/motor-driver wiring.
7.  Confirm that the battery voltage is within the manufacturer's
    specified motor/ESC range.
8.  Make sure the propeller can rotate freely.
9.  Keep hands, wires, tools, and loose objects away from the propeller.
10. If testing outside water, perform only a very brief functional check
    if the manufacturer permits it. Do not run the thruster dry for an
    extended period.

------------------------------------------------------------------------

## 5. Dry-Running Warning

The package specifically warns:

> "Do not idle without water for a long time, which may damage the
> bearing and coil."

Water provides cooling and is part of the intended operating
environment.

### Recommended practice

-   Prefer testing the thruster **submerged in water**.
-   Avoid long-duration dry testing.
-   Never leave the thruster spinning without water while
    troubleshooting software or control systems.
-   If a dry test is absolutely necessary, keep it extremely brief and
    follow the manufacturer's instructions.

------------------------------------------------------------------------

## 6. Mechanical Mounting and Safety

The package states that the rotating thruster should be fixed
effectively to avoid hand contact.

The thruster should therefore be mounted to a rigid frame before normal
operation.

### Mounting checklist

-   Use a mechanically strong mounting bracket.
-   Prevent the thruster from rotating or moving under thrust.
-   Keep the propeller guard/enclosure unobstructed.
-   Maintain sufficient clearance around the propeller.
-   Route cables away from the propeller.
-   Use strain relief for the motor cable.
-   Do not hold the thruster by hand while operating it.
-   Never touch the rotating propeller.

------------------------------------------------------------------------

## 7. Propeller Screw Inspection

The package specifically warns:

> "Before use, check whether the red screw is loose to avoid the
> propeller falling."

Before every test:

1.  Disconnect power.
2.  Inspect the red propeller screw.
3.  Check that the propeller is properly seated.
4.  Tighten the screw according to the manufacturer's recommended
    method.
5.  Rotate the propeller by hand to verify that it moves freely.
6.  Do not operate if the propeller, screw, or shaft appears damaged.

Do not overtighten the screw if the manufacturer does not specify a
torque value.

------------------------------------------------------------------------

## 8. Water Operation

For an ROV installation:

-   Fully inspect the thruster before entering the water.
-   Ensure the electrical connections are properly sealed.
-   Keep connectors and exposed electrical joints protected from water.
-   Avoid operating near sand, stones, ropes, weeds, or other debris.
-   Stop the motor immediately if abnormal vibration, noise, or loss of
    thrust occurs.
-   After operation, inspect the propeller and thruster for debris.

### Important

The thruster's advertised waterproof/depth rating does **not
automatically make the complete ROV waterproof**. The complete system's
depth capability is limited by its weakest pressure-sensitive component.

------------------------------------------------------------------------

## 9. ROV Installation

For a multi-thruster ROV, verify the rotation direction of every
thruster.

Typical checks include:

-   Forward thrust
-   Reverse thrust
-   Left/right movement
-   Vertical movement
-   Yaw control

Do not assume that CW and CCW thrusters are interchangeable without
checking the propeller and motor configuration.

For a 6-thruster ROV, verify each motor individually at low power before
performing combined movement tests.

------------------------------------------------------------------------

## 10. Initial Commissioning Test

### Stage 1 --- Visual inspection

Check:

-   Propeller
-   Red screw
-   Motor body
-   Cable
-   Mounting bracket
-   Connector

### Stage 2 --- Electrical check

Verify:

-   Battery voltage
-   ESC rating
-   Correct polarity
-   Signal wiring
-   Common ground/control reference where required by the ESC
-   Current protection

### Stage 3 --- Low-power water test

1.  Place the thruster securely in water.
2.  Keep people away from the propeller.
3.  Apply a low control command.
4.  Confirm the expected rotation direction.
5.  Check for abnormal noise or vibration.
6.  Gradually increase power.
7.  Stop immediately if excessive current, vibration, heating, or
    unusual noise occurs.

### Stage 4 --- ROV integration

After individual thruster testing:

1.  Test each thruster separately.
2.  Test pairs.
3.  Test all thrusters at low power.
4.  Verify the ROV movement directions.
5.  Perform a short controlled water test.
6.  Only then increase the operating duration.

------------------------------------------------------------------------

## 11. Stop Operation Immediately If

Stop the thruster and disconnect power if you observe:

-   Unusual vibration
-   Grinding or abnormal mechanical noise
-   Propeller wobbling
-   Loose red propeller screw
-   Excessive heating
-   Burning smell
-   Smoke
-   Sudden loss of thrust
-   Abnormal current consumption
-   Damaged cable or connector
-   Water entering a component that is not designed for immersion

Do not restart until the cause has been identified.

------------------------------------------------------------------------

## 12. Maintenance After Use

After every underwater test:

1.  Disconnect the battery.
2.  Inspect the propeller.
3.  Remove weeds, sand, fishing line, or other debris.
4.  Check the red propeller screw.
5.  Inspect the cable and connector.
6.  Check the thruster body for damage.
7.  Allow external surfaces to dry appropriately.
8.  Store the thruster without mechanical load on the propeller.

Follow the manufacturer's maintenance instructions if they provide
additional lubrication, sealing, or servicing requirements.

------------------------------------------------------------------------

## 13. Information That Must Be Confirmed Before Final ROV Integration

The supplied photographs do not show the complete technical datasheet.
Before selecting the battery and ESC, obtain these values from the
seller/manufacturer:

-   Rated voltage: \_\_\_\_\_\_ V
-   Maximum voltage: \_\_\_\_\_\_ V
-   Continuous current: \_\_\_\_\_\_ A
-   Peak current: \_\_\_\_\_\_ A
-   Rated power: \_\_\_\_\_\_ W
-   Maximum power: \_\_\_\_\_\_ W
-   KV / RPM: \_\_\_\_\_\_
-   Recommended ESC: \_\_\_\_\_\_ A
-   Recommended battery: \_\_\_\_\_\_ S
-   Maximum continuous operating time: \_\_\_\_\_\_
-   Verified operating depth: \_\_\_\_\_\_ m
-   Cable length: \_\_\_\_\_\_
-   Connector type: \_\_\_\_\_\_

### Electrical sizing reminder

If the motor power and voltage are known:

**I ≈ P / V**

where:

-   `I` = motor current in amperes
-   `P` = electrical power in watts
-   `V` = motor voltage in volts

The actual current must be taken from the manufacturer's specifications
or measured during testing. Do not use this simple equation to guess the
motor's rating.

------------------------------------------------------------------------

## 14. Quick Safety Checklist

Before every operation:

-   [ ] Correct ESC/brushless motor driver used
-   [ ] Battery voltage verified
-   [ ] Wiring polarity checked
-   [ ] Thruster firmly mounted
-   [ ] Propeller free from debris
-   [ ] Red propeller screw checked
-   [ ] No loose wires near propeller
-   [ ] Thruster submerged for normal operation
-   [ ] No hands near rotating propeller
-   [ ] Emergency power disconnect available
-   [ ] First test performed at low power

------------------------------------------------------------------------

## 15. Key Rules

**1. Never connect the brushless thruster directly to the battery.**

**2. Use the correct brushless ESC/motor driver.**

**3. Do not operate the thruster dry for a long time.**

**4. Secure the thruster before applying power.**

**5. Check the red propeller screw before every operation.**

**6. Keep hands, cables, and objects away from the rotating propeller.**

**7. Do not assume the 2000 m package claim represents the depth rating
of the complete ROV.**

**8. Confirm the manufacturer's voltage/current/power specifications
before final electrical integration.**

------------------------------------------------------------------------

## Source Note

This README was prepared from the information visible on the supplied
product packaging photographs. Where a technical parameter was not
visible, it has intentionally been marked as **not specified** rather
than estimated.
