"""
Unit tests for data models.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models import (
    MarketData, TechnicalIndicators, Signal, AlgorithmSettings,
    ScanResult, BacktestResult, Trade, PerformanceMetrics
)


class TestMarketData:
    """Test MarketData model."""
    
    def test_market_data_creation(self):
        """Test creating MarketData instance."""
        data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000
        )
        
        assert data.symbol == "AAPL"
        assert data.open == 150.0
        assert data.volume == 1000000
    
    def test_market_data_serialization(self):
        """Test MarketData JSON serialization."""
        data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000
        )
        
        # Test to_dict
        data_dict = data.to_dict()
        assert data_dict["symbol"] == "AAPL"
        assert data_dict["timestamp"] == "2024-01-01T10:00:00"
        
        # Test from_dict
        restored_data = MarketData.from_dict(data_dict)
        assert restored_data.symbol == data.symbol
        assert restored_data.timestamp == data.timestamp
        
        # Test JSON serialization
        json_str = data.to_json()
        restored_from_json = MarketData.from_json(json_str)
        assert restored_from_json.symbol == data.symbol


class TestTechnicalIndicators:
    """Test TechnicalIndicators model."""
    
    def test_technical_indicators_creation(self):
        """Test creating TechnicalIndicators instance."""
        indicators = TechnicalIndicators(
            ema5=150.0,
            ema8=149.5,
            ema13=149.0,
            ema21=148.5,
            ema50=147.0,
            atr=2.5,
            atr_long_line=145.0,
            atr_short_line=152.0
        )
        
        assert indicators.ema5 == 150.0
        assert indicators.atr == 2.5
    
    def test_technical_indicators_serialization(self):
        """Test TechnicalIndicators JSON serialization."""
        indicators = TechnicalIndicators(
            ema5=150.0,
            ema8=149.5,
            ema13=149.0,
            ema21=148.5,
            ema50=147.0,
            atr=2.5,
            atr_long_line=145.0,
            atr_short_line=152.0
        )
        
        # Test serialization round trip
        json_str = indicators.to_json()
        restored = TechnicalIndicators.from_json(json_str)
        assert restored.ema5 == indicators.ema5
        assert restored.atr_long_line == indicators.atr_long_line


class TestSignal:
    """Test Signal model."""
    
    def test_signal_creation(self):
        """Test creating Signal instance."""
        indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=147.0,
            atr=2.5, atr_long_line=145.0, atr_short_line=152.0
        )
        
        signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            price=154.0,
            indicators=indicators,
            confidence=0.85
        )
        
        assert signal.symbol == "AAPL"
        assert signal.signal_type == "long"
        assert signal.confidence == 0.85
    
    def test_signal_serialization(self):
        """Test Signal JSON serialization."""
        indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=147.0,
            atr=2.5, atr_long_line=145.0, atr_short_line=152.0
        )
        
        signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            price=154.0,
            indicators=indicators,
            confidence=0.85
        )
        
        # Test serialization round trip
        json_str = signal.to_json()
        restored = Signal.from_json(json_str)
        assert restored.symbol == signal.symbol
        assert restored.indicators.ema5 == signal.indicators.ema5


class TestAlgorithmSettings:
    """Test AlgorithmSettings model."""
    
    def test_algorithm_settings_defaults(self):
        """Test AlgorithmSettings default values."""
        settings = AlgorithmSettings()
        
        assert settings.atr_multiplier == 2.0
        assert settings.ema5_rising_threshold == 0.02
        assert settings.higher_timeframe == "15m"
    
    def test_algorithm_settings_custom(self):
        """Test AlgorithmSettings with custom values."""
        settings = AlgorithmSettings(
            atr_multiplier=3.0,
            volatility_filter=2.0,
            higher_timeframe="30m"
        )
        
        assert settings.atr_multiplier == 3.0
        assert settings.volatility_filter == 2.0
        assert settings.higher_timeframe == "30m"
    
    def test_algorithm_settings_serialization(self):
        """Test AlgorithmSettings JSON serialization."""
        settings = AlgorithmSettings(atr_multiplier=3.0)
        
        json_str = settings.to_json()
        restored = AlgorithmSettings.from_json(json_str)
        assert restored.atr_multiplier == settings.atr_multiplier


class TestTrade:
    """Test Trade model."""
    
    def test_trade_creation(self):
        """Test creating Trade instance."""
        trade = Trade(
            symbol="AAPL",
            entry_date=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=150.0,
            exit_date=datetime(2024, 1, 2, 10, 0, 0),
            exit_price=155.0,
            trade_type="long",
            pnl=5.0,
            pnl_percent=3.33
        )
        
        assert trade.symbol == "AAPL"
        assert trade.trade_type == "long"
        assert trade.pnl == 5.0
    
    def test_trade_serialization(self):
        """Test Trade JSON serialization."""
        trade = Trade(
            symbol="AAPL",
            entry_date=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=150.0,
            exit_date=datetime(2024, 1, 2, 10, 0, 0),
            exit_price=155.0,
            trade_type="long",
            pnl=5.0,
            pnl_percent=3.33
        )
        
        json_str = trade.to_json()
        restored = Trade.from_json(json_str)
        assert restored.symbol == trade.symbol
        assert restored.entry_date == trade.entry_date


class TestPerformanceMetrics:
    """Test PerformanceMetrics model."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            win_rate=0.6,
            total_return=15.5,
            average_return=0.155,
            max_drawdown=-5.2,
            sharpe_ratio=1.25
        )
        
        assert metrics.total_trades == 100
        assert metrics.win_rate == 0.6
        assert metrics.sharpe_ratio == 1.25


class TestScanResult:
    """Test ScanResult model."""
    
    def test_scan_result_creation(self):
        """Test creating ScanResult instance."""
        settings = AlgorithmSettings()
        indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=147.0,
            atr=2.5, atr_long_line=145.0, atr_short_line=152.0
        )
        signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            price=154.0,
            indicators=indicators,
            confidence=0.85
        )
        
        scan_result = ScanResult(
            id="test-scan-1",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            symbols_scanned=["AAPL", "GOOGL", "MSFT"],
            signals_found=[signal],
            settings_used=settings,
            execution_time=2.5
        )
        
        assert scan_result.id == "test-scan-1"
        assert len(scan_result.symbols_scanned) == 3
        assert len(scan_result.signals_found) == 1
        assert scan_result.execution_time == 2.5


class TestBacktestResult:
    """Test BacktestResult model."""
    
    def test_backtest_result_creation(self):
        """Test creating BacktestResult instance."""
        settings = AlgorithmSettings()
        trade = Trade(
            symbol="AAPL",
            entry_date=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=150.0,
            exit_date=datetime(2024, 1, 2, 10, 0, 0),
            exit_price=155.0,
            trade_type="long",
            pnl=5.0,
            pnl_percent=3.33
        )
        metrics = PerformanceMetrics(
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            win_rate=1.0,
            total_return=3.33,
            average_return=3.33,
            max_drawdown=0.0,
            sharpe_ratio=2.0
        )
        
        backtest_result = BacktestResult(
            id="test-backtest-1",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            symbols=["AAPL"],
            trades=[trade],
            performance=metrics,
            settings_used=settings
        )
        
        assert backtest_result.id == "test-backtest-1"
        assert len(backtest_result.trades) == 1
        assert backtest_result.performance.win_rate == 1.0