import numpy as np
from scipy import signal as sig
from scipy.signal import find_peaks

from ekg_testbench import EKGTestBench


def detect_heartbeats(filepath):
    """
    Perform analysis to detect location of heartbeats.
    :param filepath: A valid path to a CSV file of heartbeats
    :return: processed_signal: the signal used for peak detection
    beats: the indices of detected heartbeats
    """
    if filepath == '':
        return [], []

    try:
        data = np.genfromtxt(filepath, delimiter=',', skip_header=2)
    except OSError:
        return [], []

    if data.size == 0:
        return [], []

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.shape[1] < 2:
        return [], []

    signal = data[:, 1].astype(float)
    signal = signal - np.mean(signal)

    sample_rate = 300.0
    low_pass = sig.butter(4, 15 / (sample_rate / 2.0), btype='low', output='ba')
    low_filtered = sig.filtfilt(low_pass[0], low_pass[1], signal)

    high_pass = sig.butter(4, 0.5 / (sample_rate / 2.0), btype='high', output='ba')
    band_pass = sig.filtfilt(high_pass[0], high_pass[1], low_filtered)

    derivative = np.diff(band_pass, prepend=band_pass[0])
    squared = derivative ** 2

    window_size = int(round(0.15 * sample_rate))
    if window_size < 1:
        window_size = 1

    moving_average = np.convolve(squared, np.ones(window_size) / window_size, mode='same')

    peak_threshold = np.max(moving_average) * 0.20
    peaks, _ = find_peaks(
        moving_average,
        distance=int(round(0.35 * sample_rate)),
        prominence=peak_threshold,
    )

    return moving_average, peaks


# when running this file directly, this will execute first
if __name__ == "__main__":

    # place here so doesn't cause import error
    import matplotlib.pyplot as plt

    # database name
    database_name = 'mitdb_201'

    # set to true if you wish to generate a debug file
    file_debug = False

    # set to true if you wish to print overall stats to the screen
    print_debug = True

    # set to true if you wish to show a plot of each detection process
    show_plot = False

    ### DO NOT MODIFY BELOW THIS LINE!!! ###

    # path to ekg folder
    path_to_folder = "../../../data/ekg/"

    # select a signal file to run
    signal_filepath = path_to_folder + database_name + ".csv"

    # call main() and run against the file. Should return the filtered
    # signal and identified peaks
    (signal, peaks) = detect_heartbeats(signal_filepath)

    # stop with a clear message if detect_heartbeats() is not finished yet
    if peaks is None:
        raise SystemExit("detect_heartbeats() returned None for beats. Finish the steps above and return the peak indices.")

    # matched is a list of (peak, annotation) pairs; unmatched is a list of peaks that were
    # not matched to any annotation; and remaining is annotations that were not matched.
    annotation_path = path_to_folder + database_name + "_annotations.txt"
    tb = EKGTestBench(annotation_path)
    peaks_list = peaks.tolist()
    (matched, unmatched, remaining) = tb.generate_stats(peaks_list)

    # if was matched, then is true positive
    true_positive = len(matched)

    # if response was unmatched, then is false positive
    false_positive = len(unmatched)

    # whatever remains in annotations is a missed detection
    false_negative = len(remaining)

    # calculate f1 score
    f1 = true_positive / (true_positive + 0.5 * (false_positive + false_negative))

    # if we wish to show the resulting plot
    if show_plot:
        # make a nice plt of results
        plt.title('Signal for ' + database_name + " with detections")

        plt.plot(signal, label="Filtered Signal")
        plt.plot(peaks, signal[peaks], 'p', label='Detected Peaks')

        true_annotations = np.asarray(tb.annotation_indices)
        plt.plot(true_annotations, signal[true_annotations], 'o', label='True Annotations')

        plt.legend()

        # uncomment line to show the plot
        plt.show()

    # if we wish to save all the stats to a file
    if file_debug:
        # print out more complex stats to the debug file
        debug_file_path = database_name + "_debug_stats.txt"
        debug_file = open(debug_file_path, 'w')

        # print out indices of all false positives
        debug_file.writelines("-----False Positives Indices-----\n")
        for fp in unmatched:
            debug_file.writelines(str(fp) + "\n")

        # print out indices of all false negatives
        debug_file.writelines("-----False Negatives Indices-----\n")
        for fn in remaining:
            debug_file.writelines(str(fn.sample) + "\n")

        # close file that we writing
        debug_file.close()

    if print_debug:
        print("-------------------------------------------------")
        print("Database|\t\tTP|\t\tFP|\t\tFN|\t\tF1")
        print(database_name, "|\t\t", true_positive, "|\t", false_positive, '|\t', false_negative, '|\t', round(f1, 3))
        print("-------------------------------------------------")

    print("Done!")
