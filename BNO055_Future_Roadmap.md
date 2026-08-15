# BNO055 Dual-IMU Script — Future Roadmap

This document tracks planned and possible future improvements to
`bno055_dual_imu.py`, beyond its current state (dual-sensor I2C reading,
retry logic, calibration throttling, CSV logging). Nothing here is
implemented yet — this is a plan, not a changelog.

Items are grouped by how soon they're likely to matter for the ROV
project, not by difficulty.

---

## Near-term (needed before this plugs into ROV control)

### 1. Sensor fusion between the two IMUs
Right now each sensor's Roll/Pitch/Yaw is read and logged independently —
nothing combines them into one "vehicle orientation" estimate. Before
this feeds a stabilization loop, decide:
- Are the two IMUs redundant (same mounting, used for fault-tolerance —
  average or vote between them), or
- Mounted at different points (used to also infer flex/twist between two
  hull sections)?

  The combining strategy (simple average, weighted by calibration
  status, or a complementary/Kalman filter) depends entirely on that
  answer, so this needs a decision before it needs code.

### 2. Config file instead of hardcoded constants
`SENSOR_1_ADDRESS`, `READ_INTERVAL_S`, `CALIBRATION_READ_EVERY_N_CYCLES`,
etc. are Python constants at the top of the file. Move these to a
`config.yaml` or `config.json` so they can be tuned per test run without
editing and re-deploying code — especially useful once this is one
module inside the larger `rov_firmware/` architecture, where
`config/hardware_config.py` is meant to be the single source of truth.

### 3. Structured logging instead of `print()`
Replace `print()` calls with Python's `logging` module
(`logging.info`, `logging.warning`, `logging.error`). This gives you:
- Log *levels* (so calibration status can be DEBUG while sensor failures
  are ERROR, filterable independently)
- Timestamps on every line automatically
- The option to route logs to a file, the console, or both, without
  changing the calling code

This matters more once this module runs unattended inside a larger
firmware process instead of a terminal you're watching directly.

### 4. Calibration offset persistence
The BNO055 supports reading and writing calibration offsets directly
(`sensor.offsets_accelerometer`, `offsets_magnetometer`,
`offsets_gyroscope`, confirmed in the library source). Currently this
script re-calibrates from scratch every run. A follow-up:
1. Add a one-time calibration routine that waits for `sensor.calibrated`
   to become `True`
2. Save the resulting offsets to a small JSON file per sensor
3. On startup, write saved offsets back to the sensor before entering
   NDOF mode, skipping the figure-8 calibration dance on every boot

This is a real time-saver during ROV testing — recalibrating underwater
gear on land before every dive is tedious.

---

## Mid-term (integration with the rest of the firmware)

### 5. Publish readings instead of just logging them
CSV logging is good for post-run analysis but the stabilization/control
loop needs live data. Options, roughly in order of complexity:
- A simple shared in-memory object (if control code runs in the same
  process)
- A local socket or named pipe (if control runs as a separate process)
- A small pub/sub layer if telemetry also needs to reach a topside
  operator station over the tether

Whichever is chosen should keep `BNO055Sensor` itself unaware of it —
readings should still just be returned as dicts; something else should
own "what happens to a reading after it's read."

### 6. Health/watchdog integration
Right now a disconnected or persistently-failing sensor just logs errors
and returns `None` forever — the script itself never decides "this is
now a critical failure." Once this plugs into the ROV's `safety/`
module, `BNO055Sensor` should expose something like
`consecutive_failures` so a watchdog can decide when "occasional
transient I2C error" becomes "sensor has actually failed, trigger
failsafe."

### 7. Command-line arguments
Add `argparse` support for things you currently have to edit the file to
change: `--single-sensor`, `--log-dir`, `--rate-hz`, `--no-csv`. Useful
for quick bench tests without touching the config constants.

### 8. Unit tests via `pytest` instead of a standalone script
`test_real_logic_mocked_hw.py` currently runs as a plain script with
manual `assert`-based checks. Porting it to `pytest` gets you:
- Individual pass/fail per test instead of the whole script stopping at
  the first `AssertionError`
- Easy CI integration (a GitHub Action that runs the mocked-hardware
  tests on every commit, before anything touches real sensors)
- Fixtures instead of manually re-creating the fake I2C bus in every
  test function

---

## Long-term / stretch

### 9. Axis remapping utility
The library exposes `sensor.axis_remap` (confirmed in source) for
telling the chip "my X axis is actually mounted along your Y axis,"
which matters once IMUs are mounted at odd angles inside the hull rather
than perfectly axis-aligned with the vehicle's own frame. A small
one-time calibration script that walks through the datasheet's mounting
orientation table (section 3.4) and writes the correct remap would save
a lot of "why is roll reading as yaw" debugging later.

### 10. Temperature-based diagnostics
`sensor.temperature` is available but unused. For an underwater vehicle,
logging chip temperature alongside orientation could help distinguish
"sensor drifted because it's actually miscalibrated" from "sensor
drifted because the enclosure is overheating."

### 11. Live plotting / dashboard
A small local web dashboard (e.g. a lightweight Flask/WebSocket page, or
even a matplotlib live plot) showing Roll/Pitch/Yaw for both sensors in
real time during bench testing — faster to eyeball than scrolling
console text or opening the CSV afterward.

### 12. Async I/O
If the ROV firmware eventually moves to an `asyncio`-based main loop
(common for coordinating sensors + control + comms concurrently without
threads), this module would need an async-friendly read path. Not worth
doing until the rest of the firmware architecture actually needs it —
premature async here would add complexity without benefit while this is
still a standalone script.

---

## Explicitly out of scope for this module

To keep `bno055_dual_imu.py` doing one job well, the following belong in
*other* firmware modules, not here:
- PID / stabilization math (belongs in `control/stabilization.py`)
- Thruster mixing (belongs in `control/thruster_mixer.py`)
- Depth sensor reading (separate sensor, separate module)
- Failsafe *decisions* (this module can report health; `safety/failsafe.py`
  should decide what to do about it)

Keeping this boundary clean is what makes items 5 and 6 above
straightforward instead of requiring a rewrite.
