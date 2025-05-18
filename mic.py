import sounddevice as sd
import numpy as np
import time

# Parameters
CHUNK = 1024  # Number of samples per frame
RATE = 44100  # Sampling rate (Hz)
MIN_VOLUME_THRESHOLD = (
    0.01  # Minimum volume to detect "sound" (adjusted for normalization)
)
BASE_DELAY = 0.5  # Base delay between dots in seconds
VOLUME_SCALING = 5  # Scaling factor for volume-based delay adjustment


def audio_callback(indata, frames, time_info, status):
    global prev_volume
    # Check for silence or invalid data
    if not np.any(indata):  # If all input data is zero (silent input)
        return

    # Convert audio data to a NumPy array
    samples = indata[:, 0]  # Use the first channel (mono audio)
    # Calculate the root mean square (RMS) volume
    rms = np.sqrt(np.mean(samples**2))

    # Avoid errors by checking for valid values
    if np.isnan(rms) or rms <= 0:
        return

    # Calculate the change in volume to model rhythm
    volume_change = abs(rms - prev_volume)
    prev_volume = rms

    # If volume is above the threshold, output a dot
    if rms > MIN_VOLUME_THRESHOLD:
        # Calculate delay based on volume and rhythm
        delay = BASE_DELAY - (rms * VOLUME_SCALING) - (volume_change * 0.1)
        delay = max(0.1, delay)  # Ensure a minimum delay for usability
        print(".", end="", flush=True)
        time.sleep(delay)


# Global variable to track previous volume
prev_volume = 0

print("Listening and outputting dots... (Ctrl+C to stop)")
try:
    with sd.InputStream(
        channels=1, callback=audio_callback, samplerate=RATE, blocksize=CHUNK
    ):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopping...")
