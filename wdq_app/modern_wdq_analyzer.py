"""
Modern WDQ Analyzer UI - Clean separation of UI and business logic.
This file focuses only on the user interface and delegates all business logic to WDQController.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional

from wdq_controller import WDQController
from plot_manager import PlotManager


class ModernWDQAnalyzer:
    """Modern UI for WDQ data analysis with clean architecture."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WDQ Data Analyzer")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Business logic controller
        self.controller = WDQController()
        self._setup_controller_callbacks()
        
        # Configure modern styling
        self._configure_styling()
        
        # GUI components
        self.main_paned = None
        self.left_panel = None
        self.right_panel = None
        self.channel_tree = None
        self.file_info_frame = None
        self.status_bar = None
        self.plot_manager = None
        
        # UI state variables
        self.ma_window = tk.StringVar(value="10")
        self.resample_factor = tk.StringVar(value="2")
        self.cutoff_freq = tk.StringVar(value="10.0")
        self.sample_rate = tk.StringVar(value="100.0")
        self.normalize_method = tk.StringVar(value="minmax")
        
        # Channel selection for processing
        self.channel_vars = {}  # Will hold checkboxes for each channel
        self.checkbox_frame = None
        
        # Status labels for updates
        self.process_info = None
        self.status_label = None
        
        self._create_gui()
    
    def _setup_controller_callbacks(self):
        """Setup callbacks from controller to update UI."""
        self.controller.set_callbacks(
            file_loaded=self._on_file_loaded,
            processing_applied=self._on_processing_applied,
            data_reset=self._on_data_reset,
            error=self._on_error,
            plot_update=self._on_plot_update
        )
    
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
        style.configure('Success.TLabel', font=('Segoe UI', 9), foreground='#2d8f2d')
        style.configure('Error.TLabel', font=('Segoe UI', 9), foreground='#cc3333')
    
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
                             command=self._load_file)
        load_btn.pack(side=tk.RIGHT)
        
        # File info section
        self.file_info_frame = ttk.Frame(left_header)
        self.file_info_frame.pack(fill=tk.X)
        
        self._update_file_info_display()
    
    def _update_file_info_display(self):
        """Update file information display."""
        # Clear existing
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        file_info = self.controller.get_file_info()
        
        if not file_info.get("loaded", False):
            ttk.Label(self.file_info_frame, text="No file loaded", 
                     style='Status.TLabel').pack(anchor=tk.W)
            return
        
        # File info grid
        info_frame = ttk.Frame(self.file_info_frame)
        info_frame.pack(fill=tk.X)
        
        # File name (prominent)
        ttk.Label(info_frame, text=f"File: {file_info['filename']}", 
                 style='Subheader.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        # Stats in a clean row
        stats_frame = ttk.Frame(info_frame)
        stats_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        stats = [
            ("Channels", str(file_info['channels'])),
            ("Samples", f"{file_info['samples']:,}"),
            ("Sample Rate", f"{file_info['sample_rate']:.1f} Hz"),
            ("Duration", f"{file_info['duration']:.1f} sec")
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
        
        # Statistics tab
        self._create_statistics_tab(left_notebook)
    
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
        
        # Treeview with scrollbar - now includes Processing column
        columns = ('Ch#', 'Name', 'Units', 'Axis', 'Processing')
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.channel_tree = ttk.Treeview(tree_container, columns=columns, 
                                        show='headings', height=8)
        
        # Configure columns with better widths
        col_widths = {'Ch#': 40, 'Name': 100, 'Units': 60, 'Axis': 70, 'Processing': 100}
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
                  command=lambda: self._set_axis_selection('Primary')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(axis_btn_frame, text="Secondary", 
                  command=lambda: self._set_axis_selection('Secondary')).pack(side=tk.LEFT, padx=5)
        ttk.Button(axis_btn_frame, text="Hide", 
                  command=lambda: self._set_axis_selection('Omit')).pack(side=tk.LEFT, padx=5)
    
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
        
        # Channel selection frame
        self._create_channel_selection_frame(scrollable_frame)
        
        # Moving Average section
        self._create_processing_section(scrollable_frame, "Moving Average", [
            ("Window Size:", self.ma_window, "samples"),
            ("Apply to Selected", None, lambda: self._apply_moving_average())
        ])
        
        # Resampling section
        self._create_processing_section(scrollable_frame, "Resampling", [
            ("Factor:", self.resample_factor, ""),
            ("Apply to Selected", None, lambda: self._apply_resampling())
        ])
        
        # Low Pass Filter section
        self._create_processing_section(scrollable_frame, "Low Pass Filter", [
            ("Cutoff Freq:", self.cutoff_freq, "Hz"),
            ("Sample Rate:", self.sample_rate, "Hz"),
            ("Apply to Selected", None, lambda: self._apply_lowpass_filter())
        ])
        
        # Normalization section
        norm_section = ttk.LabelFrame(scrollable_frame, text="Normalization", padding=10)
        norm_section.pack(fill=tk.X, padx=10, pady=5)
        
        # Method selection
        method_frame = ttk.Frame(norm_section)
        method_frame.pack(fill=tk.X, pady=2)
        ttk.Label(method_frame, text="Method:").pack(side=tk.LEFT)
        method_combo = ttk.Combobox(method_frame, textvariable=self.normalize_method, 
                                   values=['minmax', 'zscore'], state='readonly', width=10)
        method_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(norm_section, text="Apply to Selected", 
                  command=self._apply_normalization).pack(fill=tk.X, pady=2)
        
        # Offset removal section
        offset_section = ttk.LabelFrame(scrollable_frame, text="DC Offset", padding=10)
        offset_section.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(offset_section, text="Remove from Selected", 
                  command=self._apply_offset_removal).pack(fill=tk.X, pady=2)
        
        # Action buttons (remove replot button)
        action_frame = ttk.LabelFrame(scrollable_frame, text="Actions", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="🔄 Reset to Original", 
                  command=self._reset_data).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="💾 Export CSV", 
                  command=self._export_data).pack(fill=tk.X, pady=2)
        
        # Processing status
        status_frame = ttk.Frame(scrollable_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_frame, text="Processing Status:", 
                 style='Status.TLabel').pack(anchor=tk.W)
        self.process_info = ttk.Label(status_frame, text="No processing applied", 
                                     style='Success.TLabel')
        self.process_info.pack(anchor=tk.W, pady=(2, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_channel_selection_frame(self, parent):
        """Create channel selection checkboxes for processing."""
        selection_frame = ttk.LabelFrame(parent, text="Select Channels for Processing", padding=10)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Instructions
        ttk.Label(selection_frame, text="Select which channels to apply processing to:", 
                 style='Status.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # Container for checkboxes
        self.checkbox_frame = ttk.Frame(selection_frame)
        self.checkbox_frame.pack(fill=tk.X)
        
        # Note: Checkboxes will be populated when file is loaded
        self.no_channels_label = ttk.Label(self.checkbox_frame, text="No file loaded", 
                                          style='Status.TLabel')
        self.no_channels_label.pack(anchor=tk.W)
    
    def _update_channel_checkboxes(self):
        """Update the channel selection checkboxes."""
        # Clear existing checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        
        self.channel_vars = {}
        
        if not self.controller.is_file_loaded():
            ttk.Label(self.checkbox_frame, text="No file loaded", 
                     style='Status.TLabel').pack(anchor=tk.W)
            return
        
        # Create checkboxes for each channel
        channel_data = self.controller.get_channel_data()
        
        for i, (channel_num, name, units, axis) in enumerate(channel_data):
            self.channel_vars[channel_num] = tk.BooleanVar()
            
            checkbox = ttk.Checkbutton(
                self.checkbox_frame, 
                text=f"Ch{channel_num}: {name}",
                variable=self.channel_vars[channel_num]
            )
            
            # Arrange in rows of 2
            row = i // 2
            col = i % 2
            checkbox.grid(row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)
        
        # Clear all button
        clear_btn = ttk.Button(self.checkbox_frame, text="Clear All", 
                              command=self._clear_channel_selection)
        clear_btn.grid(row=(len(channel_data) + 1) // 2, column=0, sticky=tk.W, pady=(10, 0))
    
    def _clear_channel_selection(self):
        """Clear all channel selections."""
        for var in self.channel_vars.values():
            var.set(False)
    
    def _get_selected_channels(self) -> List[int]:
        """Get list of currently selected channels."""
        selected = []
        for channel, var in self.channel_vars.items():
            if var.get():
                selected.append(channel)
        return selected
    
    def _create_statistics_tab(self, notebook):
        """Create statistics display tab."""
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        
        # Header
        header_frame = ttk.Frame(stats_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="Channel Statistics", 
                 style='Subheader.TLabel').pack(anchor=tk.W)
        
        # Refresh button
        ttk.Button(header_frame, text="🔄 Refresh", 
                  command=self._update_statistics).pack(side=tk.RIGHT)
        
        # Statistics display area
        self.stats_text = tk.Text(stats_frame, wrap=tk.WORD, height=15, 
                                 font=('Consolas', 9))
        stats_scroll = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, 
                                   command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=(0, 10))
    
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
        
        # Plot controls on the right (remove refresh since it's automatic)
        controls_frame = ttk.Frame(plot_header)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="💾 Save", 
                  command=self._save_plot).pack(side=tk.LEFT, padx=2)
        
        # Plot area
        plot_container = ttk.Frame(self.right_panel)
        plot_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Initialize plot manager
        self.plot_manager = PlotManager(plot_container)
    
    def _create_status_bar(self, parent):
        """Create status bar."""
        self.status_bar = ttk.Frame(parent, style='Card.TFrame')
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready", 
                                     style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
    
    # UI Event Handlers
    def _load_file(self):
        """Handle file loading UI interaction."""
        filename = filedialog.askopenfilename(
            title="Select WDQ File",
            filetypes=[("WDQ Files", "*.wdq"), ("All Files", "*.*")]
        )
        
        if filename:
            self._update_status("Loading file...")
            success = self.controller.load_file(filename)
            if success:
                self._update_status("File loaded successfully")
    
    def _set_axis_selection(self, axis_type: str):
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
            
            # Update controller - this will automatically trigger plot update
            self.controller.update_channel_axis(channel_num, axis_type)
    
    def _update_plot(self):
        """Update the plot with current data."""
        if not self.controller.is_file_loaded():
            return  # Don't show warning, just silently return
        
        self._update_status("Updating plot...")
        time_data, processed_data, channel_configs = self.controller.get_plot_data()
        
        self.plot_manager.update_plot(
            time_data, processed_data, channel_configs, 
            self.controller.get_file_info()['filename']
        )
        self._update_status("Ready")
    
    def _apply_moving_average(self):
        """Apply moving average to selected channels."""
        try:
            window = int(self.ma_window.get())
            selected_channels = self._get_selected_channels()
            success = self.controller.apply_moving_average(window, selected_channels)
            if success:
                self._clear_channel_selection()  # Clear selection after apply
        except ValueError:
            messagebox.showerror("Error", "Invalid window size")
    
    def _apply_resampling(self):
        """Apply resampling to selected channels."""
        try:
            factor = int(self.resample_factor.get())
            selected_channels = self._get_selected_channels()
            success = self.controller.apply_resampling(factor, selected_channels)
            if success:
                self._clear_channel_selection()  # Clear selection after apply
        except ValueError:
            messagebox.showerror("Error", "Invalid resample factor")
    
    def _apply_lowpass_filter(self):
        """Apply low pass filter to selected channels."""
        try:
            cutoff = float(self.cutoff_freq.get())
            sample_rate = float(self.sample_rate.get())
            selected_channels = self._get_selected_channels()
            success = self.controller.apply_lowpass_filter(cutoff, sample_rate, selected_channels)
            if success:
                self._clear_channel_selection()  # Clear selection after apply
        except ValueError:
            messagebox.showerror("Error", "Invalid filter parameters")
    
    def _apply_normalization(self):
        """Apply normalization to selected channels."""
        method = self.normalize_method.get()
        selected_channels = self._get_selected_channels()
        success = self.controller.apply_normalization(method, selected_channels)
        if success:
            self._clear_channel_selection()  # Clear selection after apply
    
    def _apply_offset_removal(self):
        """Apply offset removal to selected channels."""
        selected_channels = self._get_selected_channels()
        success = self.controller.apply_offset_removal(selected_channels)
        if success:
            self._clear_channel_selection()  # Clear selection after apply
    
    def _reset_data(self):
        """Reset data through controller."""
        self.controller.reset_data()
    
    def _save_plot(self):
        """Save the current plot."""
        if not self.controller.is_file_loaded():
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        default_name = self.controller.get_default_plot_name()
        saved_file = self.plot_manager.save_plot(default_name)
        
        if saved_file:
            messagebox.showinfo("Success", f"Plot saved to {saved_file}")
    
    def _export_data(self):
        """Export processed data to CSV."""
        if not self.controller.is_file_loaded():
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        default_name = self.controller.get_default_export_name()
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            success = self.controller.export_to_csv(filename)
            if success:
                messagebox.showinfo("Success", f"Data exported to {filename}")
    
    def _update_statistics(self):
        """Update the statistics display."""
        if not self.controller.is_file_loaded():
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "No file loaded")
            return
        
        stats = self.controller.get_channel_statistics()
        
        # Clear and update text
        self.stats_text.delete(1.0, tk.END)
        
        if not stats:
            self.stats_text.insert(1.0, "No data available")
            return
        
        # Format statistics nicely
        output = "Channel Statistics:\n\n"
        
        for channel, data in stats.items():
            output += f"Channel {channel}: {data['name']}\n"
            output += f"  Units: {data['units']}\n"
            output += f"  Samples: {data['samples']:,}\n"
            output += f"  Range: {data['min']:.3f} to {data['max']:.3f}\n"
            output += f"  Mean: {data['mean']:.3f}\n"
            output += f"  Std Dev: {data['std']:.3f}\n\n"
        
        self.stats_text.insert(1.0, output)
    
    def _update_status(self, message: str):
        """Update status bar message."""
        if self.status_label:
            self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _populate_channel_table(self):
        """Populate channel configuration table with processing info."""
        # Clear existing items
        for item in self.channel_tree.get_children():
            self.channel_tree.delete(item)
        
        # Get channel data from controller
        channel_data = self.controller.get_channel_data()
        processing_info = self.controller.get_channel_processing_info()
        
        # Add channels with processing info
        for channel_num, name, units, axis in channel_data:
            processing = processing_info.get(channel_num, "None")
            self.channel_tree.insert('', 'end', 
                                   values=(channel_num, name, units, axis, processing))
    
    # Controller Callback Handlers
    def _on_file_loaded(self, file_info: Dict):
        """Called when controller loads a file."""
        self._update_file_info_display()
        self._populate_channel_table()
        self._update_channel_checkboxes()  # Update checkboxes when file loads
        self._update_statistics()
    
    def _on_processing_applied(self, message: str, success: bool = True):
        """Called when controller applies processing."""
        if self.process_info:
            style = 'Success.TLabel' if success else 'Error.TLabel'
            self.process_info.config(text=message, style=style)
        
        self._update_statistics()  # Update stats after processing
        self._populate_channel_table()  # Update processing info in table
        
        # Don't show success message box since plot updates automatically provide feedback
        if not success:
            messagebox.showerror("Error", message)
    
    def _on_data_reset(self, message: str):
        """Called when controller resets data."""
        if self.process_info:
            self.process_info.config(text=message, style='Success.TLabel')
        
        self._update_statistics()
        self._populate_channel_table()  # Update processing info in table
        # Don't show message box since plot update provides visual feedback
    
    def _on_plot_update(self):
        """Called when controller wants to update the plot."""
        self._update_plot()
    
    def _on_error(self, error_message: str):
        """Called when controller encounters an error."""
        messagebox.showerror("Error", error_message)
        self._update_status(f"Error: {error_message}")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = ModernWDQAnalyzer(root)
    root.mainloop()


if __name__ == "__main__":
    main()