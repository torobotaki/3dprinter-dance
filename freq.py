import sounddevice as sd
import numpy as np
import time

# Parameters
RATE = 44100  # Sampling rate (Hz)
CHUNK = 2048  # Number of samples per frame
DEVICE_INDEX = 0  # Your microphone device index
SOFT_THRESHOLD = 0.01  # Threshold for soft sounds

# Note frequency mapping
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
    # Add more octaves as needed
]


def frequency_to_note(freq):
    """Map a frequency to the nearest musical note."""
    if freq == 0:
        return None  # No frequency detected
    closest_note = min(NOTES, key=lambda note: abs(note[1] - freq))
    return closest_note[0]


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    # Convert audio data to a NumPy array
    samples = indata[:, 0]
    # Calculate RMS volume
    rms = float(np.sqrt(np.mean(samples**2)))  # Convert RMS to native Python float

    if rms > SOFT_THRESHOLD:  # If sound is above the threshold
        # Perform FFT to get frequency spectrum
        fft = np.fft.fft(samples)
        fft_magnitudes = np.abs(fft[: len(fft) // 2])  # Take the positive frequencies
        freqs = np.fft.fftfreq(len(fft), 1 / RATE)[: len(fft) // 2]

        # Find the peak frequency
        peak_index = np.argmax(fft_magnitudes)
        peak_freq = freqs[peak_index]

        # Map the frequency to the nearest musical note
        note = frequency_to_note(peak_freq)

        # Output the detected note
        if note:
            print(f"Detected Note: {note} ({peak_freq:.2f} Hz)", flush=True)
        else:
            print(f"Undetectable Frequency: {peak_freq:.2f} Hz", flush=True)


print("Listening and detecting musical notes... (Ctrl+C to stop)")
try:
    with sd.InputStream(
        device=DEVICE_INDEX,
        channels=1,
        samplerate=RATE,
        blocksize=CHUNK,
        callback=audio_callback,
    ):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopping...")
