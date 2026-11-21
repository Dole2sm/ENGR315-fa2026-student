"""
Musical-note detection for the Module 6 assignment.

Run this file to analyze every Guitar-note-*.wav file in data/musical-notes.
The default run also creates Task 1 and Task 2 plots for Guitar-note-1.wav.
"""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.io import wavfile


# make path not dependent on current directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_DIR = SCRIPT_DIR.parents[1]
AUDIO_DIR = REPOSITORY_DIR / "data" / "musical-notes"
REFERENCE_FILE = AUDIO_DIR / "note-frequencies-reference.csv"
OUTPUT_DIR = SCRIPT_DIR / "assignment_results"


def load_note_reference(reference_file):
    """Read note names and frequencies from the provided two-header CSV."""
    notes = []
    with reference_file.open(newline="", encoding="utf-8-sig") as file:
        rows = csv.reader(file)
        next(rows, None)  # skip descriptive header row
        next(rows, None)  # skip the column name row
        for row in rows:
            if len(row) >= 2 and row[0].strip():
                notes.append((row[0].strip(), float(row[1])))

    if not notes:
        raise ValueError(f"No note frequencies were found in {reference_file}.")
    return notes


def read_audio(audio_file):
    """Read a WAV file, combine stereo channels if present, and remove DC offset."""
    sample_rate, samples = wavfile.read(str(audio_file))
    samples = np.asarray(samples, dtype=float)

    if samples.ndim == 2:
        mono = samples.mean(axis=1)
    elif samples.ndim == 1:
        mono = samples
    else:
        raise ValueError(f"Unsupported audio shape in {audio_file}: {samples.shape}")

    if mono.size < 3:
        raise ValueError(f"The audio file is too short to analyze: {audio_file}")

    # remove DC offset to avoid biasing the autocorrelation
    mono = mono - np.mean(mono)
    return sample_rate, mono


def low_pass_filter(samples, sample_rate):
    """Keep note fundamentals while reducing higher-frequency harmonics."""
    nyquist = sample_rate / 2
    cutoff = min(5000.0, nyquist * 0.9)
    if cutoff <= 0:
        raise ValueError(f"Invalid sample rate: {sample_rate}")

    coefficients = signal.butter(
        4, cutoff, btype="lowpass", fs=sample_rate, output="sos"
    )
    return signal.sosfiltfilt(coefficients, samples)


def estimate_frame_frequency(frame, sample_rate, min_frequency, max_frequency):
    """Find a frame's fundamental from the first strong autocorrelation peak."""
    frame = frame - np.mean(frame)
    frame_length = len(frame)
    correlation = signal.fftconvolve(
        frame, frame[::-1], mode="full"
    )[frame_length - 1 :]

    # normalize each lag by the energy in the samples that overlap at that lag
    prefix_energy = np.concatenate(([0.0], np.cumsum(frame * frame)))
    lags = np.arange(frame_length)
    left_energy = prefix_energy[frame_length - lags]
    right_energy = prefix_energy[frame_length] - prefix_energy[lags]
    denominator = np.sqrt(left_energy * right_energy)
    normalized = np.divide(
        correlation,
        denominator,
        out=np.zeros_like(correlation),
        where=denominator > 0,
    )

    first_lag = max(1, int(np.ceil(sample_rate / max_frequency)))
    last_lag = min(
        frame_length - 2, int(np.floor(sample_rate / min_frequency))
    )
    if first_lag > last_lag:
        raise ValueError("The audio frame is too short for the reference frequency range.")

    peaks, _ = signal.find_peaks(normalized[first_lag : last_lag + 1])
    peaks += first_lag
    if peaks.size:
        # true cycle repeats before its longer-period multiples
        # use the earliest peak that is still close in strength to the strongest peak
        strongest = np.max(normalized[peaks])
        strong_peaks = peaks[normalized[peaks] >= 0.8 * strongest]
        best_lag = int(strong_peaks[0])
    else:
        best_lag = first_lag + int(
            np.argmax(normalized[first_lag : last_lag + 1])
        )

    # parabolic interpolation around the peak estimates a fractional-sample lag
    left, center, right = normalized[best_lag - 1 : best_lag + 2]
    curvature = left - 2 * center + right
    offset = 0.0 if curvature == 0 else 0.5 * (left - right) / curvature
    return sample_rate / (best_lag + offset)


