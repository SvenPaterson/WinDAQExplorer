"""
Unit tests for DataProcessor class.

Tests all static methods in the DataProcessor class to ensure
signal processing functions work correctly.
"""

import pytest
import numpy as np
from data_processor import DataProcessor


class TestDataProcessor:
    """Test cases for DataProcessor static methods."""
    
    def setup_method(self):
        """Setup test data for each test method."""
        # Simple test signals
        self.simple_data = [1, 2, 3, 4, 5]
        self.sine_wave = np.sin(np.linspace(0, 4*np.pi, 100))
        self.noisy_data = np.array([1, 10, 2, 9, 3, 8, 4, 7, 5])
        
    def test_moving_average_basic(self):
        """Test basic moving average functionality."""
        data = [1, 2, 3, 4, 5]
        result = DataProcessor.apply_moving_average(data, window_size=3)
        
        # Check that result is numpy array
        assert isinstance(result, np.ndarray)
        # Check that length is preserved
        assert len(result) == len(data)
        # Check some expected values (center should be exact average)
        assert abs(result[2] - 3.0) < 0.01  # Middle value should be (2+3+4)/3 = 3
        
    def test_moving_average_window_size_one(self):
        """Test moving average with window size 1 (should be identity)."""
        data = [1, 2, 3, 4, 5]
        result = DataProcessor.apply_moving_average(data, window_size=1)
        np.testing.assert_array_almost_equal(result, data)
        
    def test_moving_average_smooths_noise(self):
        """Test that moving average reduces noise."""
        # Create noisy signal
        noisy = self.noisy_data
        smoothed = DataProcessor.apply_moving_average(noisy, window_size=3)
        
        # Smoothed signal should have lower variance
        assert np.var(smoothed) < np.var(noisy)
        
    def test_moving_average_invalid_window(self):
        """Test moving average with invalid window size."""
        data = [1, 2, 3, 4, 5]
        
        with pytest.raises(ValueError, match="Window size must be positive"):
            DataProcessor.apply_moving_average(data, window_size=0)
            
        with pytest.raises(ValueError, match="Window size must be positive"):
            DataProcessor.apply_moving_average(data, window_size=-1)
            
    def test_moving_average_numpy_input(self):
        """Test moving average with numpy array input."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = DataProcessor.apply_moving_average(data, window_size=3)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == len(data)
        
    def test_resample_data_basic(self):
        """Test basic data resampling."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = DataProcessor.resample_data(data, factor=2)
        
        # Should return every 2nd element
        expected = np.array([1, 3, 5, 7, 9])
        np.testing.assert_array_equal(result, expected)
        
    def test_resample_data_factor_one(self):
        """Test resampling with factor 1 (should be identity)."""
        data = [1, 2, 3, 4, 5]
        result = DataProcessor.resample_data(data, factor=1)
        np.testing.assert_array_equal(result, data)
        
    def test_resample_data_large_factor(self):
        """Test resampling with large factor."""
        data = list(range(100))
        result = DataProcessor.resample_data(data, factor=10)
        
        # Should return every 10th element
        expected = list(range(0, 100, 10))
        np.testing.assert_array_equal(result, expected)
        
    def test_resample_data_invalid_factor(self):
        """Test resampling with invalid factor."""
        data = [1, 2, 3, 4, 5]
        
        with pytest.raises(ValueError, match="Resample factor must be positive"):
            DataProcessor.resample_data(data, factor=0)
            
        with pytest.raises(ValueError, match="Resample factor must be positive"):
            DataProcessor.resample_data(data, factor=-1)
            
    def test_low_pass_filter_basic(self):
        """Test basic low-pass filter functionality."""
        # Create signal with high and low frequency components
        t = np.linspace(0, 1, 1000)
        low_freq = np.sin(2 * np.pi * 5 * t)  # 5 Hz
        high_freq = np.sin(2 * np.pi * 50 * t)  # 50 Hz
        signal = low_freq + 0.5 * high_freq
        
        # Apply low-pass filter with cutoff at 10 Hz
        filtered = DataProcessor.apply_low_pass_filter(signal, cutoff_freq=10.0, sample_rate=1000.0)
        
        # Check that result is numpy array and same length
        assert isinstance(filtered, np.ndarray)
        assert len(filtered) == len(signal)
        
        # High frequency component should be significantly reduced
        # (This is a simplified test - in practice you'd analyze frequency domain)
        assert np.std(filtered) < np.std(signal)
        
    def test_low_pass_filter_removes_high_freq(self):
        """Test that low-pass filter removes high frequencies."""
        # Pure high frequency signal
        t = np.linspace(0, 1, 1000)
        high_freq_signal = np.sin(2 * np.pi * 100 * t)  # 100 Hz
        
        # Filter with very low cutoff
        filtered = DataProcessor.apply_low_pass_filter(high_freq_signal, cutoff_freq=1.0, sample_rate=1000.0)
        
        # Filtered signal should be mostly zeros (high freq removed)
        assert np.max(np.abs(filtered)) < 0.1 * np.max(np.abs(high_freq_signal))
        
    def test_remove_offset_basic(self):
        """Test basic DC offset removal."""
        # Signal with DC offset
        data = np.array([5, 6, 7, 8, 9])  # Mean is 7
        result = DataProcessor.remove_offset(data)
        
        # Mean should be approximately zero
        assert abs(np.mean(result)) < 1e-10
        
        # Shape should be preserved
        expected = np.array([-2, -1, 0, 1, 2])
        np.testing.assert_array_almost_equal(result, expected)
        
    def test_remove_offset_zero_mean(self):
        """Test offset removal on zero-mean signal."""
        data = np.array([-2, -1, 0, 1, 2])  # Already zero mean
        result = DataProcessor.remove_offset(data)
        
        # Should be approximately unchanged
        np.testing.assert_array_almost_equal(result, data, decimal=10)
        
    def test_normalize_data_minmax(self):
        """Test min-max normalization."""
        data = np.array([1, 2, 3, 4, 5])
        result = DataProcessor.normalize_data(data, method='minmax')
        
        # Should be in range [0, 1]
        assert np.min(result) >= 0
        assert np.max(result) <= 1
        assert abs(np.min(result) - 0.0) < 1e-10
        assert abs(np.max(result) - 1.0) < 1e-10
        
    def test_normalize_data_zscore(self):
        """Test z-score normalization."""
        data = np.array([1, 2, 3, 4, 5])
        result = DataProcessor.normalize_data(data, method='zscore')
        
        # Should have zero mean and unit variance
        assert abs(np.mean(result)) < 1e-10
        assert abs(np.std(result) - 1.0) < 1e-10
        
    def test_normalize_data_constant_signal(self):
        """Test normalization with constant signal."""
        data = np.array([5, 5, 5, 5, 5])  # No variation
        
        # Min-max should return zeros
        result_minmax = DataProcessor.normalize_data(data, method='minmax')
        np.testing.assert_array_equal(result_minmax, np.zeros_like(data))
        
        # Z-score should return zeros
        result_zscore = DataProcessor.normalize_data(data, method='zscore')
        np.testing.assert_array_equal(result_zscore, np.zeros_like(data))
        
    def test_normalize_data_invalid_method(self):
        """Test normalization with invalid method."""
        data = np.array([1, 2, 3, 4, 5])
        
        with pytest.raises(ValueError, match="Unknown normalization method"):
            DataProcessor.normalize_data(data, method='invalid')
            
    def test_empty_data_handling(self):
        """Test how functions handle empty data."""
        empty_data = np.array([])
        
        # Most functions should handle empty arrays gracefully
        result_ma = DataProcessor.apply_moving_average(empty_data, window_size=1)
        assert len(result_ma) == 0
        
        result_resample = DataProcessor.resample_data(empty_data, factor=2)
        assert len(result_resample) == 0
        
        result_offset = DataProcessor.remove_offset(empty_data)
        assert len(result_offset) == 0
        
    def test_single_element_data(self):
        """Test functions with single-element data."""
        single_data = np.array([42.0])
        
        # Moving average
        result_ma = DataProcessor.apply_moving_average(single_data, window_size=1)
        np.testing.assert_array_almost_equal(result_ma, single_data)
        
        # Resampling
        result_resample = DataProcessor.resample_data(single_data, factor=1)
        np.testing.assert_array_equal(result_resample, single_data)
        
        # Offset removal
        result_offset = DataProcessor.remove_offset(single_data)
        np.testing.assert_array_almost_equal(result_offset, [0.0])
        
    def test_list_vs_numpy_consistency(self):
        """Test that functions work consistently with lists and numpy arrays."""
        data_list = [1, 2, 3, 4, 5]
        data_array = np.array(data_list)
        
        # Moving average
        result_list = DataProcessor.apply_moving_average(data_list, window_size=3)
        result_array = DataProcessor.apply_moving_average(data_array, window_size=3)
        np.testing.assert_array_almost_equal(result_list, result_array)
        
        # Resampling
        result_list = DataProcessor.resample_data(data_list, factor=2)
        result_array = DataProcessor.resample_data(data_array, factor=2)
        np.testing.assert_array_equal(result_list, result_array)
        
        # Offset removal
        result_list = DataProcessor.remove_offset(data_list)
        result_array = DataProcessor.remove_offset(data_array)
        np.testing.assert_array_almost_equal(result_list, result_array)