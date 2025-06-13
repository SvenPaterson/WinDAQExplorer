import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Define bearing parameters
num_balls = 7  # Number of balls (Z)
ball_diameter = 5.6  # Ball diameter (mm)
pitch_diameter = 20.0  # Pitch circle diameter (mm)
contact_angle = 0  # Contact angle (degrees)
cos_angle = np.cos(np.radians(contact_angle))  # Convert angle to radians

# Define RPM range
rpm_values = np.linspace(0, 1800, 500)  # Generate 500 points between 0 and 1800 RPM

# Calculate characteristic frequencies
frequencies = []
for rpm in rpm_values:
    BPFO = (num_balls / 2) * (1 - (ball_diameter / pitch_diameter) * cos_angle) * (rpm / 60)
    BPFI = (num_balls / 2) * (1 + (ball_diameter / pitch_diameter) * cos_angle) * (rpm / 60)
    FTF = (1 / 2) * (1 - (ball_diameter / pitch_diameter) * cos_angle) * (rpm / 60)
    BSF = (pitch_diameter / ball_diameter) * (1 - ((ball_diameter / pitch_diameter) * cos_angle) ** 2) * (rpm / 60)
    frequencies.append([rpm, BPFO, BPFI, FTF, BSF])

# Convert to DataFrame
columns = ["RPM", "BPFO (Hz)", "BPFI (Hz)", "FTF (Hz)", "BSF (Hz)"]
frequency_df = pd.DataFrame(frequencies, columns=columns)

# Plot the frequencies
plt.figure(figsize=(10, 6))
plt.plot(frequency_df["RPM"], frequency_df["BPFO (Hz)"], label="BPFO")
plt.plot(frequency_df["RPM"], frequency_df["BPFI (Hz)"], label="BPFI")
plt.plot(frequency_df["RPM"], frequency_df["FTF (Hz)"], label="FTF")
plt.plot(frequency_df["RPM"], frequency_df["BSF (Hz)"], label="BSF")
plt.xlabel("RPM")
plt.ylabel("Frequency (Hz)")
plt.title("Characteristic Frequencies vs. RPM")
plt.legend()
plt.grid(True)
plt.show()

# Optionally, save to CSV
frequency_df.to_csv("bearing_frequencies.csv", index=False)
