"""
Unit tests for database models structure and basic functionality.
Note: These tests focus on model structure rather than actual database operations
since they require PostgreSQL with UUID extension.
"""
import pytest
from datetime import datetime, date
import uuid

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.database_models import ScanResultDB, BacktestResultDB, TradeDB


class TestScanResultDB:
    """Test ScanResultDB database model structure."""
    
    def test_scan_result_model_creation(self):
        """Test creating a ScanResultDB model instance."""
        scan_data = {
            "timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "symbols_scanned": ["AAPL", "GOOGL", "MSFT"],
            "signals_found": [
                {
                    "symbol": "AAPL",
                    "signal_type": "long",
                    "timestamp": "2024-01-01T10:00:00",
                    "price": 154.0,
                    "confidence": 0.85,
                    "indicators": {
                        "ema5": 150.0,
                        "ema8": 149.5,
                        "ema13": 149.0,
                        "ema21": 148.5,
                        "ema50": 147.0,
                        "atr": 2.5,
                        "atr_long_line": 145.0,
                        "atr_short_line": 152.0
                    }
                }
            ],
            "settings_used": {
                "atr_multiplier": 2.0,
                "ema5_rising_threshold": 0.02,
                "higher_timeframe": "15m"
            },
            "execution_time": 2.5
        }
        
        scan_result = ScanResultDB(**scan_data)
        
        # Verify the model was created with correct attributes
        assert scan_result.symbols_scanned == ["AAPL", "GOOGL", "MSFT"]
        assert scan_result.execution_time == 2.5
        assert scan_result.timestamp == datetime(2024, 1, 1, 10, 0, 0)
        assert len(scan_result.signals_found) == 1
        assert scan_result.settings_used["atr_multiplier"] == 2.0
    
    def test_scan_result_table_name(self):
        """Test that the table name is correct."""
        assert ScanResultDB.__tablename__ == "scan_results"
    
    def test_scan_result_repr(self):
        """Test the string representation of ScanResultDB."""
        scan_result = ScanResultDB(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            symbols_scanned=["AAPL"],
            signals_found=[],
            settings_used={},
            execution_time=1.0
        )
        scan_result.id = uuid.uuid4()
        
        repr_str = repr(scan_result)
        assert "ScanResult" in repr_str
        assert str(scan_result.id) in repr_str


class TestBacktestResultDB:
    """Test BacktestResultDB database model structure."""
    
    def test_backtest_result_model_creation(self):
        """Test creating a BacktestResultDB model instance."""
        backtest_data = {
            "timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 31),
            "symbols": ["AAPL", "GOOGL"],
            "trades": [
                {
                    "symbol": "AAPL",
                    "entry_date": "2024-01-01T10:00:00",
                    "entry_price": 150.0,
                    "exit_date": "2024-01-02T10:00:00",
                    "exit_price": 155.0,
                    "trade_type": "long",
                    "pnl": 5.0,
                    "pnl_percent": 3.33
                }
            ],
            "performance": {
                "total_trades": 1,
                "winning_trades": 1,
                "losing_trades": 0,
                "win_rate": 1.0,
                "total_return": 3.33,
                "average_return": 3.33,
                "max_drawdown": 0.0,
                "sharpe_ratio": 2.0
            },
            "settings_used": {
                "atr_multiplier": 2.0,
                "higher_timeframe": "15m"
            }
        }
        
        backtest_result = BacktestResultDB(**backtest_data)
        
        # Verify the model was created with correct attributes
        assert backtest_result.start_date == date(2024, 1, 1)
        assert backtest_result.symbols == ["AAPL", "GOOGL"]
        assert len(backtest_result.trades) == 1
        assert backtest_result.performance["win_rate"] == 1.0
        assert backtest_result.settings_used["atr_multiplier"] == 2.0
    
    def test_backtest_result_table_name(self):
        """Test that the table name is correct."""
        assert BacktestResultDB.__tablename__ == "backtest_results"
    
    def test_backtest_result_relationships(self):
        """Test that relationships are properly defined."""
        # Check that the relationship exists
        assert hasattr(BacktestResultDB, 'trade_records')
        
        # Create instance to test relationship
        backtest_result = BacktestResultDB(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            symbols=["AAPL"],
            trades=[],
            performance={},
            settings_used={}
        )
        
        # Verify trade_records is accessible (even if empty)
        assert hasattr(backtest_result, 'trade_records')


