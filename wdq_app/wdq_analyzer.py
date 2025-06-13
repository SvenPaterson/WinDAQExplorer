"""Main WDQ Analyzer application."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import windaq as wdq

from models import ChannelConfig
from data_processor import DataProcessor
from plot_manager import PlotManager
from gui_components import GUIComponents


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
        
        self.file_info_label = GUIComponents.create_status_label(top_frame, "No file loaded")
        self.file_info_label.config(foreground="black")
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
        columns = ('Channel', 'Name', 'Units', 'Plot Axis')
        self.channel_tree, _, tree_frame = GUIComponents.create_treeview_with_scrollbar(
            config_frame, columns, height=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Axis selection controls
        axis_frame = ttk.Frame(config_frame)
        axis_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(axis_frame, text="Set selected channels to:").pack(side=tk.LEFT)
        
        buttons = [
            ("Primary Axis", lambda: self.set_axis_selection('Primary')),
            ("Secondary Axis", lambda: self.set_axis_selection('Secondary')),
            ("Omit", lambda: self.set_axis_selection('Omit'))
        ]
        GUIComponents.create_button_row(axis_frame, buttons, padx=5)
        
        # Update button
        ttk.Button(config_frame, text="Update Plot", 
                  command=self.update_plot).pack(pady=10)
    
    def _create_processing_tab(self):
        """Create data processing tab."""
        process_frame = ttk.Frame(self.notebook)
        self.notebook.add(process_frame, text="Data Processing")
        
        # Moving average section
        ma_frame = GUIComponents.create_labeled_frame(process_frame, "Moving Average")
        ma_frame.pack(fill=tk.X, pady=(0, 10))
        
        label, entry = GUIComponents.create_entry_with_label(
            ma_frame, "Window Size (samples):", self.ma_window)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(ma_frame, text="Apply Moving Average", 
                  command=self.apply_moving_average).pack(side=tk.LEFT)
        
        # Resampling section
        resample_frame = GUIComponents.create_labeled_frame(process_frame, "Resampling")
        resample_frame.pack(fill=tk.X, pady=(0, 10))
        
        label, entry = GUIComponents.create_entry_with_label(
            resample_frame, "Downsample by factor:", self.resample_factor)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(resample_frame, text="Apply Resampling", 
                  command=self.apply_resampling).pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.Frame(process_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Reset to Original Data", self.reset_data),
            ("Replot Data", self.update_plot),
            ("Export Data to CSV", self.export_data)
        ]
        GUIComponents.create_button_row(action_frame, buttons, padx=10)
        
        # Processing info
        self.process_info = GUIComponents.create_status_label(
            process_frame, "No processing applied")
        self.process_info.pack(pady=10)
    
    def _create_plot_tab(self):
        """Create plot view tab."""
        plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(plot_frame, text="Plot View")
        
        # Plot controls
        plot_controls = ttk.Frame(plot_frame)
        plot_controls.pack(fill=tk.X, pady=(0, 10))
        
        buttons = [
            ("Save Plot", self.save_plot),
            ("Refresh Plot", self.update_plot)
        ]
        GUIComponents.create_button_row(plot_controls, buttons, padx=10)
        
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
            self._export_to_csv(filename)
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}") not filename:
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
    main() not filename:
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
                processed = DataProcessor.apply_moving_average(
                    self.processed_data[channel], window)
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
                resampled = DataProcessor.resample_data(
                    self.processed_data[channel], factor)
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
        
        if