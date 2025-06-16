"""
Unit tests for windaq module.

Tests the windaq.py file reader for WDQ format files.
Note: These tests require sample .wdq files to be fully functional.
"""

import pytest
import os
import tempfile
import struct
from unittest.mock import patch, mock_open
from windaq import windaq


class TestWinDAQ:
    """Test cases for windaq file reader."""
    
    def test_windaq_constructor_file_not_found(self):
        """Test that constructor raises appropriate error for missing files."""
        with pytest.raises(FileNotFoundError):
            windaq("nonexistent_file.wdq")
            
    def test_windaq_constructor_empty_filename(self):
        """Test constructor with empty filename."""
        with pytest.raises((FileNotFoundError, OSError)):
            windaq("")
            
    def test_windaq_constructor_none_filename(self):
        """Test constructor with None filename."""
        with pytest.raises(TypeError):
            windaq(None)
            
    def test_windaq_data_invalid_channel_number(self):
        """Test data() method with invalid channel numbers."""
        # This test requires a mock or real file to work properly
        # For now, we'll create a basic structure
        
        # We can't easily test this without a real file or complex mocking
        # This is a placeholder for when we have sample files
        pass
        
    def test_windaq_channel_numbers_validation(self):
        """Test that channel numbers are validated properly."""
        # Placeholder - requires sample file
        pass
        
    def test_windaq_time_array_properties(self):
        """Test properties of the time array returned by time()."""
        # Placeholder - requires sample file
        pass
        
    def test_windaq_units_handling(self):
        """Test unit string handling and cleaning."""
        # Placeholder - requires sample file
        pass
        
    def test_windaq_annotation_handling(self):
        """Test annotation/channel name handling."""
        # Placeholder - requires sample file
        pass


class TestWinDAQWithSampleFile:
    """
    Tests that require a sample .wdq file.
    
    These tests will be skipped if no sample file is available.
    To enable these tests, place a sample .wdq file in wdq_app/tests/data/sample.wdq
    """
    
    @pytest.fixture
    def sample_file_path(self):
        """Fixture to provide path to sample WDQ file."""
        test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        # Look for any .wdq file in the data directory (case insensitive)
        import glob
        wdq_files = glob.glob(os.path.join(test_data_dir, '*.wdq'))
        wdq_files.extend(glob.glob(os.path.join(test_data_dir, '*.WDQ')))  # Add uppercase
        
        if wdq_files:
            return wdq_files[0]  # Use the first .wdq file found
        else:
            # Fallback to expected filename for clear error message
            return os.path.join(test_data_dir, 'sample.wdq')
        
    @pytest.fixture
    def windaq_instance(self, sample_file_path):
        """Fixture to create windaq instance with sample file."""
        if not os.path.exists(sample_file_path):
            pytest.skip(f"Sample file not found: {sample_file_path}")
        return windaq(sample_file_path)
        
    def test_windaq_loads_sample_file(self, windaq_instance):
        """Test that sample file loads successfully."""
        assert windaq_instance is not None
        assert hasattr(windaq_instance, 'nChannels')
        assert windaq_instance.nChannels > 0
        
    def test_windaq_channel_count(self, windaq_instance):
        """Test that channel count is reasonable."""
        assert windaq_instance.nChannels >= 1
        assert windaq_instance.nChannels <= 256  # Reasonable upper bound
        
    def test_windaq_sample_count(self, windaq_instance):
        """Test that sample count is reasonable."""
        assert windaq_instance.nSample > 0
        assert isinstance(windaq_instance.nSample, (int, float))
        
    def test_windaq_time_step(self, windaq_instance):
        """Test that time step is positive."""
        assert windaq_instance.timeStep > 0
        
    def test_windaq_time_array(self, windaq_instance):
        """Test properties of time array."""
        time_array = windaq_instance.time()
        
        assert len(time_array) == int(windaq_instance.nSample)
        assert time_array[0] >= 0  # Should start at or near zero
        assert all(time_array[i] <= time_array[i+1] for i in range(len(time_array)-1))  # Should be monotonic
        
    def test_windaq_channel_data(self, windaq_instance):
        """Test data retrieval for all channels."""
        for channel in range(1, windaq_instance.nChannels + 1):
            data = windaq_instance.data(channel)
            
            assert len(data) == int(windaq_instance.nSample)
            assert all(isinstance(x, (int, float)) for x in data[:10])  # Check first 10 elements
            
    def test_windaq_channel_data_invalid_numbers(self, windaq_instance):
        """Test data retrieval with invalid channel numbers."""
        # Channel 0 may or may not be invalid (implementation specific)
        # Just test that it doesn't crash
        try:
            data0 = windaq_instance.data(0)
            assert isinstance(data0, list), "Channel 0 data should be a list if returned"
        except (IndexError, ValueError, KeyError):
            pass  # Expected behavior for some implementations
            
        # Channel beyond available channels should be invalid
        with pytest.raises((IndexError, ValueError, KeyError)):
            windaq_instance.data(windaq_instance.nChannels + 1)
            
    def test_windaq_channel_units(self, windaq_instance):
        """Test unit strings for all channels."""
        for channel in range(1, windaq_instance.nChannels + 1):
            units = windaq_instance.unit(channel)
            
            # Units should be a string
            assert isinstance(units, str)
            
    def test_windaq_channel_annotations(self, windaq_instance):
        """Test channel annotations/names."""
        for channel in range(1, windaq_instance.nChannels + 1):
            annotation = windaq_instance.chAnnotation(channel)
            
            # Annotation should be a string
            assert isinstance(annotation, str)
            
    def test_windaq_data_consistency(self, windaq_instance):
        """Test that multiple calls return consistent data."""
        # Get data twice and compare
        data1 = windaq_instance.data(1)
        data2 = windaq_instance.data(1)
        
        assert len(data1) == len(data2)
        assert all(a == b for a, b in zip(data1, data2))
        
    def test_windaq_time_consistency(self, windaq_instance):
        """Test that multiple time() calls return consistent results."""
        time1 = windaq_instance.time()
        time2 = windaq_instance.time()
        
        assert len(time1) == len(time2)
        assert all(a == b for a, b in zip(time1, time2))


