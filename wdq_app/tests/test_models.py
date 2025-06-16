"""
Unit tests for data models.

Tests the ChannelConfig dataclass and its methods.
"""

import pytest
import numpy as np
from models import ChannelConfig


class TestChannelConfig:
    """Test cases for ChannelConfig dataclass."""
    
    def test_channel_config_creation_basic(self):
        """Test basic channel configuration creation."""
        config = ChannelConfig(channel_num=1, name="Temperature", units="°C", axis="Primary")
        
        assert config.channel_num == 1
        assert config.name == "Temperature"
        assert config.units == "°C"
        assert config.axis == "Primary"
        
    def test_channel_config_defaults(self):
        """Test default values are applied correctly."""
        config = ChannelConfig(channel_num=5)
        
        assert config.channel_num == 5
        assert config.name == "Channel 5"  # Should auto-generate name
        assert config.units == "N/A"  # Default units
        assert config.axis == "Primary"  # Default axis
        
    def test_channel_config_name_override(self):
        """Test that provided name overrides default."""
        config = ChannelConfig(channel_num=2, name="Pressure")
        
        assert config.channel_num == 2
        assert config.name == "Pressure"  # Should use provided name
        assert config.units == "N/A"
        assert config.axis == "Primary"
        
    def test_channel_config_empty_name_uses_default(self):
        """Test that empty name triggers default generation."""
        config = ChannelConfig(channel_num=3, name="")
        
        assert config.name == "Channel 3"  # Should auto-generate
        
    def test_label_property_with_units(self):
        """Test label generation with valid units."""
        config = ChannelConfig(channel_num=1, name="Temperature", units="°C")
        
        expected_label = "Temperature (°C)"
        assert config.label == expected_label
        
    def test_label_property_without_units(self):
        """Test label generation without units."""
        config = ChannelConfig(channel_num=1, name="Temperature", units="N/A")
        
        expected_label = "Temperature"  # Should not include (N/A)
        assert config.label == expected_label
        
    def test_label_property_empty_units(self):
        """Test label generation with empty units."""
        config = ChannelConfig(channel_num=1, name="Temperature", units="")
        
        # Empty units should be treated as no units
        expected_label = "Temperature"
        assert config.label == expected_label
        
    def test_to_dict_method(self):
        """Test conversion to dictionary."""
        config = ChannelConfig(
            channel_num=2, 
            name="Pressure", 
            units="psi", 
            axis="Secondary"
        )
        
        result = config.to_dict()
        expected = {
            'channel_num': 2,
            'name': 'Pressure',
            'units': 'psi',
            'axis': 'Secondary'
        }
        
        assert result == expected
        assert isinstance(result, dict)
        
    def test_from_dict_method(self):
        """Test creation from dictionary."""
        data = {
            'channel_num': 3,
            'name': 'Vibration',
            'units': 'g',
            'axis': 'Primary'
        }
        
        config = ChannelConfig.from_dict(data)
        
        assert config.channel_num == 3
        assert config.name == 'Vibration'
        assert config.units == 'g'
        assert config.axis == 'Primary'
        
    def test_from_dict_with_defaults(self):
        """Test creation from dictionary with missing optional fields."""
        data = {'channel_num': 4}
        
        config = ChannelConfig.from_dict(data)
        
        assert config.channel_num == 4
        assert config.name == "Channel 4"  # Default applied
        assert config.units == "N/A"  # Default applied
        assert config.axis == "Primary"  # Default applied
        
    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict roundtrip works correctly."""
        original = ChannelConfig(
            channel_num=5,
            name="Torque",
            units="Nm",
            axis="Secondary"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = ChannelConfig.from_dict(data)
        
        # Should be identical
        assert restored.channel_num == original.channel_num
        assert restored.name == original.name
        assert restored.units == original.units
        assert restored.axis == original.axis
        assert restored.label == original.label
        
    def test_channel_config_equality(self):
        """Test that identical configs are considered equal."""
        config1 = ChannelConfig(channel_num=1, name="Test", units="V", axis="Primary")
        config2 = ChannelConfig(channel_num=1, name="Test", units="V", axis="Primary")
        
        # Dataclass should implement equality
        assert config1 == config2
        
    def test_channel_config_inequality(self):
        """Test that different configs are not equal."""
        config1 = ChannelConfig(channel_num=1, name="Test", units="V", axis="Primary")
        config2 = ChannelConfig(channel_num=2, name="Test", units="V", axis="Primary")
        
        assert config1 != config2
        
    def test_special_characters_in_name(self):
        """Test handling of special characters in channel names."""
        config = ChannelConfig(
            channel_num=1, 
            name="Temperature (Ambient)", 
            units="°C"
        )
        
        assert config.name == "Temperature (Ambient)"
        assert config.label == "Temperature (Ambient) (°C)"
        
    def test_unicode_units(self):
        """Test handling of Unicode characters in units."""
        config = ChannelConfig(channel_num=1, name="Angle", units="°")
        
        assert config.units == "°"
        assert config.label == "Angle (°)"
        
    def test_axis_values(self):
        """Test valid axis values."""
        # Test all expected axis values
        for axis in ["Primary", "Secondary", "Omit"]:
            config = ChannelConfig(channel_num=1, axis=axis)
            assert config.axis == axis
            
    def test_channel_number_types(self):
        """Test that channel number must be an integer."""
        # This should work
        config = ChannelConfig(channel_num=1)
        assert config.channel_num == 1
        
        # Test with different integer types
        config = ChannelConfig(channel_num=np.int32(5))
        assert config.channel_num == 5
        
    def test_large_channel_numbers(self):
        """Test handling of large channel numbers."""
        config = ChannelConfig(channel_num=1000)
        
        assert config.channel_num == 1000
        assert config.name == "Channel 1000"
        
    def test_config_immutability_aspects(self):
        """Test aspects of config that should/shouldn't be mutable."""
        config = ChannelConfig(channel_num=1, name="Test")
        
        # These should be mutable (normal dataclass behavior)
        config.name = "Modified"
        assert config.name == "Modified"
        
        config.units = "V"
        assert config.units == "V"
        
        # Label should update dynamically
        assert "Modified" in config.label
        assert "(V)" in config.label