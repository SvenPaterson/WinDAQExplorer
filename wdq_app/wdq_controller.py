"""
Business logic controller for WDQ Analyzer.
Handles all data operations, file I/O, and processing logic.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import windaq as wdq
from pathlib import Path

from models import ChannelConfig
from data_processor import DataProcessor


class WDQController:
    """Controller class that handles all business logic for WDQ analysis."""
    
    def __init__(self):
        # Core data
        self.wfile: Optional[wdq.windaq] = None
        self.original_data: Dict[int, List[float]] = {}
        self.processed_data: Dict[int, List[float]] = {}
        self.time_data: Optional[np.ndarray] = None
        self.filename: str = ""
        self.channel_configs: Dict[int, ChannelConfig] = {}
        
        # Processing state
        self.processing_history: List[str] = []
        
        # Callbacks for UI updates
        self.on_file_loaded = None
        self.on_processing_applied = None
        self.on_data_reset = None
        self.on_error = None
    
    def set_callbacks(self, file_loaded=None, processing_applied=None, 
                     data_reset=None, error=None):
        """Set callback functions for UI updates."""
        self.on_file_loaded = file_loaded
        self.on_processing_applied = processing_applied
        self.on_data_reset = data_reset
        self.on_error = error
    
    def load_file(self, filepath: str) -> bool:
        """
        Load WDQ file and extract data.
        
        Args:
            filepath: Path to the WDQ file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._load_wdq_file(filepath)
            self._reset_processing_state()
            
            if self.on_file_loaded:
                self.on_file_loaded(self.get_file_info())
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to load file: {str(e)}")
            return False
    
    def _load_wdq_file(self, filepath: str):
        """Internal method to load WDQ file."""
        self.wfile = wdq.windaq(filepath)
        self.filename = Path(filepath).name
        
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
    
    def get_file_info(self) -> Dict:
        """Get file information for display."""
        if not self.wfile:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "filename": self.filename,
            "channels": self.wfile.nChannels,
            "samples": int(self.wfile.nSample),
            "sample_rate": 1/self.wfile.timeStep,
            "duration": self.wfile.nSample * self.wfile.timeStep
        }
    
    def get_channel_data(self) -> List[Tuple]:
        """Get channel data for table display."""
        if not self.channel_configs:
            return []
        
        return [(config.channel_num, config.name, config.units, config.axis) 
                for config in self.channel_configs.values()]
    
    def update_channel_axis(self, channel: int, axis: str):
        """Update the axis assignment for a channel."""
        if channel in self.channel_configs:
            self.channel_configs[channel].axis = axis
    
    def get_plot_data(self) -> Tuple[np.ndarray, Dict[int, List[float]], Dict[int, ChannelConfig]]:
        """Get data for plotting."""
        return self.time_data, self.processed_data, self.channel_configs
    
    def apply_moving_average(self, window_size: int) -> bool:
        """Apply moving average to all channels."""
        if not self._validate_loaded():
            return False
        
        try:
            for channel in self.processed_data:
                processed = DataProcessor.apply_moving_average(
                    self.processed_data[channel], window_size)
                self.processed_data[channel] = processed.tolist()
            
            message = f"Applied moving average (window={window_size})"
            self._update_processing_info(message)
            
            if self.on_processing_applied:
                self.on_processing_applied(message, success=True)
            
            return True
            
        except ValueError as e:
            error_msg = f"Invalid window size: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return False
    
    def apply_resampling(self, factor: int) -> bool:
        """Apply resampling to data."""
        if not self._validate_loaded():
            return False
        
        try:
            # Resample time data
            self.time_data = DataProcessor.resample_data(self.time_data, factor)
            
            # Resample channel data
            for channel in self.processed_data:
                resampled = DataProcessor.resample_data(
                    self.processed_data[channel], factor)
                self.processed_data[channel] = resampled.tolist()
            
            message = f"Resampled by factor {factor}"
            self._update_processing_info(message)
            
            if self.on_processing_applied:
                self.on_processing_applied(message, success=True)
            
            return True
            
        except ValueError as e:
            error_msg = f"Invalid resample factor: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return False
    
    def apply_lowpass_filter(self, cutoff_freq: float, sample_rate: float) -> bool:
        """Apply low pass filter to all channels."""
        if not self._validate_loaded():
            return False
        
        try:
            for channel in self.processed_data:
                filtered = DataProcessor.apply_low_pass_filter(
                    self.processed_data[channel], cutoff_freq, sample_rate)
                self.processed_data[channel] = filtered.tolist()
            
            message = f"Applied low-pass filter (cutoff={cutoff_freq}Hz)"
            self._update_processing_info(message)
            
            if self.on_processing_applied:
                self.on_processing_applied(message, success=True)
            
            return True
            
        except ValueError as e:
            error_msg = f"Invalid filter parameters: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return False
    
    def apply_offset_removal(self) -> bool:
        """Remove DC offset from all channels."""
        if not self._validate_loaded():
            return False
        
        try:
            for channel in self.processed_data:
                processed = DataProcessor.remove_offset(self.processed_data[channel])
                self.processed_data[channel] = processed.tolist()
            
            message = "Removed DC offset"
            self._update_processing_info(message)
            
            if self.on_processing_applied:
                self.on_processing_applied(message, success=True)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to remove offset: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return False
    
    def apply_normalization(self, method: str = 'minmax') -> bool:
        """Normalize data using specified method."""
        if not self._validate_loaded():
            return False
        
        try:
            for channel in self.processed_data:
                normalized = DataProcessor.normalize_data(
                    self.processed_data[channel], method)
                self.processed_data[channel] = normalized.tolist()
            
            message = f"Applied {method} normalization"
            self._update_processing_info(message)
            
            if self.on_processing_applied:
                self.on_processing_applied(message, success=True)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to normalize: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return False
    
    def reset_data(self) -> bool:
        """Reset to original data."""
        if not self.wfile:
            return False
        
        self.time_data = self.wfile.time()
        for channel in self.original_data:
            self.processed_data[channel] = self.original_data[channel].copy()
        
        self._reset_processing_state()
        message = "Reset to original data"
        self._update_processing_info(message)
        
        if self.on_data_reset:
            self.on_data_reset(message)
        
        return True
    
    def export_to_csv(self, filepath: str) -> bool:
        """Export processed data to CSV file."""
        if not self._validate_loaded():
            return False
        
        try:
            data_dict = {'Time': self.time_data}
            
            for channel, config in self.channel_configs.items():
                data_dict[config.label] = self.processed_data[channel]
            
            df = pd.DataFrame(data_dict)
            df.to_csv(filepath, index=False)
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to export data: {str(e)}")
            return False
    
    def get_processing_history(self) -> List[str]:
        """Get the processing history."""
        return self.processing_history.copy()
    
    def get_current_processing_status(self) -> str:
        """Get the current processing status."""
        if not self.processing_history:
            return "No processing applied"
        return self.processing_history[-1]
    
    def is_file_loaded(self) -> bool:
        """Check if a file is currently loaded."""
        return self.wfile is not None
    
    def get_default_export_name(self, suffix: str = "_data") -> str:
        """Get default filename for exports."""
        if not self.filename:
            return f"export{suffix}.csv"
        
        base_name = self.filename.rsplit('.', 1)[0]
        return f"{base_name}{suffix}.csv"
    
    def get_default_plot_name(self, suffix: str = "_plot") -> str:
        """Get default filename for plot exports."""
        if not self.filename:
            return f"plot{suffix}.png"
        
        base_name = self.filename.rsplit('.', 1)[0]
        return f"{base_name}{suffix}.png"
    
    def _validate_loaded(self) -> bool:
        """Internal validation that file is loaded."""
        if not self.wfile:
            if self.on_error:
                self.on_error("Please load a file first")
            return False
        return True
    
    def _reset_processing_state(self):
        """Reset processing state."""
        self.processing_history = []
    
    def _update_processing_info(self, message: str):
        """Update processing information."""
        self.processing_history.append(message)
    
    def get_channel_statistics(self) -> Dict:
        """Get basic statistics for all channels."""
        if not self.processed_data:
            return {}
        
        stats = {}
        for channel, data in self.processed_data.items():
            config = self.channel_configs[channel]
            data_array = np.array(data)
            
            stats[channel] = {
                'name': config.name,
                'units': config.units,
                'min': float(np.min(data_array)),
                'max': float(np.max(data_array)),
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array)),
                'samples': len(data_array)
            }
        
        return stats