class TestWinDAQErrorHandling:
    """Test error handling scenarios."""
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted files."""
        # Create a temporary file with invalid content
        with tempfile.NamedTemporaryFile(suffix='.wdq', delete=False) as tmp:
            tmp.write(b'This is not a valid WDQ file')
            tmp_path = tmp.name
            
        try:
            # Should handle corrupted file gracefully
            with pytest.raises((struct.error, IndexError, ValueError)):
                windaq(tmp_path)
        finally:
            os.unlink(tmp_path)
            
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        with tempfile.NamedTemporaryFile(suffix='.wdq', delete=False) as tmp:
            # File is empty
            tmp_path = tmp.name
            
        try:
            with pytest.raises((struct.error, IndexError, ValueError)):
                windaq(tmp_path)
        finally:
            os.unlink(tmp_path)
            
    def test_very_small_file_handling(self):
        """Test handling of files too small to be valid WDQ files."""
        with tempfile.NamedTemporaryFile(suffix='.wdq', delete=False) as tmp:
            tmp.write(b'tiny')  # Only 4 bytes
            tmp_path = tmp.name
            
        try:
            with pytest.raises((struct.error, IndexError, ValueError)):
                windaq(tmp_path)
        finally:
            os.unlink(tmp_path)


# Helper functions for test data generation (if needed)
def create_test_data_directory():
    """Create test data directory if it doesn't exist."""
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(test_data_dir, exist_ok=True)
    return test_data_dir


# Test discovery and documentation
if __name__ == "__main__":
    print("WinDAQ Tests")
    print("============")
    print()
    print("To run tests with a sample file:")
    print("1. Create directory: wdq_app/tests/data/")
    print("2. Place a sample .wdq file at: wdq_app/tests/data/sample.wdq")
    print("3. Run: pytest wdq_app/tests/test_windaq.py")
    print()
    print("Tests without sample files will focus on error handling and validation.")