class TestTradeDB:
    """Test TradeDB database model structure."""
    
    def test_trade_model_creation(self):
        """Test creating a TradeDB model instance."""
        backtest_id = uuid.uuid4()
        
        trade_data = {
            "backtest_id": backtest_id,
            "symbol": "AAPL",
            "entry_date": datetime(2024, 1, 1, 10, 0, 0),
            "entry_price": 150.0,
            "exit_date": datetime(2024, 1, 2, 10, 0, 0),
            "exit_price": 155.0,
            "trade_type": "long",
            "pnl": 5.0,
            "pnl_percent": 3.33
        }
        
        trade = TradeDB(**trade_data)
        
        # Verify the model was created with correct attributes
        assert trade.symbol == "AAPL"
        assert trade.trade_type == "long"
        assert trade.pnl == 5.0
        assert trade.backtest_id == backtest_id
        assert trade.entry_price == 150.0
        assert trade.exit_price == 155.0
    
    def test_trade_table_name(self):
        """Test that the table name is correct."""
        assert TradeDB.__tablename__ == "trades"
    
    def test_trade_relationships(self):
        """Test that relationships are properly defined."""
        # Check that the relationship exists
        assert hasattr(TradeDB, 'backtest')
        
        # Create instance to test relationship
        trade = TradeDB(
            backtest_id=uuid.uuid4(),
            symbol="AAPL",
            entry_date=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=150.0,
            trade_type="long",
            pnl=5.0,
            pnl_percent=3.33
        )
        
        # Verify backtest relationship is accessible
        assert hasattr(trade, 'backtest')
    
    def test_trade_repr(self):
        """Test the string representation of TradeDB."""
        trade = TradeDB(
            backtest_id=uuid.uuid4(),
            symbol="AAPL",
            entry_date=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=150.0,
            trade_type="long",
            pnl=5.0,
            pnl_percent=3.33
        )
        trade.id = uuid.uuid4()
        
        repr_str = repr(trade)
        assert "Trade" in repr_str
        assert "AAPL" in repr_str
        assert "long" in repr_str


class TestDatabaseModelsIntegration:
    """Test database models integration and structure."""
    
    def test_model_table_names(self):
        """Test that all models have correct table names."""
        assert ScanResultDB.__tablename__ == "scan_results"
        assert BacktestResultDB.__tablename__ == "backtest_results"
        assert TradeDB.__tablename__ == "trades"
    
    def test_foreign_key_relationships(self):
        """Test that foreign key relationships are properly defined."""
        # Check that TradeDB has the correct foreign key reference
        trade_columns = TradeDB.__table__.columns
        backtest_id_column = trade_columns['backtest_id']
        
        # Verify the column exists and has foreign key
        assert backtest_id_column is not None
        assert len(backtest_id_column.foreign_keys) > 0
        
        # Check the foreign key points to the right table
        fk = list(backtest_id_column.foreign_keys)[0]
        assert fk.column.table.name == "backtest_results"
        assert fk.column.name == "id"
    
    def test_uuid_columns(self):
        """Test that UUID columns are properly defined."""
        # Check ScanResultDB
        scan_id_column = ScanResultDB.__table__.columns['id']
        assert scan_id_column.primary_key
        
        # Check BacktestResultDB
        backtest_id_column = BacktestResultDB.__table__.columns['id']
        assert backtest_id_column.primary_key
        
        # Check TradeDB
        trade_id_column = TradeDB.__table__.columns['id']
        assert trade_id_column.primary_key
    
    def test_jsonb_columns(self):
        """Test that JSONB columns are properly defined."""
        # Check ScanResultDB JSONB columns
        scan_table = ScanResultDB.__table__
        assert 'symbols_scanned' in scan_table.columns
        assert 'signals_found' in scan_table.columns
        assert 'settings_used' in scan_table.columns
        
        # Check BacktestResultDB JSONB columns
        backtest_table = BacktestResultDB.__table__
        assert 'symbols' in backtest_table.columns
        assert 'trades' in backtest_table.columns
        assert 'performance' in backtest_table.columns
        assert 'settings_used' in backtest_table.columns