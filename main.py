import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import iirnotch, filtfilt, butter
from tkinter import Tk, filedialog
from pathlib import Path
import windaq as wdq

# Helper Functions
def select_folder_and_find_files(extension=".WDH"):
    """
    Prompts the user to select a folder and retrieves all files with the specified extension.
    """
    root = Tk()
    root.withdraw()  # Hide Tkinter root window
    folder_path = filedialog.askdirectory(title="Select a Folder")
    if not folder_path:
        print("No folder selected.")
        return []
    
    matching_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(extension):
                matching_files.append(os.path.join(root_dir, file))
    return matching_files


def wdh_to_df(file):
    """
    Converts a Windaq file to a DataFrame with specific columns.
    """
    wfile = wdq.windaq(file)
    return pd.DataFrame({
        'time, s': wfile.time(),
        'speed, rpm': wfile.data(3),
        'torque, Nm': wfile.data(1),
        'temp, degF': wfile.data(2)
    })


# Plotting Functions
def plot_filter_torque_stand_data(df, test_name, start_time=0, stop_time=0):
    """
    Plots speed, torque, and filtered torque data with legends and minor gridlines.
    """
    # Filter the dataframe for the specified time range
    df_plot = df[(df['time, s'] >= start_time) & (df['time, s'] <= stop_time)] if stop_time else df

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)

    # Plot Speed
    ax1.plot(df_plot['time, s'], df_plot['speed, rpm'], label='Speed', color="red")
    ax1.set_ylim(0, 2000)
    ax1.set_ylabel("Speed, rpm", color="red")
    ax1.grid(which='major', linestyle='-', linewidth=0.75, alpha=0.7)
    ax1.grid(which='minor', linestyle='--', linewidth=0.5, alpha=0.5)
    ax1.legend(loc="upper left")
    ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))

    # Plot Torque
    ax2.plot(df_plot['time, s'], df_plot['torque, Nm'], label='Original Torque', color="red")
    ax2.plot(df_plot['time, s'], df_plot['torque, Nm (filtered)'], label='Filtered Torque', color="blue")
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_ylabel("Torque, Nm")
    ax2.set_xlabel("Time, sec")
    ax2.grid(which='major', linestyle='-', linewidth=0.75, alpha=0.7)
    ax2.grid(which='minor', linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.legend(loc="upper left")
    ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))

    # Make the gridline at y=0 fully black
    ax2.axhline(0.0, color='grey', linewidth=0.75, linestyle='-')  # Custom line at y=0

    # Add Temperature on Secondary Y-Axis
    ax_temp = ax2.twinx()
    ax_temp.plot(df_plot['time, s'], df_plot['temp, degF'], label='Temperature', color="green", alpha=0.3)
    ax_temp.set_ylim(70, 200)
    ax_temp.set_ylabel("Temperature, degF", color="green")
    ax_temp.legend(loc="upper right")

    # Final layout adjustments
    plt.tight_layout()
    return plt


# Signal Processing Functions
def analyze_fft(df, column, sampling_rate, start_time=None, stop_time=None, sort_by_magnitude=False):
    """
    Performs FFT analysis on a specified column of the dataframe.
    """
    # Filter by time range
    if start_time or stop_time:
        df = df[(df['time, s'] >= (start_time if start_time else df['time, s'].min())) & 
                (df['time, s'] <= (stop_time if stop_time else df['time, s'].max()))]

    # Perform FFT
    data = df[column] - df[column].mean()  # Remove DC offset
    fft_result = np.fft.fft(data)
    fft_magnitude = np.abs(fft_result)[:len(data) // 2]
    fft_freqs = np.fft.fftfreq(len(data), d=1/sampling_rate)[:len(data) // 2]

    if sort_by_magnitude:
        sorted_indices = np.argsort(fft_magnitude)[::-1]
        fft_freqs = fft_freqs[sorted_indices]
        fft_magnitude = fft_magnitude[sorted_indices]

    return fft_freqs, fft_magnitude


def lowpass_filter(data, sampling_rate, cutoff_freq, order=4):
    """
    Applies a low-pass filter to the data.
    """
    nyquist = 0.5 * sampling_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)


# Main Script
if __name__ == "__main__":
    # File Selection and Loading
    file_paths = select_folder_and_find_files()
    
    if not file_paths:
        print("No files selected. Exiting.")
        exit()

    # Extract the folder path from the first file
    selected_folder = os.path.dirname(file_paths[0])
    print(f"Saving plots in folder: {selected_folder}")

    # Load files into data_files dictionary
    data_files = {os.path.splitext(os.path.basename(path))[0]: wdh_to_df(path) for path in file_paths}

    # Analysis and Filtering
    lowpass_cutoff = 0.5  # Example cutoff frequency
    for test in data_files:
        print(f"Processing: {test}")
        
        # Apply Low-Pass Filter
        data_files[test]['torque, Nm (filtered)'] = lowpass_filter(
            data=data_files[test]['torque, Nm'],
            sampling_rate=100,
            cutoff_freq=lowpass_cutoff
        )
        
        # Plot Filtered Data
        plt = plot_filter_torque_stand_data(data_files[test], test_name=test, start_time=0, stop_time=675)
        
        # Save the plot in the same folder
        plot_file_path = os.path.join(selected_folder, f"{test}_filtered_plot.png")
        plt.savefig(plot_file_path)
        print(f"Plot saved to: {plot_file_path}")
        plt.close()  # Close the figure to free memory

        # FFT Analysis (optional)
        FFT_Analysis = False
        if FFT_Analysis:
            freqs, magnitudes = analyze_fft(data_files[test], "torque, Nm", sampling_rate=100, sort_by_magnitude=True)
            print("Top Frequencies:")
            for freq, mag in zip(freqs[:10], magnitudes[:10]):
                print(f"Frequency: {freq:.2f} Hz, Magnitude: {mag:.2f}")