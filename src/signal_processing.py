import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq

    b, a = butter(
        order,
        normal_cutoff,
        btype="low",
        analog=False,
    )

    return b, a


def smooth_force_signal(force, dt, cutoff_hz=2000):
    fs = 1.0 / dt
    b, a = butter_lowpass(cutoff_hz, fs)

    return filtfilt(b, a, force)


def detect_peaks(force, dt, height_threshold=0.1):
    threshold = height_threshold * np.max(force)
    min_dist = int(0.001 / dt)

    peaks, props = find_peaks(
        force,
        height=threshold,
        distance=min_dist,
    )

    return peaks, props


def compute_trapezoid(y, x):
    """
    Compatible trapezoidal integration.

    np.trapezoid is available in newer NumPy versions.
    np.trapz works in older NumPy versions.
    """
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)

    return np.trapz(y, x)


def compute_impulse(force, t):
    return compute_trapezoid(force, t)


def compute_rise_time(force, t, low_frac=0.1, high_frac=0.9):
    peak_idx = np.argmax(force)
    peak_val = force[peak_idx]

    low_val = low_frac * peak_val
    high_val = high_frac * peak_val

    low_idx = np.searchsorted(force[:peak_idx], low_val)
    high_idx = np.searchsorted(force[:peak_idx], high_val)

    if high_idx <= low_idx:
        return np.nan

    return t[high_idx] - t[low_idx]


def segment_active_region(force, threshold_frac=0.05):
    threshold = threshold_frac * np.max(force)
    indices = np.where(force > threshold)[0]

    if len(indices) == 0:
        return 0, len(force)

    return indices[0], indices[-1]