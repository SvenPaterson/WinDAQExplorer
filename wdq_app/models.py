"""Data models for WDQ Analyzer."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ChannelConfig:
    """Configuration for a single channel."""
    
    channel_num: int
    name: str = ""
    units: str = "N/A"
    axis: str = "Primary"
    subplot: int = 1  # Field for subplot assignment
    color: str = "auto"  # New field for color assignment
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.name:
            self.name = f"Channel {self.channel_num}"
    
    @property
    def label(self) -> str:
        """Generate label for plotting."""
        return f"{self.name} ({self.units})" if self.units and self.units != "N/A" else self.name
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'channel_num': self.channel_num,
            'name': self.name,
            'units': self.units,
            'axis': self.axis,
            'subplot': self.subplot,
            'color': self.color
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelConfig':
        """Create from dictionary."""
        return cls(**data)