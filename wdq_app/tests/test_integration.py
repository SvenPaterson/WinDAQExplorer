"""
Integration tests for WinDAQExplorer.

Tests the interaction between different components of the application.
"""

import pytest
import numpy as np
from models import ChannelConfig
from data_processor import DataProcessor


class TestDataFlowIntegration:
    """Test data flow between components."""
    
    def test_channel_config_with_processed_data(self):
        """Test that channel configuration works with processed data."""
        # Create sample data
        sample_data = np.sin(np.linspace(0, 4*np.pi, 100))
        
        # Create channel config
        config = ChannelConfig(channel_num=1, name="Sine Wave", units="V", axis="Primary")
        
        # Process the data
        processed = DataProcessor.apply_moving_average(sample_data, window_size=5)
        
        # Verify integration
        assert len(processed) == len(sample_data)
        assert config.label == "Sine Wave (V)"
        assert config.channel_num == 1
        
    def test_multiple_processing_steps(self):
        """Test chaining multiple processing operations."""
        # Start with noisy data
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 5 * t) + 0.1 * np.random.randn(1000)
        
        # Chain processing operations
        step1 = DataProcessor.apply_moving_average(signal, window_size=10)
        step2 = DataProcessor.resample_data(step1, factor=2)
        step3 = DataProcessor.remove_offset(step2)
        step4 = DataProcessor.normalize_data(step3, method='minmax')
        
        # Verify each step
        assert len(step1) == len(signal)  # Moving average preserves length
        assert len(step2) == len(step1) // 2  # Resampling reduces length
        assert abs(np.mean(step3)) < 1e-10  # Offset removal makes mean ~0
        assert np.min(step4) >= 0 and np.max(step4) <= 1  # Normalization bounds
        
    def test_channel_config_serialization_with_special_chars(self):
        """Test channel config serialization with various character types."""
        # Test with special characters that might appear in real data
        config = ChannelConfig(
            channel_num=1,
            name="Temperature (°C)",
            units="°C",
            axis="Primary"
        )
        
        # Serialize and deserialize
        data = config.to_dict()
        restored = ChannelConfig.from_dict(data)
        
        # Verify integrity
        assert restored.name == "Temperature (°C)"
        assert restored.units == "°C"
        assert restored.label == "Temperature (°C) (°C)"
        
    def test_data_processor_with_real_world_scenarios(self):
        """Test data processor with realistic signal processing scenarios."""
        # Simulate accelerometer data with noise and drift
        t = np.linspace(0, 10, 10000)  # 10 seconds at 1kHz
        vibration = 0.1 * np.sin(2 * np.pi * 60 * t)  # 60 Hz vibration
        noise = 0.05 * np.random.randn(len(t))
        drift = 0.01 * t  # Linear drift
        signal = vibration + noise + drift
        
        # Typical processing chain for vibration analysis
        # 1. Remove DC offset/drift
        detrended = DataProcessor.remove_offset(signal)
        
        # 2. Apply low-pass filter to remove noise
        filtered = DataProcessor.apply_low_pass_filter(detrended, cutoff_freq=100, sample_rate=1000)
        
        # 3. Smooth with moving average
        smoothed = DataProcessor.apply_moving_average(filtered, window_size=10)
        
        # Verify processing chain
        assert len(smoothed) == len(signal)
        assert np.std(smoothed) < np.std(signal)  # Should be smoother
        assert abs(np.mean(detrended)) < abs(np.mean(signal))  # Should remove drift
        
    def test_error_propagation_through_processing_chain(self):
        """Test that errors propagate correctly through processing steps."""
        # Test with invalid parameters
        data = np.array([1, 2, 3, 4, 5])
        
        # Should fail early with invalid window size
        with pytest.raises(ValueError):
            DataProcessor.apply_moving_average(data, window_size=0)
            
        # Should fail with invalid resample factor
        with pytest.raises(ValueError):
            DataProcessor.resample_data(data, factor=-1)
            
        # Should fail with invalid normalization method
        with pytest.raises(ValueError):
            DataProcessor.normalize_data(data, method='invalid')


