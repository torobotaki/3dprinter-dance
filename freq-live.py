import serial
import numpy as np
import sounddevice as sd
import logging
import time

# Parameters
SERIAL_PORT = "/dev/tty.usbserial-14520"  # Replace with your printer's serial port
BAUD_RATE = 250000  # Standard baud rate for 3D printers
CYLINDER_RADIUS = 7.5  # Cylinder radius (15 mm diameter)
NUM_LAYERS = 20  # Number of cylinder layers
LAYER_HEIGHT = 0.2  # Height per layer (mm)
GLITCH_SCALE = 0.1  # Modulation scale (10% of cylinder size)
MIN_Z_HEIGHT = 0.2  # Minimum Z height to avoid touching the plate
SAMPLE_RATE = 44100  # Audio sampling rate (Hz)
CHUNK_SIZE = 2048  # Number of audio samples per chunk
SOFT_THRESHOLD = 0.01  # Minimum RMS for sound detection
MOVE_SPEED = 1200  # Speed for X and Y movements (F code in mm/min)

# Logging configuration
logging.basicConfig(filename="printer_debug.log", level=logging.INFO)

# Notes mapping
NOTES = [
    ("C0", 16.35),
    ("C#0/Db0", 17.32),
    ("D0", 18.35),
    ("D#0/Eb0", 19.45),
    ("E0", 20.60),
    ("F0", 21.83),
    ("F#0/Gb0", 23.12),
    ("G0", 24.50),
    ("G#0/Ab0", 25.96),
    ("A0", 27.50),
    ("A#0/Bb0", 29.14),
    ("B0", 30.87),
    ("C1", 32.70),
    ("C#1/Db1", 34.65),
    ("D1", 36.71),
    ("D#1/Eb1", 38.89),
    ("E1", 41.20),
    ("F1", 43.65),
    ("F#1/Gb1", 46.25),
    ("G1", 49.00),
    ("G#1/Ab1", 51.91),
    ("A1", 55.00),
    ("A#1/Bb1", 58.27),
    ("B1", 61.74),
    ("C2", 65.41),
    ("C#2/Db2", 69.30),
    ("D2", 73.42),
    ("D#2/Eb2", 77.78),
    ("E2", 82.41),
    ("F2", 87.31),
    ("F#2/Gb2", 92.50),
    ("G2", 98.00),
    ("G#2/Ab2", 103.83),
    ("A2", 110.00),
    ("A#2/Bb2", 116.54),
    ("B2", 123.47),
    ("C3", 130.81),
    ("C#3/Db3", 138.59),
    ("D3", 146.83),
    ("D#3/Eb3", 155.56),
    ("E3", 164.81),
    ("F3", 174.61),
    ("F#3/Gb3", 185.00),
    ("G3", 196.00),
    ("G#3/Ab3", 207.65),
    ("A3", 220.00),
    ("A#3/Bb3", 233.08),
    ("B3", 246.94),
    ("C4", 261.63),
    ("C#4/Db4", 277.18),
    ("D4", 293.66),
    ("D#4/Eb4", 311.13),
    ("E4", 329.63),
    ("F4", 349.23),
    ("F#4/Gb4", 369.99),
    ("G4", 392.00),
    ("G#4/Ab4", 415.30),
    ("A4", 440.00),
    ("A#4/Bb4", 466.16),
    ("B4", 493.88),
    ("C5", 523.25),
    ("C#5/Db5", 554.37),
    ("D5", 587.33),
    ("D#5/Eb5", 622.25),
    ("E5", 659.25),
    ("F5", 698.46),
    ("F#5/Gb5", 739.99),
    ("G5", 783.99),
    ("G#5/Ab5", 830.61),
    ("A5", 880.00),
    ("A#5/Bb5", 932.33),
    ("B5", 987.77),
    ("C6", 1046.50),
    ("C#6/Db6", 1108.73),
    ("D6", 1174.66),
    ("D#6/Eb6", 1244.51),
    ("E6", 1318.51),
    ("F6", 1396.91),
    ("F#6/Gb6", 1479.98),
    ("G6", 1567.98),
    ("G#6/Ab6", 1661.22),
    ("A6", 1760.00),
    ("A#6/Bb6", 1864.66),
    ("B6", 1975.53),
    # Add further octaves as needed
]


# Function to map frequency to the nearest note
def frequency_to_note(freq):
    """Map a frequency to the nearest musical note."""
    if freq == 0:
        return None  # No frequency detected
    closest_note = min(NOTES, key=lambda note: abs(note[1] - freq))
    return closest_note


# Function to calculate RMS (loudness)
def calculate_rms(samples):
    return float(np.sqrt(np.mean(samples**2)))


