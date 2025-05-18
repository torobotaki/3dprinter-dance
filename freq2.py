import sounddevice as sd
import numpy as np
from scipy.signal import butter, lfilter
import time

# Parameters
RATE = 44100  # Sampling rate (Hz)
CHUNK = 2048  # Number of samples per frame
DEVICE_INDEX = 0  # Your microphone device index
SOFT_THRESHOLD = 0.01  # Minimum threshold for sound detection
SAMPLING_INTERVAL = 0.5  # Sampling every 0.5 seconds

# Extended notes table
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


# High-pass filter to remove low-frequency noise
def high_pass_filter(data, cutoff=50, fs=44100, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="high", analog=False)
    return lfilter(b, a, data)


def frequency_to_note(freq):
    """Map a frequency to the nearest musical note."""
    if freq == 0:
        return None  # No frequency detected
    closest_note = min(NOTES, key=lambda note: abs(note[1] - freq))
    return closest_note


def categorize_loudness(rms):
    """Categorize loudness based on RMS value."""
    if rms < 0.025:
        return "softest"
    elif rms < 0.05:
        return "soft"
    elif rms < 0.075:
        return "neutral"
    elif rms <= 0.1:
        return "loud"
    else:
        return "LOUDER"


print("Listening for sound and detecting loudness... (Ctrl+C to stop)")
try:
    with sd.InputStream(
        device=DEVICE_INDEX, channels=1, samplerate=RATE, blocksize=CHUNK
    ) as stream:
        while True:
            # Record a chunk of audio
            samples, _ = stream.read(CHUNK)
            samples = samples.flatten()  # Convert to 1D array

            # Apply a high-pass filter to remove low-frequency noise
            samples = high_pass_filter(samples, cutoff=50, fs=RATE)

            # Calculate RMS volume
            rms = float(
                np.sqrt(np.mean(samples**2))
            )  # Convert RMS to native Python float

            # Categorize and print loudness
            loudness = categorize_loudness(rms)
            print(f"Loudness: {loudness} (RMS: {rms:.2f})")

            # Perform FFT to get frequency spectrum
            fft = np.fft.fft(samples)
            fft_magnitudes = np.abs(
                fft[: len(fft) // 2]
            )  # Take the positive frequencies
            freqs = np.fft.fftfreq(len(fft), 1 / RATE)[: len(fft) // 2]

            # Find the peak frequency
            valid_freqs = freqs[freqs > 50]  # Ignore low frequencies
            valid_magnitudes = fft_magnitudes[freqs > 50]

            if len(valid_magnitudes) > 0:
                peak_index = np.argmax(valid_magnitudes)
                peak_freq = valid_freqs[peak_index]
                note = frequency_to_note(peak_freq)

                if note:
                    print(f"Detected Note: {note[0]} ({peak_freq:.2f} Hz)")
                else:
                    print(f"Detected Frequency: {peak_freq:.2f} Hz")

            # Wait for the next sampling interval
            time.sleep(SAMPLING_INTERVAL)
except KeyboardInterrupt:
    print("\nStopping...")
