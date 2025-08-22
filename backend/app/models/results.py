"""
Result models for scan and backtest operations.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import List, Dict, Any
import json
from .signals import Signal, AlgorithmSettings


@dataclass
class ScanResult:
    """Result of a stock scanning operation."""
    id: str
    timestamp: datetime
    symbols_scanned: List[str]
    signals_found: List[Signal]
    settings_used: AlgorithmSettings
    execution_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['signals_found'] = [signal.to_dict() for signal in self.signals_found]
        data['settings_used'] = self.settings_used.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResult':
        """Create instance from dictionary."""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data['signals_found'], list):
            data['signals_found'] = [Signal.from_dict(signal) for signal in data['signals_found']]
        if isinstance(data['settings_used'], dict):
            data['settings_used'] = AlgorithmSettings.from_dict(data['settings_used'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'ScanResult':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Trade:
    """Represents a single trade from backtesting."""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    trade_type: str  # 'long' or 'short'
    pnl: float
    pnl_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['entry_date'] = self.entry_date.isoformat()
        data['exit_date'] = self.exit_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create instance from dictionary."""
        data = data.copy()
        if isinstance(data['entry_date'], str):
            data['entry_date'] = datetime.fromisoformat(data['entry_date'])
        if isinstance(data['exit_date'], str):
            data['exit_date'] = datetime.fromisoformat(data['exit_date'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Trade':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PerformanceMetrics:
    """Performance metrics calculated from backtest results."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    average_return: float
    max_drawdown: float
    sharpe_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create instance from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'PerformanceMetrics':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class BacktestResult:
    """Result of a backtesting operation."""
    id: str
    timestamp: datetime
    start_date: date
    end_date: date
    symbols: List[str]
    trades: List[Trade]
    performance: PerformanceMetrics
    settings_used: AlgorithmSettings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        data['trades'] = [trade.to_dict() for trade in self.trades]
        data['performance'] = self.performance.to_dict()
        data['settings_used'] = self.settings_used.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create instance from dictionary."""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])
        if isinstance(data['trades'], list):
            data['trades'] = [Trade.from_dict(trade) for trade in data['trades']]
        if isinstance(data['performance'], dict):
            data['performance'] = PerformanceMetrics.from_dict(data['performance'])
        if isinstance(data['settings_used'], dict):
            data['settings_used'] = AlgorithmSettings.from_dict(data['settings_used'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'BacktestResult':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))