"""Plot management module for WDQ Analyzer with dynamic subplot support."""

import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict

from models import ChannelConfig

# Suppress font warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')

# Set matplotlib backend and font
matplotlib.use('TkAgg')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']


class PlotManager:
    """Manages plot creation and updates with dynamic subplot support."""
    
    # Color palette for channels
    COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', 
              '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.fig = None
        self.axes = []
        self.canvas = None
        self._setup_plot()
    
    def _setup_plot(self):
        """Initialize plot components."""
        self.fig = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_plot(self, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                    channel_configs: Dict[int, ChannelConfig], filename: str):
        """Update the plot with new data using dynamic subplots."""
        # Clear figure
        self.fig.clear()
        self.axes = []
        
        # Group channels by subplot
        subplot_groups = defaultdict(lambda: {'primary': [], 'secondary': [], 'hidden': []})
        
        for channel, config in channel_configs.items():
            if config.axis.lower() == 'omit' or config.axis.lower() == 'hide':
                subplot_groups[config.subplot]['hidden'].append(channel)
            elif config.axis.lower() == 'primary':
                subplot_groups[config.subplot]['primary'].append(channel)
            elif config.axis.lower() == 'secondary':
                subplot_groups[config.subplot]['secondary'].append(channel)
        
        # Remove empty subplots and renumber
        active_subplots = {}
        subplot_index = 1
        for subplot_num in sorted(subplot_groups.keys()):
            group = subplot_groups[subplot_num]
            if group['primary'] or group['secondary']:  # Has visible channels
                active_subplots[subplot_index] = group
                subplot_index += 1
        
        if not active_subplots:
            # No channels to plot
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No channels selected for plotting\n\nSelect channels and assign to Primary or Secondary axis', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        num_subplots = len(active_subplots)
        
        # Create subplots
        for i, (subplot_idx, group) in enumerate(active_subplots.items(), 1):
            # Create primary axis
            ax_primary = self.fig.add_subplot(num_subplots, 1, i)
            self.axes.append(ax_primary)
            
            # Plot primary channels
            if group['primary']:
                self._plot_channels_on_axis(ax_primary, time_data, channel_data, channel_configs, 
                                          group['primary'], 'Primary', 'left')
            
            # Create secondary axis if needed
            ax_secondary = None
            if group['secondary']:
                ax_secondary = ax_primary.twinx()
                self.axes.append(ax_secondary)
                self._plot_channels_on_axis(ax_secondary, time_data, channel_data, channel_configs, 
                                          group['secondary'], 'Secondary', 'right')
            
            # Set subplot title and formatting
            if num_subplots == 1:
                title = f'{filename}'
            else:
                title = f'{filename} - Subplot {subplot_idx}'
            
            ax_primary.set_title(title, fontsize=10, pad=10)
            ax_primary.grid(True, alpha=0.3)
            
            # Only show x-label on bottom subplot
            if i == num_subplots:
                ax_primary.set_xlabel('Time (seconds)')
            else:
                ax_primary.set_xticklabels([])
        
        plt.tight_layout()
        self.canvas.draw()
    
    def _plot_channels_on_axis(self, ax, time_data: np.ndarray, channel_data: Dict[int, List[float]], 
                              channel_configs: Dict[int, ChannelConfig], channels: List[int], 
                              axis_type: str, legend_side: str):
        """Plot channels on a specific axis."""
        if not channels:
            return
        
        # Determine units for y-label
        units = set()
        for channel in channels:
            config = channel_configs[channel]
            if config.units != "N/A":
                units.add(config.units)
        
        # Create y-label
        if len(units) == 1:
            ylabel = f"{axis_type} ({list(units)[0]})"
        elif len(units) > 1:
            ylabel = f"{axis_type} (Mixed Units)"
        else:
            ylabel = axis_type
        
        ax.set_ylabel(ylabel)
        
        # Plot channels
        for i, channel in enumerate(channels):
            config = channel_configs[channel]
            
            # Use assigned color or auto-assign
            if config.color == "auto" or config.color == "#auto":
                color = self.COLORS[i % len(self.COLORS)]
            else:
                color = config.color
            
            # Use different line styles for secondary axis to distinguish from primary
            if axis_type == 'Secondary' and len(channels) > 1:
                linestyles = ['-', '--', '-.', ':']
                linestyle = linestyles[i % len(linestyles)]
                linewidth = 1.5
            else:
                linestyle = '-'
                linewidth = 2.0 if axis_type == 'Primary' else 1.5
            
            ax.plot(time_data, channel_data[channel], 
                   label=config.label, color=color, linewidth=linewidth, 
                   linestyle=linestyle, alpha=0.8)
        
        # Add legend
        if channels:
            # Position legend based on which side
            if legend_side == 'left':
                legend_loc = 'upper left'
            else:
                legend_loc = 'upper right'
            
            legend = ax.legend(loc=legend_loc, framealpha=0.9, fontsize=9)
            
            # Color the legend text to match the axis
            if axis_type == 'Secondary':
                for text in legend.get_texts():
                    text.set_color('darkred')
    
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