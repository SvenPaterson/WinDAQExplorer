"""Data processing module for WDQ Analyzer."""

import numpy as np
from typing import Union, List


class DataProcessor:
    """Handles data processing operations."""
    
    @staticmethod
    def apply_moving_average(data: Union[np.ndarray, List[float]], window_size: int) -> np.ndarray:
        """
        Apply moving average to data.
        
        Args:
            data: Input data array or list
            window_size: Size of the moving average window
            
        Returns:
            Processed data array
            
        Raises:
            ValueError: If window size is less than 1
        """
        if window_size < 1:
            raise ValueError("Window size must be positive")
        
        data_array = np.array(data)
        
        # Handle empty data
        if len(data_array) == 0:
            return data_array
        
        return np.convolve(data_array, np.ones(window_size) / window_size, mode='same')
    
    @staticmethod
    def resample_data(data: Union[np.ndarray, List[float]], factor: int) -> np.ndarray:
        """
        Downsample data by given factor.
        
        Args:
            data: Input data array or list
            factor: Downsampling factor
            
        Returns:
            Resampled data array
            
        Raises:
            ValueError: If resample factor is less than 1
        """
        if factor < 1:
            raise ValueError("Resample factor must be positive")
        
        data_array = np.array(data)
        return data_array[::factor]
    
    @staticmethod
    def apply_low_pass_filter(data: Union[np.ndarray, List[float]], cutoff_freq: float, 
                            sample_rate: float) -> np.ndarray:
        """
        Apply a simple low-pass filter using FFT.
        
        Args:
            data: Input data array or list
            cutoff_freq: Cutoff frequency in Hz
            sample_rate: Sampling rate in Hz
            
        Returns:
            Filtered data array
        """
        data_array = np.array(data)
        
        # FFT
        fft_data = np.fft.fft(data_array)
        frequencies = np.fft.fftfreq(len(data_array), 1/sample_rate)
        
        # Apply filter
        fft_data[np.abs(frequencies) > cutoff_freq] = 0
        
        # Inverse FFT
        filtered_data = np.real(np.fft.ifft(fft_data))
        
        return filtered_data
    
    @staticmethod
    def remove_offset(data: Union[np.ndarray, List[float]]) -> np.ndarray:
        """
        Remove DC offset from data.
        
        Args:
            data: Input data array or list
            
        Returns:
            Data with offset removed
        """
        data_array = np.array(data)
        return data_array - np.mean(data_array)
    
    @staticmethod
    def normalize_data(data: Union[np.ndarray, List[float]], method: str = 'minmax') -> np.ndarray:
        """
        Normalize data using specified method.
        
        Args:
            data: Input data array or list
            method: Normalization method ('minmax' or 'zscore')
            
        Returns:
            Normalized data array
        """
        data_array = np.array(data)
        
        if method == 'minmax':
            min_val = np.min(data_array)
            max_val = np.max(data_array)
            if max_val - min_val != 0:
                return (data_array - min_val) / (max_val - min_val)
            else:
                return np.zeros_like(data_array)
        
        elif method == 'zscore':
            mean = np.mean(data_array)
            std = np.std(data_array)
            if std != 0:
                return (data_array - mean) / std
            else:
                return np.zeros_like(data_array)
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")