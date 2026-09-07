#!/usr/bin/env python3
"""
================================================================================
 main.py — ROV Firmware Orchestrator
================================================================================

WHAT THIS IS
-------------
A top-level launcher for the ROV's independent subsystems (IMU, and later
thrusters, depth sensor, control loop, etc.). It runs each subsystem as
its OWN separate process — exactly as if you'd typed
`python3 V3_two_sensor_IMU_code.py` yourself in its own terminal.

WHY THIS APPROACH
-------------------
V3_two_sensor_IMU_code.py (and future subsystem scripts) don't need ANY
changes to be run this way — they don't need to be rewritten as
importable functions, don't need threading added, nothing. If a script
already runs standalone with `python3 <script>.py`, this orchestrator can
launch it as-is. Add a new subsystem later by adding one entry to the
SUBSYSTEMS list below.

WHAT THIS HANDLES FOR YOU
----------------------------
- Starts every subsystem listed below, each as its own process.
- Watches all of them; if one exits unexpectedly, says so clearly.
- If a subsystem marked "required": True crashes, shuts everything else
  down too (fail-safe default — change this policy per subsystem if a
  crash in one shouldn't stop the others; see the SUBSYSTEMS list).
- On Ctrl+C, shuts every subsystem down gracefully (SIGINT first, giving
  each script's own cleanup code — like closing its CSV file and
  releasing the I2C bus — a chance to run), escalating to a harder stop
  only if a process doesn't exit in time.

HOW TO USE
-----------
1. Add each subsystem script to the SUBSYSTEMS list below.
2. Run:
       python3 main.py
3. Press Ctrl+C once to shut everything down cleanly.

CURRENT LIMITATION (documented, not hidden)
----------------------------------------------
This does NOT yet let subsystems talk to each other (e.g. the IMU
feeding a future control loop) — each process is independent and only
communicates via whatever file/network mechanism it already uses (for
the IMU script, that's its CSV log). See BNO055_Future_Roadmap.md, item
#5 ("Publish readings instead of just logging them") for the planned
next step once a control loop subsystem actually exists.
================================================================================
"""

import os
import signal
import subprocess
import sys
import time

# --------------------------------------------------------------------------
# CONFIGURATION — add a new subsystem by adding one entry here.
# --------------------------------------------------------------------------
SUBSYSTEMS = [
    {
        "name": "IMU (dual BNO055)",
        "script": "V3_two_sensor_IMU_code.py",
        # If True: this subsystem crashing triggers a full shutdown of
        # every other subsystem too. If False: it's logged as a warning,
        # but the rest keep running. Set per-subsystem based on whether
        # the ROV can safely operate without it.
        "required": True,
    },
    {
        "name": "IMU Web Dashboard",
        "script": "imu_web_dashboard.py",
        # False: the dashboard is only a viewer of the CSV the IMU script
        # writes -- if it crashes (or Flask isn't installed on this
        # machine yet), the IMU logging itself is completely unaffected,
        # so there's no safety reason to bring anything else down over it.
        "required": False,
    },
    # Future subsystems — uncomment/add once those scripts exist:
    # {"name": "Thruster Control", "script": "thruster_control.py", "required": True},
    # {"name": "Depth Sensor",     "script": "depth_sensor.py",     "required": False},
]

# How long (seconds) to wait after asking a subsystem to shut down
# gracefully (SIGINT) before escalating to a harder stop.
GRACEFUL_SHUTDOWN_TIMEOUT_S = 5

# How often (seconds) the orchestrator checks whether any subsystem has
# exited on its own (crashed, or finished).
MONITOR_POLL_INTERVAL_S = 1.0


class Subsystem:
    """Wraps one subprocess with a name and its required/optional policy."""

    def __init__(self, name, script, required):
        self.name = name
        self.script = script
        self.required = required
        self.process = None
        self._exit_reported = False

    def start(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.script)
        if not os.path.isfile(script_path):
            print(f"[main] ERROR: '{self.script}' not found at {script_path}. "
                  f"Skipping this subsystem.")
            return False

        # start_new_session=True gives this child its own process group,
        # so a Ctrl+C in the terminal (which normally goes to the whole
        # foreground group) does NOT automatically reach the children.
        # main.py's own signal handler below takes full, explicit
        # responsibility for shutting children down in the right order,
        # instead of relying on ambient shell/terminal behavior.
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            start_new_session=True,
        )
        print(f"[main] Started '{self.name}' (PID {self.process.pid})")
        return True

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def request_shutdown(self):
        """Sends SIGINT (same as Ctrl+C) so the subsystem's own cleanup code runs."""
        if self.is_running():
            self.process.send_signal(signal.SIGINT)

    def force_stop(self):
        """Escalation: SIGTERM, then SIGKILL as an absolute last resort."""
        if self.is_running():
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print(f"[main] '{self.name}' did not respond to SIGTERM — sending SIGKILL.")
                self.process.kill()


def shutdown_all(subsystems, reason):
    """Gracefully stops every currently-running subsystem, escalating if needed."""
    print(f"\n[main] Shutting down all subsystems. Reason: {reason}")

    running = [s for s in subsystems if s.is_running()]
    for s in running:
        print(f"[main] Requesting graceful shutdown of '{s.name}'...")
        s.request_shutdown()

    deadline = time.monotonic() + GRACEFUL_SHUTDOWN_TIMEOUT_S
    while time.monotonic() < deadline:
        running = [s for s in running if s.is_running()]
        if not running:
            break
        time.sleep(0.2)

    for s in running:
        print(f"[main] '{s.name}' did not exit within "
              f"{GRACEFUL_SHUTDOWN_TIMEOUT_S}s — forcing stop.")
        s.force_stop()

    print("[main] All subsystems stopped.")


def main():
    subsystems = [Subsystem(**entry) for entry in SUBSYSTEMS]

    started = [s for s in subsystems if s.start()]
    if not started:
        print("[main] No subsystems could be started. Exiting.")
        sys.exit(1)

    # main.py's own Ctrl+C handling: catch SIGINT here, and be the one
    # place responsible for deciding how children shut down (see
    # start_new_session=True above for why this isn't automatic).
    shutdown_requested = {"flag": False}

    def handle_sigint(signum, frame):
        shutdown_requested["flag"] = True

    signal.signal(signal.SIGINT, handle_sigint)

    print(f"\n[main] {len(started)} subsystem(s) running. Press Ctrl+C to stop.\n")

    try:
        while True:
            if shutdown_requested["flag"]:
                shutdown_all(started, reason="Ctrl+C received")
                break

            # Check whether anything has exited on its own (crashed or
            # finished unexpectedly -- these scripts are meant to run
            # until stopped, so any exit here is noteworthy).
            for s in started:
                if not s.is_running() and s.process.returncode is not None:
                    # Already-reported exits won't be running, so guard
                    # against re-reporting the same exit every poll cycle.
                    if s._exit_reported:
                        continue
                    s._exit_reported = True

                    print(f"[main] '{s.name}' exited on its own "
                          f"(return code {s.process.returncode}).")

                    if s.required:
                        shutdown_all(started, reason=f"'{s.name}' is required and stopped")
                        sys.exit(1)
                    else:
                        print(f"[main] '{s.name}' is not required — "
                              f"continuing with remaining subsystems.")

            time.sleep(MONITOR_POLL_INTERVAL_S)
    except KeyboardInterrupt:
        # Fallback in case SIGINT arrives between the flag check and the
        # sleep, rather than being caught by handle_sigint in time.
        shutdown_all(started, reason="Ctrl+C received")


if __name__ == "__main__":
    main()
