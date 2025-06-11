import windaq as wdq
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def convert_wdq_to_csv(input_file, output_file):
    """
    Convert a Windaq file to CSV format.

    Parameters:
    input_file (str): Path to the input Windaq file.
    output_file (str): Path to the output CSV file.
    """
    try:
        # Read the Windaq file
        wfile = wdq.windaq(input_file)
        
        # Create a dictionary to hold all channel data
        data_dict = {}
        
        # Add time column
        data_dict['Time'] = wfile.time()
        
        # Add data for each channel
        for channel in range(1, wfile.nChannels + 1):
            # Get channel data
            channel_data = wfile.data(channel)
            
            # Get channel annotation (if available) or use default naming
            try:
                channel_name = wfile.chAnnotation(channel)
                if not channel_name or channel_name.strip() == '':
                    channel_name = f"Channel_{channel}"
            except:
                channel_name = f"Channel_{channel}"
            
            # Get units (if available)
            try:
                units = wfile.unit(channel)
                if units and units.strip():
                    channel_name += f" ({units})"
            except:
                pass
            
            data_dict[channel_name] = channel_data
        
        # Create DataFrame
        df = pd.DataFrame(data_dict)
        
        # Write to CSV
        df.to_csv(output_file, index=False)
        print(f"Successfully converted {input_file} to {output_file}")
        print(f"File contains {wfile.nChannels} channels with {int(wfile.nSample)} samples each")
        print(f"Time step: {wfile.timeStep} seconds")

        # Show success message
        messagebox.showinfo("Success", f"File converted successfully!\nOutput: {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"Conversion failed: {str(e)}")


def plot_wdq_data(input_file):
    """
    Plot Windaq data with time on x-axis, channel 1 on primary y-axis,
    and remaining channels on secondary y-axis.

    Parameters:
    input_file (str): Path to the input Windaq file.
    """
    try:
        # Read the Windaq file
        wfile = wdq.windaq(input_file)
        
        # Get time data
        time_data = wfile.time()
        
        # Create the plot
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Plot channel 1 on primary y-axis
        channel1_data = wfile.data(1)
        
        # Get channel 1 info
        try:
            ch1_name = wfile.chAnnotation(1)
            if not ch1_name or ch1_name.strip() == '':
                ch1_name = "Channel 1"
        except:
            ch1_name = "Channel 1"
        
        try:
            ch1_units = wfile.unit(1)
            if ch1_units and ch1_units.strip():
                ch1_label = f"{ch1_name} ({ch1_units})"
            else:
                ch1_label = ch1_name
        except:
            ch1_label = ch1_name
        
        # Plot channel 1
        line1 = ax1.plot(time_data, channel1_data, 'b-', linewidth=1.5, label=ch1_label)
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel(ch1_label, color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)
        
        # Create secondary y-axis for remaining channels
        if wfile.nChannels > 1:
            ax2 = ax1.twinx()
            
            # Plot remaining channels on secondary y-axis
            colors = ['r', 'g', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown', 'pink']
            lines2 = []
            labels2 = []
            
            for channel in range(2, wfile.nChannels + 1):
                channel_data = wfile.data(channel)
                color = colors[(channel-2) % len(colors)]
                
                # Get channel info
                try:
                    ch_name = wfile.chAnnotation(channel)
                    if not ch_name or ch_name.strip() == '':
                        ch_name = f"Channel {channel}"
                except:
                    ch_name = f"Channel {channel}"
                    
                try:
                    ch_units = wfile.unit(channel)
                    if ch_units and ch_units.strip():
                        ch_label = f"{ch_name} ({ch_units})"
                    else:
                        ch_label = ch_name
                except:
                    ch_label = ch_name
                
                line = ax2.plot(time_data, channel_data, color=color, linewidth=1, 
                               label=ch_label, alpha=0.8)
                lines2.extend(line)
                labels2.append(ch_label)
            
            ax2.set_ylabel('Other Channels', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            
            # Create combined legend
            lines = line1 + lines2
            labels = [ch1_label] + labels2
            ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(1.05, 1))
        else:
            # Single channel case
            ax1.legend(loc='upper right')
        
        # Set title with file info
        filename = input_file.split('/')[-1].split('\\')[-1]  # Get just the filename
        plt.title(f'Windaq Data: {filename}\n'
                 f'Channels: {wfile.nChannels}, Samples: {int(wfile.nSample)}, '
                 f'Sample Rate: {1/wfile.timeStep:.2f} Hz\n'
                 f'Created: {wfile.fileCreated}', pad=20)
        
        # Adjust layout to prevent legend cutoff
        plt.tight_layout()
        
        # Show the plot
        plt.show()
        
        print(f"Successfully plotted data from {input_file}")
        print(f"File contains {wfile.nChannels} channels with {int(wfile.nSample)} samples each")
        print(f"Time step: {wfile.timeStep} seconds")
        print(f"Sample rate: {1/wfile.timeStep:.2f} Hz")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"Plotting failed: {str(e)}")


if __name__ == "__main__":
    # Ask user for input file path with tkinter dialog
    input_file = filedialog.askopenfilename(
        title="Select Windaq File", 
        filetypes=[("Windaq Files", "*.wdq"), ("All Files", "*.*")]
    )
    

    # output_file = f"{input_file.rsplit('.', 1)[0]}.csv"
    # convert_wdq_to_csv(input_file, output_file)

    plot_wdq_data(input_file)

        