def detect_frequency(filtered, sample_rate, notes):
    """Estimate pitch in several central frames and take the median."""
    note_frequencies = [frequency for _, frequency in notes]
    frame_length = min(int(0.35 * sample_rate), len(filtered))
    if frame_length < 3:
        raise ValueError("The audio is too short for pitch detection.")

    first_start = int(0.2 * len(filtered))
    final_start = min(int(0.8 * len(filtered)), len(filtered) - frame_length)
    hop = max(1, int(0.15 * sample_rate))
    starts = list(range(first_start, final_start + 1, hop))
    if not starts:
        starts = [max(0, (len(filtered) - frame_length) // 2)]

    estimates = []
    for start in starts:
        frame = filtered[start : start + frame_length]
        estimates.append(
            estimate_frame_frequency(
                frame,
                sample_rate,
                min(note_frequencies),
                max(note_frequencies),
            )
        )
    return float(np.median(estimates))


def find_nearest_note(frequency, notes):
    """Return the reference note closest in equal-tempered pitch distance."""
    return min(
        notes,
        key=lambda item: abs(1200 * np.log2(frequency / item[1])),
    )


def create_plots(audio_file, sample_rate, original, filtered, frequency, note):
    """Save a full-recording plot and a five-period original/filtered comparison."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    time = np.arange(len(original)) / sample_rate
    safe_name = audio_file.stem

    figure, axis = plt.subplots(figsize=(10, 4))
    axis.plot(time, original, label="Original audio")
    axis.set_title(f"Audio Signal Over Time: {audio_file.name}")
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Amplitude (ADC counts)")
    axis.legend()
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / f"{safe_name}_full_signal.png", dpi=160)
    plt.close(figure)

    # show several periods from the steady part of the recording
    zoom_duration = min(5 / frequency, time[-1])
    zoom_start = min(0.3 * time[-1], max(0.0, time[-1] - zoom_duration))
    first_sample = int(zoom_start * sample_rate)
    last_sample = min(
        len(original), first_sample + max(2, int(zoom_duration * sample_rate))
    )

    figure, axis = plt.subplots(figsize=(10, 4))
    axis.plot(time[first_sample:last_sample], original[first_sample:last_sample],
              label="Original (DC removed)", alpha=0.75)
    axis.plot(time[first_sample:last_sample], filtered[first_sample:last_sample],
              label="Low-pass filtered", linewidth=1.5)
    axis.set_title(
        f"Five Periods for {audio_file.name}: "
        f"{frequency:.2f} Hz ({note})"
    )
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Amplitude (ADC counts)")
    axis.legend()
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / f"{safe_name}_five_periods.png", dpi=160)
    plt.close(figure)


def resolve_audio_argument(argument):
    """Resolve a file name or path relative to the assignment or data directory."""
    requested = Path(argument)
    if requested.is_absolute():
        return requested

    for base in (AUDIO_DIR, REPOSITORY_DIR, SCRIPT_DIR):
        candidate = base / requested
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find audio file: {argument}")


def main():
    parser = argparse.ArgumentParser(
        description="Detect notes in the supplied guitar WAV recordings."
    )
    parser.add_argument(
        "--plot-file",
        help="Audio file for the Task 1 and Task 2 plots; defaults to Guitar-note-1.wav.",
    )
    arguments = parser.parse_args()

    notes = load_note_reference(REFERENCE_FILE)
    if arguments.plot_file:
        plot_file = resolve_audio_argument(arguments.plot_file)
    else:
        plot_file = AUDIO_DIR / "Guitar-note-1.wav"

    if not plot_file.is_file():
        raise FileNotFoundError(f"Could not find plot audio file: {plot_file}")

    audio_files = sorted(AUDIO_DIR.glob("Guitar-note-*.wav"))
    if not audio_files:
        raise FileNotFoundError(f"No Guitar-note-*.wav files found in {AUDIO_DIR}.")
    if plot_file not in audio_files:
        audio_files.append(plot_file)
        audio_files.sort()

    results = []
    for audio_file in audio_files:
        sample_rate, original = read_audio(audio_file)
        filtered = low_pass_filter(original, sample_rate)
        frequency = detect_frequency(filtered, sample_rate, notes)
        note_name, reference_frequency = find_nearest_note(frequency, notes)
        results.append((audio_file.name, frequency, note_name, reference_frequency))

        if audio_file.resolve() == plot_file.resolve():
            create_plots(
                audio_file, sample_rate, original, filtered, frequency, note_name
            )

    print(f"{'File name':<24} {'Detected frequency (Hz)':>24}  {'Note':<6}")
    print("-" * 58)
    for filename, frequency, note_name, _ in results:
        print(f"{filename:<24} {frequency:>24.2f}  {note_name:<6}")
    print(f"\nTask 1 and Task 2 plots saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
