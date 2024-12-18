import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import windaq as wdq

from scipy.signal import filtfilt, butter
from tkinter import Tk, filedialog
from collections import defaultdict

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

def determine_test_start(df, speed_threshold=1):
    """
    Determines the start point of the test based on speed exceeding a threshold.
    """
    start_index = df[df['speed, rpm'] > speed_threshold].index.min()
    if pd.isna(start_index):
        print("No test start detected.")
        return None
    start_time = df.loc[start_index, 'time, s']
    print(f"Test start detected at time: {start_time} seconds")
    return start_time

def evaluate_torque_at_stages(df, torque_steps):
    """
    Calculates the average filtered torque for specified torque steps.

    Parameters:
    - df: DataFrame containing test data.
    - torque_steps: List of dictionaries with 'start_time' and 'duration'.

    Returns:
    - A dictionary with step names and corresponding average filtered torque.
    """
    results = {}
    for step in torque_steps:
        step_start_time = step['start_time']
        step_end_time = step_start_time + step['duration']
        
        # Filter data within the step time range
        step_data = df[(df['time, s'] >= step_start_time) & (df['time, s'] <= step_end_time)]
        
        # Calculate average of filtered torque
        avg_torque = step_data['torque, Nm (filtered)'].mean()
        results[step['name']] = avg_torque
        
        print(f"{step['name']} avg torque: {avg_torque:.3f} Nm")
    return results

def plot_filter_torque_stand_data(df, test_name, start_time=0, duration=0):
    """
    Plots speed, torque, and filtered torque data with legends and minor gridlines.
    """
    if duration:
        stop_time = start_time + duration
    else:
        stop_time = 0
    # Filter the dataframe for the specified time range
    df_plot = df[(df['time, s'] >= start_time) & (df['time, s'] <= stop_time)] if stop_time else df

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(test_name, fontsize=16, y=0.99)

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
    plt.tight_layout(rect=[0, 0, 1, 0.99])  # Adjust top margin to fit the title
    return plt

