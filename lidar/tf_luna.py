import sys
import serial
import time

# Configuration — auto-detect platform
if sys.platform == "win32":
    SERIAL_PORT = "COM3"
else:
    SERIAL_PORT = "/dev/serial0"  # Pi 5 UART on GPIO 14/15

BAUD_RATE = 115200
MIN_DISTANCE_CM = 30       # Threshold — anything closer triggers warning
FRAME_HEADER = 0x59

def read_distance(ser):
    """Read one distance frame from TF Luna. Returns distance in cm or None."""
    # Wait for two consecutive 0x59 header bytes
    while True:
        b = ser.read(1)
        if not b:
            return None
        if b[0] == FRAME_HEADER:
            b2 = ser.read(1)
            if not b2:
                return None
            if b2[0] == FRAME_HEADER:
                break

    # Read remaining 7 bytes of the 9-byte frame (2 header bytes already consumed)
    data = ser.read(7)
    if len(data) < 7:
        return None

    dist_low, dist_high = data[0], data[1]
    distance_cm = dist_low + (dist_high << 8)
    return distance_cm


def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(0.1)

    print(f"TF Luna running on {SERIAL_PORT} — threshold: {MIN_DISTANCE_CM} cm")
    print("-" * 40)

    was_too_close = False

    while True:
        dist = read_distance(ser)
        if dist is None:
            continue

        too_close = dist < MIN_DISTANCE_CM

        if too_close and not was_too_close:
            print(f"lidar: Too close ({dist} cm)")
        elif not too_close and was_too_close:
            print(f"lidar: Clear ({dist} cm)")

        was_too_close = too_close


if __name__ == "__main__":
    main()
