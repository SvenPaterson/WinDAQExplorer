import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import windaq as wdq

class WDQAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("WDQ Data Analyzer")
        self.root.geometry("1200x800")
        
        # Data storage
        self.wfile = None
        self.original_data = {}
        self.processed_data = {}
        self.time_data = None
        self.filename = ""
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for file loading and info
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load file button
        ttk.Button(top_frame, text="Load WDQ File", command=self.load_file).pack(side=tk.LEFT)
        
        # File info label
        self.file_info_label = ttk.Label(top_frame, text="No file loaded")
        self.file_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Channel Configuration
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Channel Configuration")
        self.create_config_tab()
        
        # Tab 2: Data Processing
        self.process_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.process_frame, text="Data Processing")
        self.create_processing_tab()
        
        # Tab 3: Plot View
        self.plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="Plot View")
        self.create_plot_tab()
        
    def create_config_tab(self):
        # Channel configuration table
        config_label = ttk.Label(self.config_frame, text="Channel Configuration", font=('Arial', 12, 'bold'))
        config_label.pack(pady=(0, 10))
        
        # Treeview for channel configuration
        columns = ('Channel', 'Name', 'Units', 'Plot Axis')
        self.channel_tree = ttk.Treeview(self.config_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.channel_tree.heading(col, text=col)
            self.channel_tree.column(col, width=150)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(self.config_frame, orient=tk.VERTICAL, command=self.channel_tree.yview)
        self.channel_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree_frame = ttk.Frame(self.config_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.channel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Axis selection frame
        axis_frame = ttk.Frame(self.config_frame)
        axis_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(axis_frame, text="Set selected channels to:").pack(side=tk.LEFT)
        
        ttk.Button(axis_frame, text="Primary Axis", 
                  command=lambda: self.set_axis_selection('Primary')).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(axis_frame, text="Secondary Axis", 
                  command=lambda: self.set_axis_selection('Secondary')).pack(side=tk.LEFT, padx=5)
        ttk.Button(axis_frame, text="Omit", 
                  command=lambda: self.set_axis_selection('Omit')).pack(side=tk.LEFT, padx=5)
        
        # Update plot button
        ttk.Button(self.config_frame, text="Update Plot", command=self.update_plot).pack(pady=10)
        
    def create_processing_tab(self):
        # Moving average section
        ma_frame = ttk.LabelFrame(self.process_frame, text="Moving Average", padding=10)
        ma_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(ma_frame, text="Window Size (samples):").pack(side=tk.LEFT)
        self.ma_window = tk.StringVar(value="10")
        ttk.Entry(ma_frame, textvariable=self.ma_window, width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(ma_frame, text="Apply Moving Average", command=self.apply_moving_average).pack(side=tk.LEFT)
        
        # Resampling section
        resample_frame = ttk.LabelFrame(self.process_frame, text="Resampling", padding=10)
        resample_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(resample_frame, text="Downsample by factor:").pack(side=tk.LEFT)
        self.resample_factor = tk.StringVar(value="2")
        ttk.Entry(resample_frame, textvariable=self.resample_factor, width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(resample_frame, text="Apply Resampling", command=self.apply_resampling).pack(side=tk.LEFT)
        
        # Reset and Export section
        action_frame = ttk.Frame(self.process_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Reset to Original Data", command=self.reset_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Replot Data", command=self.update_plot).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Export Data to CSV", command=self.export_data).pack(side=tk.LEFT)
        
        # Processing info
        self.process_info = ttk.Label(self.process_frame, text="No processing applied", foreground="blue")
        self.process_info.pack(pady=10)
        
    def create_plot_tab(self):
        # Plot controls
        plot_controls = ttk.Frame(self.plot_frame)
        plot_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(plot_controls, text="Save Plot", command=self.save_plot).pack(side=tk.LEFT)
        ttk.Button(plot_controls, text="Refresh Plot", command=self.update_plot).pack(side=tk.LEFT, padx=(10, 0))
        
        # Plot canvas
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Select WDQ File",
            filetypes=[("WDQ Files", "*.wdq"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            self.wfile = wdq.windaq(filename)
            self.filename = filename.split('/')[-1].split('\\')[-1]
            
            # Load original data
            self.time_data = self.wfile.time()
            self.original_data = {}
            self.processed_data = {}
            
            for channel in range(1, self.wfile.nChannels + 1):
                data = self.wfile.data(channel)
                self.original_data[channel] = data
                self.processed_data[channel] = data.copy()
            
            # Update file info
            self.file_info_label.config(
                text=f"File: {self.filename} | Channels: {self.wfile.nChannels} | "
                     f"Samples: {int(self.wfile.nSample)} | Rate: {1/self.wfile.timeStep:.1f} Hz"
            )
            
            # Populate channel configuration table
            self.populate_channel_table()
            
            # Reset processing info
            self.process_info.config(text="No processing applied")
            
            # Switch to config tab
            self.notebook.select(0)
            
            messagebox.showinfo("Success", f"Loaded {self.filename} successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def populate_channel_table(self):
        # Clear existing items
        for item in self.channel_tree.get_children():
            self.channel_tree.delete(item)
        
        # Add channels
        for channel in range(1, self.wfile.nChannels + 1):
            try:
                name = self.wfile.chAnnotation(channel)
                if not name or name.strip() == '':
                    name = f"Channel {channel}"
            except:
                name = f"Channel {channel}"
            
            try:
                units = self.wfile.unit(channel)
                if not units or units.strip() == '':
                    units = "N/A"
            except:
                units = "N/A"
            
            # Default: first channel primary, others secondary
            axis = "Primary" if channel == 1 else "Secondary"
            
            self.channel_tree.insert('', 'end', values=(channel, name, units, axis))
    
    def set_axis_selection(self, axis_type):
        selected_items = self.channel_tree.selection()
        for item in selected_items:
            values = list(self.channel_tree.item(item)['values'])
            values[3] = axis_type
            self.channel_tree.item(item, values=values)
    
    def apply_moving_average(self):
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        try:
            window = int(self.ma_window.get())
            if window < 1:
                raise ValueError("Window size must be positive")
            
            for channel in self.processed_data:
                data = np.array(self.processed_data[channel])
                # Simple moving average
                processed = np.convolve(data, np.ones(window)/window, mode='same')
                self.processed_data[channel] = processed.tolist()
            
            self.process_info.config(text=f"Applied moving average (window={window})")
            messagebox.showinfo("Success", f"Applied moving average with window size {window}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid window size: {str(e)}")
    
    def apply_resampling(self):
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        try:
            factor = int(self.resample_factor.get())
            if factor < 1:
                raise ValueError("Resample factor must be positive")
            
            # Resample time data
            self.time_data = self.time_data[::factor]
            
            # Resample channel data
            for channel in self.processed_data:
                data = np.array(self.processed_data[channel])
                self.processed_data[channel] = data[::factor].tolist()
            
            self.process_info.config(text=f"Resampled by factor {factor}")
            messagebox.showinfo("Success", f"Resampled data by factor {factor}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid resample factor: {str(e)}")
    
    def reset_data(self):
        if not self.wfile:
            return
        
        # Reset to original data
        self.time_data = self.wfile.time()
        for channel in self.original_data:
            self.processed_data[channel] = self.original_data[channel].copy()
        
        self.process_info.config(text="Reset to original data")
        messagebox.showinfo("Success", "Data reset to original")
    
    def update_plot(self):
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Get channel configurations
        primary_channels = []
        secondary_channels = []
        
        for item in self.channel_tree.get_children():
            values = self.channel_tree.item(item)['values']
            channel_num = int(values[0])
            axis_type = values[3]
            
            if axis_type == "Primary":
                primary_channels.append(channel_num)
            elif axis_type == "Secondary":
                secondary_channels.append(channel_num)
        
        # Plot primary channels
        if primary_channels:
            for i, channel in enumerate(primary_channels):
                try:
                    name = self.channel_tree.item(
                        self.channel_tree.get_children()[channel-1])['values'][1]
                    units = self.channel_tree.item(
                        self.channel_tree.get_children()[channel-1])['values'][2]
                    label = f"{name} ({units})" if units != "N/A" else name
                except:
                    label = f"Channel {channel}"
                
                self.ax1.plot(self.time_data, self.processed_data[channel], 
                             label=label, linewidth=1.5)
            
            self.ax1.set_xlabel('Time (seconds)')
            self.ax1.set_ylabel('Primary Channels')
            self.ax1.legend()
            self.ax1.grid(True, alpha=0.3)
            self.ax1.set_title(f'Primary Channels - {self.filename}')
        
        # Plot secondary channels
        if secondary_channels:
            colors = ['r', 'g', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown', 'pink']
            for i, channel in enumerate(secondary_channels):
                try:
                    name = self.channel_tree.item(
                        self.channel_tree.get_children()[channel-1])['values'][1]
                    units = self.channel_tree.item(
                        self.channel_tree.get_children()[channel-1])['values'][2]
                    label = f"{name} ({units})" if units != "N/A" else name
                except:
                    label = f"Channel {channel}"
                
                color = colors[i % len(colors)]
                self.ax2.plot(self.time_data, self.processed_data[channel], 
                             color=color, label=label, linewidth=1)
            
            self.ax2.set_xlabel('Time (seconds)')
            self.ax2.set_ylabel('Secondary Channels')
            self.ax2.legend()
            self.ax2.grid(True, alpha=0.3)
            self.ax2.set_title('Secondary Channels')
        
        # If no secondary channels, remove the second subplot
        if not secondary_channels:
            self.ax2.set_visible(False)
        else:
            self.ax2.set_visible(True)
        
        plt.tight_layout()
        self.canvas.draw()
        
        # Switch to plot tab
        self.notebook.select(2)
    
    def save_plot(self):
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Plot",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot: {str(e)}")
    
    def export_data(self):
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Create DataFrame
                data_dict = {'Time': self.time_data}
                
                for item in self.channel_tree.get_children():
                    values = self.channel_tree.item(item)['values']
                    channel_num = int(values[0])
                    name = values[1]
                    units = values[2]
                    
                    if units != "N/A":
                        col_name = f"{name} ({units})"
                    else:
                        col_name = name
                    
                    data_dict[col_name] = self.processed_data[channel_num]
                
                df = pd.DataFrame(data_dict)
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WDQAnalyzer(root)
    root.mainloop()