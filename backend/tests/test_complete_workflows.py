"""
Integration tests for complete scan and backtest workflows.
Tests end-to-end functionality from API request to database persistence.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd

from app.services.scanner_service import ScannerService
from app.services.backtest_service import BacktestService
from app.models.market_data import AlgorithmSettings
from app.database import get_database


class TestCompleteWorkflows:
    """Test complete workflows from start to finish."""
    
    @pytest.fixture
    def scanner_service(self):
        """Create scanner service instance."""
        return ScannerService()
    
    @pytest.fixture
    def backtest_service(self):
        """Create backtest service instance."""
        return BacktestService()
    
    @pytest.fixture
    def sample_settings(self):
        """Sample algorithm settings for testing."""
        return AlgorithmSettings(
            atr_multiplier=2.0,
            ema5_rising_threshold=0.02,
            ema8_rising_threshold=0.01,
            ema21_rising_threshold=0.005,
            volatility_filter=1.5,
            fomo_filter=1.0,
            higher_timeframe="15m"
        )
    
    @pytest.fixture
    def mock_market_data(self):
        """Mock market data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
        return pd.DataFrame({
            'Open': [100 + i * 0.1 for i in range(100)],
            'High': [101 + i * 0.1 for i in range(100)],
            'Low': [99 + i * 0.1 for i in range(100)],
            'Close': [100.5 + i * 0.1 for i in range(100)],
            'Volume': [1000 + i * 10 for i in range(100)]
        }, index=dates)
    
    @patch('app.services.data_service.DataService.fetch_current_data')
    @patch('app.services.data_service.DataService.get_higher_timeframe_data')
    async def test_complete_scan_workflow(self, mock_htf_data, mock_current_data, 
                                        scanner_service, sample_settings, mock_market_data):
        """Test complete scan workflow from request to database storage."""
        # Setup mock data
        mock_current_data.return_value = {
            'AAPL': mock_market_data,
            'GOOGL': mock_market_data
        }
        mock_htf_data.return_value = mock_market_data
        
        # Execute scan
        symbols = ['AAPL', 'GOOGL']
        result = await scanner_service.scan_stocks(symbols, sample_settings)
        
        # Verify result structure
        assert result is not None
        assert result.symbols_scanned == symbols
        assert isinstance(result.signals_found, list)
        assert result.settings_used == sample_settings
        assert result.execution_time > 0
        
        # Verify database persistence
        db = get_database()
        saved_result = await db.get_scan_result(result.id)
        assert saved_result is not None
        assert saved_result.id == result.id
        
        # Verify all required fields are present
        assert saved_result.timestamp is not None
        assert len(saved_result.symbols_scanned) == 2
        assert isinstance(saved_result.signals_found, list)
    
    @patch('app.services.data_service.DataService.fetch_historical_data')
    async def test_complete_backtest_workflow(self, mock_historical_data, 
                                            backtest_service, sample_settings, mock_market_data):
        """Test complete backtest workflow from request to performance calculation."""
        # Setup mock historical data
        mock_historical_data.return_value = {
            'AAPL': mock_market_data,
            'GOOGL': mock_market_data
        }
        
        # Execute backtest
        symbols = ['AAPL', 'GOOGL']
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await backtest_service.run_backtest(symbols, start_date, end_date, sample_settings)
        
        # Verify result structure
        assert result is not None
        assert result.symbols == symbols
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert isinstance(result.trades, list)
        assert result.performance is not None
        assert result.settings_used == sample_settings
        
        # Verify performance metrics
        performance = result.performance
        assert hasattr(performance, 'total_trades')
        assert hasattr(performance, 'win_rate')
        assert hasattr(performance, 'total_return')
        assert hasattr(performance, 'average_return')
        assert hasattr(performance, 'max_drawdown')
        
        # Verify database persistence
        db = get_database()
        saved_result = await db.get_backtest_result(result.id)
        assert saved_result is not None
        assert saved_result.id == result.id
    
    @patch('app.services.data_service.DataService.fetch_current_data')
    async def test_scan_workflow_with_no_signals(self, mock_current_data, 
                                               scanner_service, sample_settings):
        """Test scan workflow when no signals are generated."""
        # Setup mock data that won't generate signals
        flat_data = pd.DataFrame({
            'Open': [100] * 50,
            'High': [100.1] * 50,
            'Low': [99.9] * 50,
            'Close': [100] * 50,
            'Volume': [1000] * 50
        }, index=pd.date_range(start='2024-01-01', periods=50, freq='1min'))
        
        mock_current_data.return_value = {'AAPL': flat_data}
        
        result = await scanner_service.scan_stocks(['AAPL'], sample_settings)
        
        assert result is not None
        assert len(result.signals_found) == 0
        assert result.symbols_scanned == ['AAPL']
    
    @patch('app.services.data_service.DataService.fetch_historical_data')
    async def test_backtest_workflow_with_insufficient_data(self, mock_historical_data, 
                                                          backtest_service, sample_settings):
        """Test backtest workflow with insufficient historical data."""
        # Setup mock data with insufficient periods
        short_data = pd.DataFrame({
            'Open': [100] * 10,
            'High': [100.1] * 10,
            'Low': [99.9] * 10,
            'Close': [100] * 10,
            'Volume': [1000] * 10
        }, index=pd.date_range(start='2024-01-01', periods=10, freq='1min'))
        
        mock_historical_data.return_value = {'AAPL': short_data}
        
        with pytest.raises(ValueError, match="Insufficient data"):
            await backtest_service.run_backtest(
                ['AAPL'], 
                date(2024, 1, 1), 
                date(2024, 1, 31), 
                sample_settings
            )
    
    async def test_concurrent_scan_workflows(self, scanner_service, sample_settings, mock_market_data):
        """Test multiple concurrent scan workflows."""
        with patch('app.services.data_service.DataService.fetch_current_data') as mock_data:
            mock_data.return_value = {'AAPL': mock_market_data}
            
            # Run multiple scans concurrently
            tasks = [
                scanner_service.scan_stocks(['AAPL'], sample_settings)
                for _ in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all scans completed successfully
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert result.symbols_scanned == ['AAPL']
    
    async def test_scan_history_retrieval_workflow(self, scanner_service, sample_settings, mock_market_data):
        """Test complete workflow including history retrieval."""
        with patch('app.services.data_service.DataService.fetch_current_data') as mock_data:
            mock_data.return_value = {'AAPL': mock_market_data}
            
            # Perform multiple scans
            results = []
            for i in range(3):
                result = await scanner_service.scan_stocks(['AAPL'], sample_settings)
                results.append(result)
                await asyncio.sleep(0.1)  # Small delay to ensure different timestamps
            
            # Retrieve scan history
            history = await scanner_service.get_scan_history()
            
            # Verify history contains all scans
            assert len(history) >= 3
            
            # Verify history is ordered by timestamp (most recent first)
            timestamps = [scan.timestamp for scan in history[:3]]
            assert timestamps == sorted(timestamps, reverse=True)