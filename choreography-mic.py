import serial
import numpy as np
import logging
import time
import sounddevice as sd
import random
import scipy.io.wavfile as wav
from pydub import AudioSegment
import logging

# Logging on the console and a file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console
        logging.FileHandler("printer_debug.log"),  # File
    ],
)


# Parameters
SERIAL_PORT = "/dev/tty.usbserial-1450"  # Replace with your printer's serial port
BAUD_RATE = 250000  # Standard baud rate for 3D printers
CYLINDER_RADIUS = 3.5  # Radius for basic choreography (7 cm diameter)
PLATE_CENTER = (10.5, 10.5)  # Center of the 21x21 cm plate
LAYER_HEIGHT = 10  # Height per layer (mm)
MOVE_SPEED_BASE = 150  # Base speed in mm/min
MOVE_SPEED_MAX = 1000  # Maximum speed in mm/min
WAYPOINTS = 360  # Number of points in the circle
ACK_TIMEOUT = 50  # Timeout for printer acknowledgment in seconds
CHUNK_SIZE = 2048  # Audio chunk size
SAMPLE_RATE = 44100  # Audio sample rate
MAX_RADIUS = 9.0  # Maximum allowed movement radius (18 cm diameter)
PRINTER_POLL_FREQ = 0.5  # frequency of sending movements to the printer. 0.5 works alright in my experiments.


# Frequency mapping to notes
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

# Movement mapping Notes to movements
MOVEMENTS = {
    "A": "x+",
    "B": "x-",
    "C": "y+",
    "D": "y-",
    "E": "z+",
    "F": "z-",
    "G": "xy?",
    "#": "x?",  # Sharp changes X direction randomly
    "b": "y?",  # Flat changes Y direction randomly
}


def wait_for_printer_ready(ser):
    start_time = time.time()
    while True:
        if time.time() - start_time > ACK_TIMEOUT:
            logging.error("Timeout waiting for printer acknowledgment.")
            raise TimeoutError("Printer did not acknowledge within timeout period.")
        response = ser.readline().decode(errors="ignore").strip()
        # logging.debug(f"Printer response: {response}")
        if "ok" in response or "wait" in response:
            ser.flushInput()
            return


def calculate_rms(samples):
    return float(np.sqrt(np.mean(samples**2)))


def normalize_note_with_accidental(note):
    """Extract the base note and accidental (sharp/flat) from the note."""
    if note:
        base_note = note[0]
        accidental = note[1] if len(note) > 1 and note[1] in ["#", "b"] else "natural"
        return base_note, accidental
    return None, None


def audio_from_file(file_path):
    """Read audio from file and process in chunks."""
    try:
        if file_path.endswith(".wav"):
            sample_rate, data = wav.read(file_path)
        elif file_path.endswith(".mp3"):
            audio = AudioSegment.from_mp3(file_path)
            sample_rate = audio.frame_rate
            data = np.array(audio.get_array_of_samples())
        else:
            logging.error("Unsupported file format.")
            return

        if len(data.shape) > 1:  # Convert stereo to mono
            data = data[:, 0]
        total_samples = len(data)
        start = 0

        while start < total_samples:
            end = min(start + CHUNK_SIZE, total_samples)
            chunk = data[start:end]
            start = end
            yield chunk, sample_rate
    except Exception as e:
        logging.error(f"Error reading audio file: {e}")
        raise


