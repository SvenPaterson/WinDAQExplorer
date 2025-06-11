import windaq as wdq
from tkinter import filedialog, messagebox
import pandas as pd

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
        
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"Conversion failed: {str(e)}")

if __name__ == "__main__":
    # Ask user for input file path with tkinter dialog
    input_file = filedialog.askopenfilename(
        title="Select Windaq File", 
        filetypes=[("Windaq Files", "*.wdq"), ("All Files", "*.*")]
    )
    
    if not input_file:
        messagebox.showwarning("Warning", "No input file selected.")
    else:
        # Generate output filename
        output_file = f"{input_file.rsplit('.', 1)[0]}.csv"
        
        # Convert the file
        convert_wdq_to_csv(input_file, output_file)
        
        # Show success message
        messagebox.showinfo("Success", f"File converted successfully!\nOutput: {output_file}")