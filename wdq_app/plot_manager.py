"""Plot management module for WDQ Analyzer."""

import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, List, Optional

from models import ChannelConfig

# Suppress font warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')

# Set matplotlib backend and font
matplotlib.use('TkAgg')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']


class PlotManager:
    """Manages plot creation and updates."""
    
    # Color palette for secondary channels
    COLORS = ['r', 'g', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown', 'pink']
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.fig = None
        self.axes = []
        self.canvas = None
        self._setup_plot()
    
    def _setup_plot(self):
        """Initialize plot components."""
        self.fig = plt.figure(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_plot(self, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                    channel_configs: Dict[int, ChannelConfig], filename: str):
        """Update the plot with new data."""
        # Clear figure
        self.fig.clear()
        self.axes = []
        
        # Separate channels by axis
        primary_channels = [ch for ch, config in channel_configs.items() 
                          if config.axis == "Primary"]
        secondary_channels = [ch for ch, config in channel_configs.items() 
                            if config.axis == "Secondary"]
        
        # Determine subplot configuration
        num_plots = 0
        if primary_channels:
            num_plots += 1
        if secondary_channels:
            num_plots += 1
        
        if num_plots == 0:
            # No channels to plot
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No channels selected for plotting', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Create subplots
        plot_index = 1
        
        # Plot primary channels
        if primary_channels:
            ax1 = self.fig.add_subplot(num_plots, 1, plot_index)
            self.axes.append(ax1)
            self._plot_channels(ax1, time_data, channel_data, channel_configs, 
                              primary_channels, f'Primary Channels - {filename}', 'Primary Channels')
            plot_index += 1
        
        # Plot secondary channels
        if secondary_channels:
            ax2 = self.fig.add_subplot(num_plots, 1, plot_index)
            self.axes.append(ax2)
            self._plot_channels(ax2, time_data, channel_data, channel_configs, 
                              secondary_channels, 'Secondary Channels', 'Secondary Channels',
                              use_colors=True)
        
        plt.tight_layout()
        self.canvas.draw()
    
    def _plot_channels(self, ax, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                      channel_configs: Dict[int, ChannelConfig], channels: List[int], 
                      title: str, ylabel: str, use_colors: bool = False):
        """Plot channels on given axis."""
        for i, channel in enumerate(channels):
            config = channel_configs[channel]
            
            # Set color and line style
            if use_colors:
                color = self.COLORS[i % len(self.COLORS)]
                linewidth = 1
            else:
                color = None  # Let matplotlib choose
                linewidth = 1.5
            
            ax.plot(time_data, channel_data[channel], 
                   label=config.label, linewidth=linewidth, color=color)
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel(ylabel)
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_title(title)
    
    def save_plot(self, default_filename: str = "plot.png") -> Optional[str]:
        """Save the current plot to file."""
        filename = filedialog.asksaveasfilename(
            title="Save Plot",
            defaultextension=".png",
            initialfile=default_filename,
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return filename
        return None
    
    def clear_plot(self):
        """Clear the current plot."""
        self.fig.clear()
        self.axes = []
        self.canvas.draw()