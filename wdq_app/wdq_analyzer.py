"""Improved WDQ Analyzer with modern UI design."""

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
    """Main application class for WDQ data analysis with improved UI."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WDQ Data Analyzer")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Configure modern styling
        self._configure_styling()
        
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
        self.main_paned = None
        self.left_panel = None
        self.right_panel = None
        self.channel_tree = None
        self.file_info_frame = None
        self.status_bar = None
        self.plot_manager = None
        
        # Control variables
        self.ma_window = tk.StringVar(value="10")
        self.resample_factor = tk.StringVar(value="2")
        self.cutoff_freq = tk.StringVar(value="10.0")
        self.sample_rate = tk.StringVar(value="100.0")
        
        self._create_gui()
    
    def _configure_styling(self):
        """Configure modern styling for the application."""
        style = ttk.Style()
        
        # Configure notebook to look more modern
        style.configure('Modern.TNotebook', tabposition='n')
        style.configure('Modern.TNotebook.Tab', padding=[20, 8])
        
        # Configure frames with better spacing
        style.configure('Card.TFrame', relief='solid', borderwidth=1)
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Subheader.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9), foreground='#666666')
    
    def _create_gui(self):
        """Create the modern GUI structure."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self._create_header(main_container)
        
        # Create main content area with paned window
        self._create_main_content(main_container)
        
        # Create status bar
        self._create_status_bar(main_container)
    
    def _create_header(self, parent):
        """Create modern header with file controls and info."""
        header_frame = ttk.Frame(parent, style='Card.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Left side - file controls
        left_header = ttk.Frame(header_frame)
        left_header.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=15)
        
        # App title and load button
        title_frame = ttk.Frame(left_header)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="WDQ Data Analyzer", 
                 style='Header.TLabel').pack(side=tk.LEFT)
        
        # Modern load button
        load_btn = ttk.Button(title_frame, text="📁 Load WDQ File", 
                             command=self.load_file)
        load_btn.pack(side=tk.RIGHT)
        
        # File info section
        self.file_info_frame = ttk.Frame(left_header)
        self.file_info_frame.pack(fill=tk.X)
        
        self._create_file_info_display()
    
    def _create_file_info_display(self):
        """Create attractive file information display."""
        # Clear existing
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        if not self.wfile:
            ttk.Label(self.file_info_frame, text="No file loaded", 
                     style='Status.TLabel').pack(anchor=tk.W)
            return
        
        # File info grid
        info_frame = ttk.Frame(self.file_info_frame)
        info_frame.pack(fill=tk.X)
        
        # File name (prominent)
        ttk.Label(info_frame, text=f"File: {self.filename}", 
                 style='Subheader.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        # Stats in a clean row
        stats_frame = ttk.Frame(info_frame)
        stats_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        stats = [
            ("Channels", str(self.wfile.nChannels)),
            ("Samples", f"{int(self.wfile.nSample):,}"),
            ("Sample Rate", f"{1/self.wfile.timeStep:.1f} Hz"),
            ("Duration", f"{self.wfile.nSample * self.wfile.timeStep:.1f} sec")
        ]
        
        for i, (label, value) in enumerate(stats):
            ttk.Label(stats_frame, text=f"{label}:", 
                     font=('Segoe UI', 9)).grid(row=0, column=i*2, sticky=tk.W, padx=(0, 5))
            ttk.Label(stats_frame, text=value, 
                     font=('Segoe UI', 9, 'bold')).grid(row=0, column=i*2+1, sticky=tk.W, padx=(0, 20))
    
    def _create_main_content(self, parent):
        """Create main content area with improved layout."""
        # Paned window for resizable layout
        self.main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - controls (30% width)
        self.left_panel = ttk.Frame(self.main_paned, style='Card.TFrame')
        self.main_paned.add(self.left_panel, weight=30)
        
        # Right panel - plot (70% width)
        self.right_panel = ttk.Frame(self.main_paned, style='Card.TFrame')
        self.main_paned.add(self.right_panel, weight=70)
        
        # Create left panel content
        self._create_left_panel()
        
        # Create right panel content
        self._create_right_panel()
    
    def _create_left_panel(self):
        """Create left control panel with tabs."""
        # Notebook for left panel tabs
        left_notebook = ttk.Notebook(self.left_panel, style='Modern.TNotebook')
        left_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Channel configuration tab
        self._create_channel_config_tab(left_notebook)
        
        # Processing tab
        self._create_processing_tab(left_notebook)
    
    def _create_channel_config_tab(self, notebook):
        """Create improved channel configuration tab."""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Channels")
        
        # Header
        header_frame = ttk.Frame(config_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="Channel Configuration", 
                 style='Subheader.TLabel').pack(anchor=tk.W)
        
        # Instructions
        ttk.Label(header_frame, text="Select channels and assign to plot axes:", 
                 style='Status.TLabel').pack(anchor=tk.W, pady=(2, 0))
        
        # Channel table with improved styling
        table_frame = ttk.Frame(config_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview with scrollbar
        columns = ('Ch#', 'Name', 'Units', 'Axis')
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.channel_tree = ttk.Treeview(tree_container, columns=columns, 
                                        show='headings', height=8)
        
        # Configure columns with better widths
        col_widths = {'Ch#': 40, 'Name': 120, 'Units': 60, 'Axis': 80}
        for col in columns:
            self.channel_tree.heading(col, text=col)
            self.channel_tree.column(col, width=col_widths[col], minwidth=30)
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, 
                                   command=self.channel_tree.yview)
        self.channel_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.channel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Axis assignment buttons in a clean row
        axis_label_frame = ttk.Frame(button_frame)
        axis_label_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(axis_label_frame, text="Assign selected to:", 
                 style='Status.TLabel').pack(anchor=tk.W)
        
        axis_btn_frame = ttk.Frame(button_frame)
        axis_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(axis_btn_frame, text="Primary", 
                  command=lambda: self.set_axis_selection('Primary')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(axis_btn_frame, text="Secondary", 
                  command=lambda: self.set_axis_selection('Secondary')).pack(side=tk.LEFT, padx=5)
        ttk.Button(axis_btn_frame, text="Hide", 
                  command=lambda: self.set_axis_selection('Omit')).pack(side=tk.LEFT, padx=5)
        
        # Update plot button
        ttk.Button(button_frame, text="🔄 Update Plot", 
                  command=self.update_plot).pack(fill=tk.X)
    
    def _create_processing_tab(self, notebook):
        """Create improved processing tab."""
        process_frame = ttk.Frame(notebook)
        notebook.add(process_frame, text="Processing")
        
        # Create scrollable frame for processing options
        canvas = tk.Canvas(process_frame)
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Moving Average section
        self._create_processing_section(scrollable_frame, "Moving Average", [
            ("Window Size:", self.ma_window, "samples"),
            ("Apply", None, lambda: self.apply_moving_average())
        ])
        
        # Resampling section
        self._create_processing_section(scrollable_frame, "Resampling", [
            ("Factor:", self.resample_factor, ""),
            ("Apply", None, lambda: self.apply_resampling())
        ])
        
        # Low Pass Filter section
        self._create_processing_section(scrollable_frame, "Low Pass Filter", [
            ("Cutoff Freq:", self.cutoff_freq, "Hz"),
            ("Sample Rate:", self.sample_rate, "Hz"),
            ("Apply", None, lambda: self.apply_lowpass_filter())
        ])
        
        # Action buttons
        action_frame = ttk.LabelFrame(scrollable_frame, text="Actions", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="🔄 Reset to Original", 
                  command=self.reset_data).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="📊 Replot Data", 
                  command=self.update_plot).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="💾 Export CSV", 
                  command=self.export_data).pack(fill=tk.X, pady=2)
        
        # Processing status
        status_frame = ttk.Frame(scrollable_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_frame, text="Processing Status:", 
                 style='Status.TLabel').pack(anchor=tk.W)
        self.process_info = ttk.Label(status_frame, text="No processing applied", 
                                     style='Status.TLabel', foreground='green')
        self.process_info.pack(anchor=tk.W, pady=(2, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_processing_section(self, parent, title, controls):
        """Create a processing section with consistent styling."""
        section = ttk.LabelFrame(parent, text=title, padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        for control in controls:
            if len(control) == 3 and callable(control[2]):
                # Button
                ttk.Button(section, text=control[0], 
                          command=control[2]).pack(fill=tk.X, pady=2)
            elif len(control) == 3:
                # Entry with label and units
                entry_frame = ttk.Frame(section)
                entry_frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(entry_frame, text=control[0]).pack(side=tk.LEFT)
                entry = ttk.Entry(entry_frame, textvariable=control[1], width=10)
                entry.pack(side=tk.LEFT, padx=(5, 5))
                if control[2]:
                    ttk.Label(entry_frame, text=control[2], 
                             style='Status.TLabel').pack(side=tk.LEFT)
    
    def _create_right_panel(self):
        """Create right panel with plot."""
        # Plot header
        plot_header = ttk.Frame(self.right_panel)
        plot_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(plot_header, text="Data Visualization", 
                 style='Subheader.TLabel').pack(side=tk.LEFT)
        
        # Plot controls on the right
        controls_frame = ttk.Frame(plot_header)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="💾 Save", 
                  command=self.save_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="🔄 Refresh", 
                  command=self.update_plot).pack(side=tk.LEFT, padx=2)
        
        # Plot area
        plot_container = ttk.Frame(self.right_panel)
        plot_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Initialize plot manager
        self.plot_manager = PlotManager(plot_container)
    
    def _create_status_bar(self, parent):
        """Create status bar."""
        self.status_bar = ttk.Frame(parent, style='Card.TFrame')
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(self.status_bar, text="Ready", 
                 style='Status.TLabel').pack(side=tk.LEFT, padx=10, pady=5)
    
    def apply_lowpass_filter(self):
        """Apply low pass filter to all channels."""
        if not self._validate_file_loaded():
            return
        
        try:
            cutoff = float(self.cutoff_freq.get())
            sample_rate = float(self.sample_rate.get())
            
            for channel in self.processed_data:
                filtered = DataProcessor.apply_low_pass_filter(
                    self.processed_data[channel], cutoff, sample_rate)
                self.processed_data[channel] = filtered.tolist()
            
            self._update_processing_info(f"Applied low-pass filter (cutoff={cutoff}Hz)")
            messagebox.showinfo("Success", f"Applied low-pass filter with cutoff {cutoff}Hz")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid filter parameters: {str(e)}")
    
    # Rest of methods remain the same as before...
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
            self._create_file_info_display()  # Update file info display
            self._populate_channel_table()
            self._reset_processing_state()
            
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
        """Create configuration for a channel with cleaned units."""
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
            else:
                # Clean up units - remove null characters and extra symbols
                units = units.replace('\x00', '').strip()
                # Remove common problematic characters
                units = ''.join(c for c in units if c.isprintable() and c not in '[]')
                if not units:
                    units = "N/A"
        except:
            units = "N/A"
        
        # First channel primary, others secondary by default
        axis = "Primary" if channel == 1 else "Secondary"
        
        return ChannelConfig(channel, name, units, axis)
    
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
        if hasattr(self, 'process_info'):
            self.process_info.config(text="No processing applied")
    
    def set_axis_selection(self, axis_type: str):
        """Set axis type for selected channels."""
        selected_items = self.channel_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "Please select channels first")
            return
        
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
    
    def _sync_channel_configs(self):
        """Sync channel configurations from tree view."""
        for item in self.channel_tree.get_children():
            values = self.channel_tree.item(item)['values']
            channel_num = int(values[0])
            if channel_num in self.channel_configs:
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
        if hasattr(self, 'process_info'):
            self.process_info.config(text=message)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = WDQAnalyzer(root)
    root.mainloop()


if __name__ == "__main__":
    main()