# Function to capture real-time audio
def capture_audio():
    """Capture audio and return the dominant frequency and RMS loudness."""
    with sd.InputStream(
        channels=1, samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE
    ) as stream:
        samples, _ = stream.read(CHUNK_SIZE)
        samples = samples.flatten()

        # Calculate RMS loudness
        rms = calculate_rms(samples)

        # Perform FFT to find dominant frequency
        fft = np.fft.fft(samples)
        fft_magnitudes = np.abs(fft[: len(fft) // 2])
        freqs = np.fft.fftfreq(len(fft), 1 / SAMPLE_RATE)[: len(fft) // 2]

        peak_index = np.argmax(fft_magnitudes)
        peak_freq = freqs[peak_index]

        # Map frequency to note
        note = frequency_to_note(peak_freq)
        return note, rms


# Function to wait for the printer's "ok" response
def wait_for_printer_ready(ser):
    """Wait until the printer responds with 'ok' or stops moving."""
    while True:
        response = ser.readline().decode().strip()
        if "ok" in response or "wait" in response:
            logging.info(f"Printer response: {response}")
            ser.flushInput()  # Clear input buffer after "ok"
            break


# Function to send G-code to the printer
def send_gcode_with_glitches(serial_port, baud_rate):
    """
    Capture audio and send G-code to the printer with glitches based on audio.

    Parameters:
    - serial_port: str, serial port for the printer.
    - baud_rate: int, baud rate for the serial connection.
    """
    # Open serial connection
    ser = serial.Serial(serial_port, baud_rate)
    time.sleep(2)  # Wait for the connection to stabilize

    try:
        # Printer initialization
        ser.write(b"G21\n")  # Set units to millimeters
        print("Sending: G21 (Set units to millimeters)")
        wait_for_printer_ready(ser)

        ser.write(b"G90\n")  # Absolute positioning
        print("Sending: G90 (Set absolute positioning)")
        wait_for_printer_ready(ser)

        ser.write(b"M82\n")  # Set extruder to absolute mode
        print("Sending: M82 (Set extruder to absolute mode)")
        wait_for_printer_ready(ser)

        ser.write(b"G28\n")  # Home all axes
        print("Sending: G28 (Home all axes)")
        wait_for_printer_ready(ser)

        #        ser.write(b"M104 S200\n")  # Set extruder temperature to 200°C
        #        print("Sending: M104 S200 (Set extruder temperature)")
        #       wait_for_printer_ready(ser)

        # ser.write(b"M109 S200\n")  # Wait for extruder to reach target temperature
        # print("Sending: M109 S200 (Wait for extruder temperature)")
        # wait_for_printer_ready(ser)

        ser.write(b"G92 E0\n")  # Reset extruder position
        print("Sending: G92 E0 (Reset extruder position)")
        wait_for_printer_ready(ser)

        # Generate G-code based on real-time audio
        for layer_idx in range(NUM_LAYERS):
            z_height = max(layer_idx * LAYER_HEIGHT, MIN_Z_HEIGHT)
            ser.write(
                f"G1 Z{z_height:.2f} F{MOVE_SPEED}\n".encode()
            )  # Move to layer height
            print(f"Sending: G1 Z{z_height:.2f} F{MOVE_SPEED} (Move to layer height)")
            wait_for_printer_ready(ser)

            for angle_idx in range(360):
                # Capture audio for glitch values
                note, rms = capture_audio()
                if note:
                    note_glitch = (int(note[1]) % 10) * GLITCH_SCALE * CYLINDER_RADIUS
                else:
                    note_glitch = 0
                loudness_glitch = rms * GLITCH_SCALE * CYLINDER_RADIUS

                # Calculate base X and Y positions for the cylinder
                angle_rad = np.radians(angle_idx)
                base_x = CYLINDER_RADIUS * np.cos(angle_rad)
                base_y = CYLINDER_RADIUS * np.sin(angle_rad)

                x_pos = base_x + note_glitch
                y_pos = base_y + loudness_glitch

                # Send G-code for the point
                gcode = f"G1 X{x_pos:.2f} Y{y_pos:.2f} F{MOVE_SPEED} E{angle_idx * 0.01:.3f}\n"
                ser.write(gcode.encode())
                print(
                    f"Sending: {gcode.strip()} (Note: {note[0] if note else 'None'}, Loudness: {rms:.2f})"
                )
                wait_for_printer_ready(ser)

        # Printer shutdown commands
        ser.write(b"G28\n")  # Home all axes
        print("Sending: G28 (Home all axes)")
        wait_for_printer_ready(ser)

        ser.write(b"M104 S0\n")  # Turn off extruder heating
        print("Sending: M104 S0 (Turn off extruder heating)")
        wait_for_printer_ready(ser)

        ser.write(b"M140 S0\n")  # Turn off bed heating
        print("Sending: M140 S0 (Turn off bed heating)")
        wait_for_printer_ready(ser)

        ser.write(b"M84\n")  # Disable motors
        print("Sending: M84 (Disable motors)")
        wait_for_printer_ready(ser)

    except KeyboardInterrupt:
        print("\nInterrupted! Closing serial connection.")
    finally:
        ser.close()
        print("Serial connection closed.")


# Send G-code to the printer based on live audio
send_gcode_with_glitches(SERIAL_PORT, BAUD_RATE)