class TestChannelConfigIntegration:
    """Test channel configuration integration scenarios."""
    
    def test_multi_channel_configuration(self):
        """Test configuration of multiple channels with different properties."""
        channels = []
        
        # Create different types of channels
        channels.append(ChannelConfig(1, "Temperature", "°C", "Primary"))
        channels.append(ChannelConfig(2, "Pressure", "psi", "Secondary"))
        channels.append(ChannelConfig(3, "Vibration", "g", "Secondary"))
        channels.append(ChannelConfig(4, "Unused", "N/A", "Omit"))
        
        # Test serialization of all channels
        serialized = [ch.to_dict() for ch in channels]
        restored = [ChannelConfig.from_dict(data) for data in serialized]
        
        # Verify all channels restored correctly
        for original, restored_ch in zip(channels, restored):
            assert original.channel_num == restored_ch.channel_num
            assert original.name == restored_ch.name
            assert original.units == restored_ch.units
            assert original.axis == restored_ch.axis
            assert original.label == restored_ch.label
            
    def test_channel_grouping_by_axis(self):
        """Test grouping channels by axis assignment."""
        channels = [
            ChannelConfig(1, "Temp1", "°C", "Primary"),
            ChannelConfig(2, "Temp2", "°C", "Primary"),
            ChannelConfig(3, "Pressure", "psi", "Secondary"),
            ChannelConfig(4, "Flow", "L/min", "Secondary"),
            ChannelConfig(5, "Unused", "N/A", "Omit"),
        ]
        
        # Group by axis
        primary = [ch for ch in channels if ch.axis == "Primary"]
        secondary = [ch for ch in channels if ch.axis == "Secondary"]
        omitted = [ch for ch in channels if ch.axis == "Omit"]
        
        # Verify grouping
        assert len(primary) == 2
        assert len(secondary) == 2
        assert len(omitted) == 1
        
        # Verify channel numbers
        assert {ch.channel_num for ch in primary} == {1, 2}
        assert {ch.channel_num for ch in secondary} == {3, 4}
        assert {ch.channel_num for ch in omitted} == {5}


class TestEdgeCaseIntegration:
    """Test edge cases in component integration."""
    
    def test_empty_data_through_processing_chain(self):
        """Test processing chain with empty data."""
        empty_data = np.array([])
        
        # Should handle empty data gracefully
        result1 = DataProcessor.apply_moving_average(empty_data, window_size=1)
        result2 = DataProcessor.resample_data(result1, factor=1)
        result3 = DataProcessor.remove_offset(result2)
        
        # All results should be empty
        assert len(result1) == 0
        assert len(result2) == 0
        assert len(result3) == 0
        
    def test_single_sample_processing(self):
        """Test processing with single data point."""
        single_data = np.array([42.0])
        
        # Should handle single point gracefully
        result1 = DataProcessor.apply_moving_average(single_data, window_size=1)
        result2 = DataProcessor.resample_data(result1, factor=1)
        result3 = DataProcessor.remove_offset(result2)
        result4 = DataProcessor.normalize_data(result3, method='minmax')
        
        # Verify results
        assert len(result1) == 1
        assert len(result2) == 1
        assert len(result3) == 1
        assert len(result4) == 1
        assert result4[0] == 0.0  # Single point normalized to 0
        
    def test_large_data_processing(self):
        """Test processing with large datasets."""
        # Create large dataset (1 million points)
        large_data = np.random.randn(1_000_000)
        
        # Should handle large data efficiently
        result = DataProcessor.apply_moving_average(large_data, window_size=100)
        
        # Verify result
        assert len(result) == len(large_data)
        assert np.std(result) < np.std(large_data)  # Should be smoother