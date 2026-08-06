import time
import board
import busio
import adafruit_bno055

def get_compass_direction(heading):
    if heading is None:
        return "N/A"
    if heading >= 337.5 or heading < 22.5:
        return "North"
    elif heading < 67.5:
        return "North-East"
    elif heading < 112.5:
        return "East"
    elif heading < 157.5:
        return "South-East"
    elif heading < 202.5:
        return "South"
    elif heading < 247.5:
        return "South-West"
    elif heading < 292.5:
        return "West"
    else:
        return "North-West"

def get_tilt_status(val):
    if val is None:
        return "N/A"
    if val > 5.0:
        return "Positive Tilt"
    elif val < -5.0:
        return "Negative Tilt"
    else:
        return "Level"

def main():
    i2c = busio.I2C(board.SCL, board.SDA)

    try:
        sensor1 = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
        print("Sensor 1 (0x28) Initialized.")
    except Exception as e:
        print(f"Error Sensor 1: {e}")
        return

    try:
        sensor2 = adafruit_bno055.BNO055_I2C(i2c, address=0x29)
        print("Sensor 2 (0x29) Initialized.")
    except Exception as e:
        print(f"Error Sensor 2: {e}")
        return

    print("\nReading Orientation Telemetry (Ctrl+C to Stop)...\n")

    while True:
        try:
            h1, r1, p1 = sensor1.euler
            h2, r2, p2 = sensor2.euler

            print("=========================================")
            print("         DUAL IMU TELEMETRY STREAM       ")
            print("=========================================")
            
            print("[Sensor 1 - Address 0x28]")
            if h1 is not None:
                print(f"  Heading : {h1:6.1f}° ({get_compass_direction(h1)})")
                print(f"  Roll    : {r1:6.1f}° ({get_tilt_status(r1)})")
                print(f"  Pitch   : {p1:6.1f}° ({get_tilt_status(p1)})")
            else:
                print("  Initializing orientation...")

            print("\n[Sensor 2 - Address 0x29]")
            if h2 is not None:
                print(f"  Heading : {h2:6.1f}° ({get_compass_direction(h2)})")
                print(f"  Roll    : {r2:6.1f}° ({get_tilt_status(r2)})")
                print(f"  Pitch   : {p2:6.1f}° ({get_tilt_status(p2)})")
            else:
                print("  Initializing orientation...")

            print("\n--- CSV Stream ---")
            print(f"{h1},{r1},{p1},{h2},{r2},{p2}")
            print("=========================================\n")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nLogging terminated by user.")
            break
        except Exception as err:
            print(f"Read error: {err}")
            time.sleep(1)

if __name__ == "__main__":
    main()