import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import windaq as wdq


class ChannelConfig:
    """Configuration for a single channel."""
    
    def __init__(self, channel_num: int, name: str = "", units: str = "N/A", axis: str = "Primary"):
        self.channel_num = channel_num
        self.name = name or f"Channel {channel_num}"
        self.units = units
        self.axis = axis
    
    @property
    def label(self) -> str:
        """Generate label for plotting."""
        return f"{self.name} ({self.units})" if self.units != "N/A" else self.name


class DataProcessor:
    """Handles data processing operations."""
    
    @staticmethod
    def apply_moving_average(data: np.ndarray, window_size: int) -> np.ndarray:
        """Apply moving average to data."""
        if window_size < 1:
            raise ValueError("Window size must be positive")
        return np.convolve(data, np.ones(window_size) / window_size, mode='same')
    
    @staticmethod
    def resample_data(data: np.ndarray, factor: int) -> np.ndarray:
        """Downsample data by given factor."""
        if factor < 1:
            raise ValueError("Resample factor must be positive")
        return data[::factor]


class PlotManager:
    """Manages plot creation and updates."""
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.fig = None
        self.ax1 = None
        self.ax2 = None
        self.canvas = None
        self._setup_plot()
    
    def _setup_plot(self):
        """Initialize plot components."""
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_plot(self, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                    channel_configs: Dict[int, ChannelConfig], filename: str):
        """Update the plot with new data."""
        self.ax1.clear()
        self.ax2.clear()
        
        primary_channels = [ch for ch, config in channel_configs.items() 
                          if config.axis == "Primary"]
        secondary_channels = [ch for ch, config in channel_configs.items() 
                            if config.axis == "Secondary"]
        
        # Plot primary channels
        if primary_channels:
            self._plot_channels(self.ax1, time_data, channel_data, channel_configs, 
                              primary_channels, f'Primary Channels - {filename}', 'Primary Channels')
        
        # Plot secondary channels
        if secondary_channels:
            self._plot_channels(self.ax2, time_data, channel_data, channel_configs, 
                              secondary_channels, 'Secondary Channels', 'Secondary Channels')
            self.ax2.set_visible(True)
        else:
            self.ax2.set_visible(False)
        
        plt.tight_layout()
        self.canvas.draw()
    
    def _plot_channels(self, ax, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                      channel_configs: Dict[int, ChannelConfig], channels: List[int], 
                      title: str, ylabel: str):
        """Plot channels on given axis."""
        colors = ['b', 'r', 'g', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown', 'pink']
        
        for i, channel in enumerate(channels):
            config = channel_configs[channel]
            color = colors[i % len(colors)] if ax == self.ax2 else None
            ax.plot(time_data, channel_data[channel], 
                   label=config.label, linewidth=1.5 if ax == self.ax1 else 1,
                   color=color)
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title(title)
    
    def save_plot(self, default_filename: str = "plot.png"):
        """Save the current plot to file."""
        filename = filedialog.asksaveasfilename(
            title="Save Plot",
            defaultextension=".png",
            initialfile=default_filename,
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return filename
        return None


class WDQAnalyzer:
    """Main application class for WDQ data analysis."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WDQ Data Analyzer")
        self.root.geometry("1200x800")
        
        # Data storage
        self.wfile: Optional[wdq.windaq] = None
        self.original_data: Dict[int, List[float]] = {}
        self.processed_data: Dict[int, List[float]] = {}
        self.time_data: Optional[np.ndarray] = None
        self.filename: str = ""
        self.channel_configs: Dict[int, ChannelConfig] = {}
        
        # Processing state
        self.processing_history: List[str] = []
        
        # GUI components
        self.notebook = None
        self.channel_tree = None
        self.file_info_label = None
        self.process_info = None
        self.plot_manager = None
        
        # Control variables
        self.ma_window = tk.StringVar(value="10")
        self.resample_factor = tk.StringVar(value="2")
        
        self._create_gui()
    
    def _create_gui(self):
        """Create the main GUI structure."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_top_frame(main_frame)
        self._create_notebook(main_frame)
    
    def _create_top_frame(self, parent: ttk.Frame):
        """Create top frame with file controls."""
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(top_frame, text="Load WDQ File", command=self.load_file).pack(side=tk.LEFT)
        
        self.file_info_label = ttk.Label(top_frame, text="No file loaded")
        self.file_info_label.pack(side=tk.LEFT, padx=(20, 0))
    
    def _create_notebook(self, parent: ttk.Frame):
        """Create notebook with tabs."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_config_tab()
        self._create_processing_tab()
        self._create_plot_tab()
    
    def _create_config_tab(self):
        """Create channel configuration tab."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Channel Configuration")
        
        # Header
        ttk.Label(config_frame, text="Channel Configuration", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Channel table
        self._create_channel_table(config_frame)
        
        # Axis selection controls
        self._create_axis_controls(config_frame)
        
        # Update button
        ttk.Button(config_frame, text="Update Plot", 
                  command=self.update_plot).pack(pady=10)
    
    def _create_channel_table(self, parent: ttk.Frame):
        """Create channel configuration table."""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ('Channel', 'Name', 'Units', 'Plot Axis')
        self.channel_tree = ttk.Treeview(tree_frame, columns=columns, 
                                       show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.channel_tree.heading(col, text=col)
            self.channel_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                command=self.channel_tree.yview)
        self.channel_tree.configure(yscrollcommand=scrollbar.set)
        
        self.channel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_axis_controls(self, parent: ttk.Frame):
        """Create axis selection controls."""
        axis_frame = ttk.Frame(parent)
        axis_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(axis_frame, text="Set selected channels to:").pack(side=tk.LEFT)
        
        for text, value in [("Primary Axis", "Primary"), 
                           ("Secondary Axis", "Secondary"), 
                           ("Omit", "Omit")]:
            ttk.Button(axis_frame, text=text,
                      command=lambda v=value: self.set_axis_selection(v)
                      ).pack(side=tk.LEFT, padx=(10 if text == "Primary Axis" else 5, 5))
    
    def _create_processing_tab(self):
        """Create data processing tab."""
        process_frame = ttk.Frame(self.notebook)
        self.notebook.add(process_frame, text="Data Processing")
        
        # Moving average section
        self._create_moving_average_section(process_frame)
        
        # Resampling section
        self._create_resampling_section(process_frame)
        
        # Action buttons
        self._create_action_buttons(process_frame)
        
        # Processing info
        self.process_info = ttk.Label(process_frame, text="No processing applied", 
                                    foreground="blue")
        self.process_info.pack(pady=10)
    
    def _create_moving_average_section(self, parent: ttk.Frame):
        """Create moving average controls."""
        ma_frame = ttk.LabelFrame(parent, text="Moving Average", padding=10)
        ma_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(ma_frame, text="Window Size (samples):").pack(side=tk.LEFT)
        ttk.Entry(ma_frame, textvariable=self.ma_window, width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(ma_frame, text="Apply Moving Average", 
                  command=self.apply_moving_average).pack(side=tk.LEFT)
    
    def _create_resampling_section(self, parent: ttk.Frame):
        """Create resampling controls."""
        resample_frame = ttk.LabelFrame(parent, text="Resampling", padding=10)
        resample_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(resample_frame, text="Downsample by factor:").pack(side=tk.LEFT)
        ttk.Entry(resample_frame, textvariable=self.resample_factor, 
                 width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(resample_frame, text="Apply Resampling", 
                  command=self.apply_resampling).pack(side=tk.LEFT)
    
    def _create_action_buttons(self, parent: ttk.Frame):
        """Create action buttons."""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Reset to Original Data", self.reset_data),
            ("Replot Data", self.update_plot),
            ("Export Data to CSV", self.export_data)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(action_frame, text=text, command=command).pack(
                side=tk.LEFT, padx=(0 if i == 0 else 10, 0))
    
    def _create_plot_tab(self):
        """Create plot view tab."""
        plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(plot_frame, text="Plot View")
        
        # Plot controls
        plot_controls = ttk.Frame(plot_frame)
        plot_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(plot_controls, text="Save Plot", 
                  command=self.save_plot).pack(side=tk.LEFT)
        ttk.Button(plot_controls, text="Refresh Plot", 
                  command=self.update_plot).pack(side=tk.LEFT, padx=(10, 0))
        
        # Initialize plot manager
        self.plot_manager = PlotManager(plot_frame)
    
    def load_file(self):
        """Load WDQ file and initialize data."""
        filename = filedialog.askopenfilename(
            title="Select WDQ File",
            filetypes=[("WDQ Files", "*.wdq"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            self._load_wdq_file(filename)
            self._update_file_info()
            self._populate_channel_table()
            self._reset_processing_state()
            
            self.notebook.select(0)  # Switch to config tab
            messagebox.showinfo("Success", f"Loaded {self.filename} successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def _load_wdq_file(self, filename: str):
        """Load WDQ file and extract data."""
        self.wfile = wdq.windaq(filename)
        self.filename = filename.split('/')[-1].split('\\')[-1]
        
        # Load time data
        self.time_data = self.wfile.time()
        
        # Load channel data
        self.original_data = {}
        self.processed_data = {}
        self.channel_configs = {}
        
        for channel in range(1, self.wfile.nChannels + 1):
            data = self.wfile.data(channel)
            self.original_data[channel] = data
            self.processed_data[channel] = data.copy()
            
            # Create channel configuration
            self.channel_configs[channel] = self._create_channel_config(channel)
    
    def _create_channel_config(self, channel: int) -> ChannelConfig:
        """Create configuration for a channel."""
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
        
        # First channel primary, others secondary by default
        axis = "Primary" if channel == 1 else "Secondary"
        
        return ChannelConfig(channel, name, units, axis)
    
    def _update_file_info(self):
        """Update file information display."""
        info_text = (f"File: {self.filename} | "
                    f"Channels: {self.wfile.nChannels} | "
                    f"Samples: {int(self.wfile.nSample)} | "
                    f"Rate: {1/self.wfile.timeStep:.1f} Hz")
        self.file_info_label.config(text=info_text)
    
    def _populate_channel_table(self):
        """Populate channel configuration table."""
        # Clear existing items
        for item in self.channel_tree.get_children():
            self.channel_tree.delete(item)
        
        # Add channels
        for channel, config in self.channel_configs.items():
            self.channel_tree.insert('', 'end', 
                                   values=(config.channel_num, config.name, 
                                          config.units, config.axis))
    
    def _reset_processing_state(self):
        """Reset processing state."""
        self.processing_history = []
        self.process_info.config(text="No processing applied")
    
    def set_axis_selection(self, axis_type: str):
        """Set axis type for selected channels."""
        selected_items = self.channel_tree.selection()
        
        for item in selected_items:
            values = list(self.channel_tree.item(item)['values'])
            channel_num = int(values[0])
            values[3] = axis_type
            self.channel_tree.item(item, values=values)
            
            # Update channel config
            self.channel_configs[channel_num].axis = axis_type
    
    def apply_moving_average(self):
        """Apply moving average to all channels."""
        if not self._validate_file_loaded():
            return
        
        try:
            window = int(self.ma_window.get())
            
            for channel in self.processed_data:
                data = np.array(self.processed_data[channel])
                processed = DataProcessor.apply_moving_average(data, window)
                self.processed_data[channel] = processed.tolist()
            
            self._update_processing_info(f"Applied moving average (window={window})")
            messagebox.showinfo("Success", f"Applied moving average with window size {window}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid window size: {str(e)}")
    
    def apply_resampling(self):
        """Apply resampling to data."""
        if not self._validate_file_loaded():
            return
        
        try:
            factor = int(self.resample_factor.get())
            
            # Resample time data
            self.time_data = DataProcessor.resample_data(self.time_data, factor)
            
            # Resample channel data
            for channel in self.processed_data:
                data = np.array(self.processed_data[channel])
                resampled = DataProcessor.resample_data(data, factor)
                self.processed_data[channel] = resampled.tolist()
            
            self._update_processing_info(f"Resampled by factor {factor}")
            messagebox.showinfo("Success", f"Resampled data by factor {factor}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid resample factor: {str(e)}")
    
    def reset_data(self):
        """Reset to original data."""
        if not self.wfile:
            return
        
        self.time_data = self.wfile.time()
        for channel in self.original_data:
            self.processed_data[channel] = self.original_data[channel].copy()
        
        self._reset_processing_state()
        self._update_processing_info("Reset to original data")
        messagebox.showinfo("Success", "Data reset to original")
    
    def update_plot(self):
        """Update the plot with current data."""
        if not self._validate_file_loaded():
            return
        
        # Update channel configs from tree
        self._sync_channel_configs()
        
        # Update plot
        self.plot_manager.update_plot(
            self.time_data, 
            self.processed_data, 
            self.channel_configs, 
            self.filename
        )
        
        # Switch to plot tab
        self.notebook.select(2)
    
    def _sync_channel_configs(self):
        """Sync channel configurations from tree view."""
        for item in self.channel_tree.get_children():
            values = self.channel_tree.item(item)['values']
            channel_num = int(values[0])
            self.channel_configs[channel_num].axis = values[3]
    
    def save_plot(self):
        """Save the current plot."""
        if not self._validate_file_loaded():
            return
        
        default_name = self.filename.rsplit('.', 1)[0] + "_plot.png"
        saved_file = self.plot_manager.save_plot(default_name)
        
        if saved_file:
            messagebox.showinfo("Success", f"Plot saved to {saved_file}")
    
    def export_data(self):
        """Export processed data to CSV."""
        if not self._validate_file_loaded():
            return
        
        default_name = self.filename.rsplit('.', 1)[0] + "_data.csv"
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            self._export_to_csv(filename)
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def _export_to_csv(self, filename: str):
        """Export data to CSV file."""
        data_dict = {'Time': self.time_data}
        
        for channel, config in self.channel_configs.items():
            data_dict[config.label] = self.processed_data[channel]
        
        df = pd.DataFrame(data_dict)
        df.to_csv(filename, index=False)
    
    def _validate_file_loaded(self) -> bool:
        """Check if file is loaded."""
        if not self.wfile:
            messagebox.showwarning("Warning", "Please load a file first")
            return False
        return True
    
    def _update_processing_info(self, message: str):
        """Update processing information display."""
        self.processing_history.append(message)
        self.process_info.config(text=message)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = WDQAnalyzer(root)
    root.mainloop()


if __name__ == "__main__":
    main()