def plot_speed_vs_torque(sweep_data, output_path):
    """
    Plots combined speed vs filtered torque for sweep data.

    Parameters:
    - sweep_data: Combined DataFrame containing speed and filtered torque for all sweeps.
    - output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(sweep_data["speed, rpm"], sweep_data["torque, Nm (filtered)"], label="Combined Sweeps")
    plt.title("Speed vs Filtered Torque (Combined)")
    plt.xlabel("Speed (RPM)")
    plt.ylabel("Filtered Torque (Nm)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Combined Speed vs Torque plot saved to: {output_path}")

def plot_speed_vs_torque_multiple_tests(data_files, output_path):
    """
    Plots speed vs filtered torque for multiple tests on the same plot.
    Speeds are assumed to have proper directionality (positive for CW, negative for CCW).
    
    Parameters:
    - data_files: Dictionary of DataFrames with test names as keys.
    - output_path: Path to save the combined plot.
    """
    plt.figure(figsize=(12, 8))

    for test_name, df in data_files.items():
        plt.plot(df['speed, rpm'], df['torque, Nm (filtered)'], label=test_name)

    plt.xlim(-2000, 2000)
    plt.title("Speed vs Filtered Torque for All Tests")
    plt.xlabel("Speed (RPM)")
    plt.ylabel("Filtered Torque (Nm)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Combined Speed vs Torque plot saved to: {output_path}")

def extract_and_combine_sweeps(df, test_steps):
    """
    Extracts all sweeps (CW and CCW) from the DataFrame and combines them.

    Parameters:
    - df: DataFrame containing the test data.
    - test_steps: List of test step definitions.
    - start_time: Time when the test starts.

    Returns:
    - A combined DataFrame containing speed and filtered torque for all sweeps.
    """
    combined_sweeps = pd.DataFrame()

    for step in test_steps:
        step_start_time = step['start_time']  # Align step times to detected start
        step_end_time = step_start_time + step['duration']
        print(f"Extracting {step['name']} from {step_start_time}s to {step_end_time}s")

        # Extract data for this sweep step
        sweep_data = df[(df['time, s'] >= step_start_time) & (df['time, s'] <= step_end_time)].copy()

        # Adjust speed for CCW sweeps
        if step['direction'] == "CCW":
            sweep_data["speed, rpm"] = -sweep_data["speed, rpm"]

        combined_sweeps = pd.concat([combined_sweeps, sweep_data], ignore_index=True)

    return combined_sweeps

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

def save_torque_averages_to_excel(all_torque_averages, file_path):
    """
    Saves torque averages from all tests to an Excel file.

    Parameters:
    - all_torque_averages: Dictionary of test names with torque averages for steps.
    - output_path: Path to save the Excel file.
    """
    # Convert the nested dictionary into a structured DataFrame
    rows = []
    for test_name, step_averages in all_torque_averages.items():
        for step_name, avg_torque in step_averages.items():
            rows.append({"Test Name": test_name, "Step Name": step_name, "Avg Torque (Nm)": avg_torque})
    
    df = pd.DataFrame(rows)
    df.to_excel(file_path, index=False, engine="xlsxwriter")
    print(f"Torque averages saved to Excel file: {file_path}")

# Main Script
if __name__ == "__main__":
    # Debug mode
    plot_all_runs = True
    plot_torque_steps = False
    csv_instead_of_xlsx = False

    # Define test steps for torque analysis
    torque_steps = [
        {"name": "Pre Break-in Torque", "direction": "CW", "start_time": 1, "duration": 19},
        {"name": "Pre CW sweep", "direction": "CW", "start_time": 334, "duration": 19},
        {"name": "Post CW sweep", "direction": "CW", "start_time": 479, "duration": 19},
        {"name": "Pre CCW sweep", "direction": "CCW", "start_time": 501, "duration": 19},
        {"name": "Post CCW sweep", "direction": "CCW", "start_time": 647, "duration": 19},
    ]

    # Define test steps for speed sweeps
    speed_sweep_steps = [
        {"name": "Sweep CW", "direction": "CW", "start_time": 396, "duration": 125},
        {"name": "Sweep CCW", "direction": "CCW", "start_time": 565, "duration": 125},
    ]

    # File Selection and Loading
    file_paths = select_folder_and_find_files()
    
    if not file_paths:
        print("No files selected. Exiting.")
        exit()

    all_combined_sweeps = {}
    all_torque_averages = {}

    for file_path in file_paths:
        # Identify the folder where this file resides
        current_folder = os.path.dirname(file_path)
        folder_name = os.path.basename(current_folder)
        test_name = os.path.splitext(os.path.basename(file_path))[0]

        print(f"Processing {test_name} in folder: {current_folder}")
        
        # Load the data
        df = wdh_to_df(file_path)

        # Apply Low-Pass Filter
        df['torque, Nm (filtered)'] = lowpass_filter(
            data=df['torque, Nm'],
            sampling_rate=100,
            cutoff_freq=0.5
        )

        # Determine test start
        start_time = determine_test_start(df)
        if start_time is None:
            continue
        df['time, s'] = df['time, s'] - start_time

        # Extract and combine sweeps
        all_combined_sweeps[test_name] = extract_and_combine_sweeps(df, speed_sweep_steps)

        # Evaluate torque steps
        all_torque_averages[test_name] = evaluate_torque_at_stages(df, torque_steps)

        # Save results for each torque step
        if plot_torque_steps:
            for step in torque_steps:
                test_step_name = f"{test_name}_{step['name'].replace(' ', '_')}"
                step_start_time = step['start_time']
                step_duration = step['duration']

                plt = plot_filter_torque_stand_data(
                    df=df, 
                    test_name=f"{test_name}: {step['name']}",
                    start_time=step_start_time, 
                    duration=step_duration
                )
                step_plot_file = os.path.join(current_folder, f"{test_step_name}.png")
                plt.savefig(step_plot_file)
                plt.close()
                print(f"Step plot saved to: {step_plot_file}")

        # Save individual test plot
        if plot_all_runs:
            plot_file_path = os.path.join(current_folder, f"{test_name}_filtered_plot.png")
            plt = plot_filter_torque_stand_data(df, test_name=test_name, start_time=0)
            plt.savefig(plot_file_path)
            plt.close()
            print(f"Filtered plot saved to: {plot_file_path}")

        # Save raw data (CSV or Excel)
        if csv_instead_of_xlsx:
            rawdata_path = os.path.join(current_folder, f"{test_name}.csv")
            df.to_csv(rawdata_path, index=False)
        else:
            rawdata_path = os.path.join(current_folder, f"{test_name}_rawdata.xlsx")
            df.to_excel(rawdata_path, index=False)
        print(f"Raw data saved to: {rawdata_path}")


    # Group files by their immediate folder
    grouped_files = defaultdict(list)
    for path in file_paths:
        current_folder = os.path.dirname(path)  # Folder where the WDH resides
        grouped_files[current_folder].append(path)

    # Save torque averages specific to each folder
    for folder_path, files in grouped_files.items():
        folder_name = os.path.basename(folder_path)  # Folder name, e.g., "20996"
        torque_averages_for_folder = {}

        # Calculate torque averages only for the files in the current folder
        for file_path in files:
            test_name = os.path.splitext(os.path.basename(file_path))[0]
            torque_averages_for_folder[test_name] = all_torque_averages[test_name]

        # Save torque averages specific to this folder
        torque_averages_path = os.path.join(folder_path, f"{folder_name}_torque_averages.xlsx")
        save_torque_averages_to_excel(torque_averages_for_folder, torque_averages_path)
        print(f"Torque averages saved to: {torque_averages_path}")

    # Combine and save plots for each folder containing WDH files
    for folder_path, files in grouped_files.items():
        folder_name = os.path.basename(folder_path)  # Name of the folder (e.g., "20995")
        combined_sweeps = {}

        # Process all WDH files within the current folder
        for file_path in files:
            test_name = os.path.splitext(os.path.basename(file_path))[0]
            print(f"Processing {test_name} in folder: {folder_path}")

            # Load data
            df = wdh_to_df(file_path)

            # Apply Low-Pass Filter
            df['torque, Nm (filtered)'] = lowpass_filter(
                data=df['torque, Nm'],
                sampling_rate=100,
                cutoff_freq=0.5
            )

            # Determine test start
            start_time = determine_test_start(df)
            if start_time is None:
                continue
            df['time, s'] = df['time, s'] - start_time

            # Extract sweeps and add to combined plot
            combined_sweeps[test_name] = extract_and_combine_sweeps(df, speed_sweep_steps)

        # Save the combined plot in the current folder
        combined_plot_path = os.path.join(folder_path, f"{folder_name}_speedVStorque.png")
        plot_speed_vs_torque_multiple_tests(combined_sweeps, combined_plot_path)
        print(f"Combined Speed vs Torque plot saved to: {combined_plot_path}")