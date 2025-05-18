import serial
import numpy as np
import logging
import time

# Parameters
SERIAL_PORT = "/dev/tty.usbserial-1450"  # Replace with your printer's serial port
BAUD_RATE = 250000  # Standard baud rate for 3D printers
CYLINDER_RADIUS = 6.5  # Radius for basic choreography (13 cm diameter)
PLATE_CENTER = (10.5, 10.5)  # Center of the 21x21 cm plate
LAYER_HEIGHT = 0.2  # Height per layer (mm)
MOVE_SPEED_BASE = 500  # Base speed in mm/min
WAYPOINTS = 360  # Number of points in the circle
ACK_TIMEOUT = 50  # Timeout for printer acknowledgment in seconds

# Logging configuration
logging.basicConfig(
    filename="printer_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def wait_for_printer_ready(ser):
    start_time = time.time()
    while True:
        if time.time() - start_time > ACK_TIMEOUT:
            logging.error("Timeout waiting for printer acknowledgment.")
            raise TimeoutError("Printer did not acknowledge within timeout period.")
        response = ser.readline().decode(errors="ignore").strip()
        logging.debug(f"Printer response: {response}")
        if "ok" in response or "wait" in response:
            ser.flushInput()
            return


def generate_circle_waypoints(center, radius, num_points):
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    waypoints = [
        (center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle))
        for angle in angles
    ]
    logging.debug(f"Generated {len(waypoints)} waypoints for circular path.")
    return waypoints


def execute_full_choreography(serial_port, baud_rate):
    ser = serial.Serial(serial_port, baud_rate)
    time.sleep(2)

    try:
        logging.info("Starting printer initialization.")
        ser.write(b"G21\n")  # Set units to millimeters
        logging.debug("Sent: G21 (Set units to millimeters)")
        wait_for_printer_ready(ser)

        ser.write(b"G90\n")
        logging.debug("Sent: G90 (Set to absolute positioning)")
        wait_for_printer_ready(ser)

        ser.write(b"M82\n")
        logging.debug("Sent: M82 (Set extruder to absolute mode)")
        wait_for_printer_ready(ser)

        ser.write(b"G28\n")
        logging.debug("Sent: G28 (Home all axes)")
        wait_for_printer_ready(ser)

        # Generate circular waypoints
        waypoints = generate_circle_waypoints(PLATE_CENTER, CYLINDER_RADIUS, WAYPOINTS)

        # Move to the first waypoint
        first_x, first_y = waypoints[0]
        z = 30.0  # Convert to mm
        init_command = (
            f"G1 X{first_x * 10:.2f} Y{first_y * 10:.2f} Z{z:.2f} F{MOVE_SPEED_BASE}"
        )
        ser.write(f"{init_command}\n".encode())
        logging.debug(f"Moving to initial position: {init_command}")
        wait_for_printer_ready(ser)

        # Perform circular choreography for 30 seconds
        duration = 30
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed_time = time.time() - start_time
            waypoint_index = int((elapsed_time / duration) * WAYPOINTS) % WAYPOINTS
            x, y = waypoints[waypoint_index]
            command = f"G1 X{x * 10:.2f} Y{y * 10:.2f} Z{z:.2f} F{MOVE_SPEED_BASE}"
            ser.write(f"{command}\n".encode())
            logging.debug(f"Executing waypoint {waypoint_index}: {command}")
            wait_for_printer_ready(ser)

        logging.info("Choreography completed.")

    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        ser.close()
        logging.info("Serial connection closed.")


if __name__ == "__main__":
    execute_full_choreography(SERIAL_PORT, BAUD_RATE)