def capture_system_audio():
    """Capture audio from the system output using a valid device."""
    try:
        with sd.InputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            device=2,  # Replace 3 with your desired device index
        ) as stream:
            samples, _ = stream.read(CHUNK_SIZE)
            samples = samples.flatten()
            rms = calculate_rms(samples)
            fft = np.fft.fft(samples)
            fft_magnitudes = np.abs(fft[: len(fft) // 2])
            freqs = np.fft.fftfreq(len(fft), 1 / SAMPLE_RATE)[: len(fft) // 2]
            peak_index = np.argmax(fft_magnitudes)
            peak_freq = freqs[peak_index]
            note = (
                min(NOTES, key=lambda x: abs(peak_freq - x[1]))[0]
                if peak_freq > 0
                else None
            )
            return note, rms, peak_freq
    except Exception as e:
        logging.error(f"Error capturing system audio: {e}")
        return None, 0, 0


def capture_audio():
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE
    ) as stream:
        samples, _ = stream.read(CHUNK_SIZE)
        samples = samples.flatten()
        rms = calculate_rms(samples)
        fft = np.fft.fft(samples)
        fft_magnitudes = np.abs(fft[: len(fft) // 2])
        freqs = np.fft.fftfreq(len(fft), 1 / SAMPLE_RATE)[: len(fft) // 2]
        peak_index = np.argmax(fft_magnitudes)
        peak_freq = freqs[peak_index]
        note = (
            min(NOTES, key=lambda x: abs(peak_freq - x[1]))[0]
            if peak_freq > 0
            else None
        )
        normalized_note = normalize_note(note)
        # logging.debug(
        #     f"Captured audio: Frequency={peak_freq:.2f} Hz, Note={note}, Normalized Note={normalized_note}, RMS={rms:.2f}"
        # )
        return normalized_note, rms, peak_freq


def setup_output(live_mode):
    """Initialize the output for live mode or file mode."""
    if live_mode:
        return serial.Serial(SERIAL_PORT, BAUD_RATE)
    else:
        while True:
            file_path = input(
                "Enter G-code output file path (e.g., output.gcode): "
            ).strip()
            if file_path:
                try:
                    return open(file_path, "w")
                except Exception as e:
                    print(f"Error opening file: {e}. Please try again.")
            else:
                print("File path cannot be empty. Please provide a valid file path.")


def send_initial_position(output, x, y, z, live_mode):
    """Send the initial position command to the printer or G-code file."""
    logging.info(f"Initial position set to: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
    command = f"G1 X{x * 10:.2f} Y{y * 10:.2f} Z{z:.2f} F500"
    if live_mode:
        output.write(f"{command}\n".encode())
        wait_for_printer_ready(output)
    else:
        output.write(f"{command}\n")
    logging.debug(f"{'Sending' if live_mode else 'Writing'}: {command}")


def process_movement(output, x, y, z, note, rms, freq, live_mode):
    """Process the movement based on the detected note and RMS."""
    if note:
        logging.debug(f"Detected note: {note}, Frequency={freq:.2f} Hz, RMS={rms:.2f}")
        x, y, z = move_printer(output, x, y, z, note, rms, live_mode)
        if live_mode:
            time.sleep(PRINTER_POLL_FREQ)
    else:
        logging.debug("No note detected. Skipping movement.")
    return x, y, z


def get_audio_source():
    """Prompt the user to select the audio source: microphone, file, or system output."""
    while True:
        source = (
            input("Select audio source ('mic', 'file', 'system'): ").strip().lower()
        )
        if source in ["mic", "file", "system"]:
            return source
        else:
            print("Invalid input. Please enter 'mic', 'file', or 'system'.")


def normalize_note(note):
    """Extract the first character of the note and the accidental (sharp or flat) if present."""
    if note:
        return (
            note[0],
            note[1] if len(note) > 1 and note[1] in ["#", "b"] else "natural",
        )
    return None, None


# Add Z-axis boundaries
MIN_Z = -10  # Minimum Z height (e.g., at the plate level)
MAX_Z = 120  # Maximum Z height (adjust based on your setup)


def move_printer(output, x, y, z, note, rms, live_mode):
    """Processes movements based on note and RMS and sends them to the printer."""
    # Normalize the note to extract the base note and accidental
    base_note, accidental = normalize_note_with_accidental(
        note
    )  # Updated function to include accidentals

    # Initialize movement variables
    dx, dy, dz = 0, 0, 0

    # Base note movements
    if base_note in MOVEMENTS:
        commands = MOVEMENTS[base_note].split()
        for cmd in commands:
            dx += {"x+": 1, "x-": -1, "y+": 0, "y-": 0}.get(cmd, 0)
            dy += {"y+": 1, "y-": -1, "x+": 0, "x-": 0}.get(cmd, 0)
            dz += {"z+": 1, "z-": -1}.get(cmd, 0)

    # Accidental movements
    if accidental in MOVEMENTS:
        commands = MOVEMENTS[accidental].split()
        for cmd in commands:
            dx += {"x?": random.choice([-1, 1])}.get(cmd, 0)
            dy += {"y?": random.choice([-1, 1])}.get(cmd, 0)

    # Scale movements
    rms_scale = max(MOVE_SPEED_BASE, min(rms * MOVE_SPEED_MAX, MOVE_SPEED_MAX))
    dx *= rms_scale * 0.1  # Convert to cm
    dy *= rms_scale * 0.1
    dz *= LAYER_HEIGHT

    # Calculate new position
    new_x, new_y, new_z = x + dx, y + dy, z + dz

    # Enforce boundaries
    distance_from_center = np.sqrt(
        (new_x - PLATE_CENTER[0]) ** 2 + (new_y - PLATE_CENTER[1]) ** 2
    )
    if distance_from_center > MAX_RADIUS:
        logging.warning(
            f"Movement out of bounds. Adjusting to max radius. Attempted: X={new_x}, Y={new_y}, Z={new_z}"
        )
        angle = np.arctan2(new_y - PLATE_CENTER[1], new_x - PLATE_CENTER[0])
        new_x = PLATE_CENTER[0] + MAX_RADIUS * np.cos(angle)
        new_y = PLATE_CENTER[1] + MAX_RADIUS * np.sin(angle)

    if new_z < MIN_Z:
        new_z = MIN_Z
    elif new_z > MAX_Z:
        new_z = MAX_Z

    # Send G-code command
    command = f"G1 X{new_x * 10:.2f} Y{new_y * 10:.2f} Z{new_z:.2f} F{rms_scale}"
    if live_mode:
        output.write(f"{command}\n".encode())
    else:
        output.write(f"{command}\n")

    logging.info(
        f"Note: {note}, RMS: {rms:.2f}, Movement: dx={dx:.2f} cm, dy={dy:.2f} cm, dz={dz:.2f} cm. "
        f"New Position: X={new_x:.2f}, Y={new_y:.2f}, Z={new_z:.2f}"
    )
    if live_mode:
        wait_for_printer_ready(output)

    return new_x, new_y, new_z


def execute_choreography_with_audio(live_mode, source="mic", file_path=None):
    try:
        logging.info("Starting printer initialization.")

        # Printer setup
        output = setup_output(live_mode)

        # Set initial position
        x, y, z = PLATE_CENTER[0], PLATE_CENTER[1], 10.0
        send_initial_position(output, x, y, z, live_mode)

        # Audio source logic
        if source == "mic":
            while True:
                note, rms, freq = capture_audio()
                process_movement(output, x, y, z, note, rms, freq, live_mode)
        elif source == "file" and file_path:
            for chunk, sample_rate in audio_from_file(file_path):
                note, rms, freq = capture_audio_from_file(chunk, sample_rate)
                process_movement(output, x, y, z, note, rms, freq, live_mode)
        elif source == "system":
            while True:
                note, rms, freq = capture_system_audio()
                process_movement(output, x, y, z, note, rms, freq, live_mode)
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        output.close()
        logging.info("Execution finished.")


if __name__ == "__main__":
    mode = (
        input("Enter mode ('live' for printer, 'file' for G-code file): ")
        .strip()
        .lower()
    )

    if mode not in ["live", "file"]:
        print("Invalid mode. Please enter 'live' or 'file'.")
        exit()

    audio_source = (
        input(
            "Select audio source ('mic' for microphone, 'file' for audio file, 'system' for system output): "
        )
        .strip()
        .lower()
    )

    if audio_source not in ["mic", "file", "system"]:
        print("Invalid audio source. Please enter 'mic', 'file', or 'system'.")
        exit()

    if audio_source == "file":
        file_path = input("Enter audio file path (e.g., song.wav): ").strip()
        if not file_path:
            print("Audio file path cannot be empty.")
            exit()
        execute_choreography_with_audio(
            live_mode=(mode == "live"), source=audio_source, file_path=file_path
        )
    else:
        execute_choreography_with_audio(live_mode=(mode == "live"), source=audio_source)
