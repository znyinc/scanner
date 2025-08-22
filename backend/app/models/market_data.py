"""
Market data models for the stock scanner application.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class MarketData:
    """Represents market data for a single stock at a specific time."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create instance from dictionary."""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'MarketData':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class TechnicalIndicators:
    """Technical indicators calculated from market data."""
    ema5: float
    ema8: float
    ema13: float
    ema21: float
    ema50: float
    atr: float
    atr_long_line: float
    atr_short_line: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnicalIndicators':
        """Create instance from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'TechnicalIndicators':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))