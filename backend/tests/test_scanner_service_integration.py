"""
Integration tests for the scanner service.
Tests the complete scanning workflow including data fetching and algorithm evaluation.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from app.services.scanner_service import ScannerService, ScanFilters
from app.services.data_service import DataService
from app.services.algorithm_engine import AlgorithmEngine
from app.models.market_data import MarketData
from app.models.signals import Signal, AlgorithmSettings
from app.models.results import ScanResult


@pytest.fixture
def mock_data_service():
    """Mock data service for testing."""
    service = Mock(spec=DataService)
    service.fetch_current_data = AsyncMock()
    service.fetch_higher_timeframe_data = AsyncMock()
    return service


@pytest.fixture
def mock_algorithm_engine():
    """Mock algorithm engine for testing."""
    engine = Mock(spec=AlgorithmEngine)
    engine.generate_signals = Mock()
    return engine


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    base_time = datetime.now()
    return [
        MarketData(
            symbol="AAPL",
            timestamp=base_time - timedelta(minutes=i),
            open=150.0 + i * 0.1,
            high=151.0 + i * 0.1,
            low=149.0 + i * 0.1,
            close=150.5 + i * 0.1,
            volume=1000000 + i * 1000
        ) for i in range(50)
    ]


@pytest.fixture
def sample_signals():
    """Sample signals for testing."""
    from app.models.market_data import TechnicalIndicators
    
    return [
        Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime.now(),
            price=150.5,
            confidence=0.85,
            indicators=TechnicalIndicators(
                ema5=150.2,
                ema8=150.0,
                ema13=149.8,
                ema21=149.5,
                ema50=149.0,
                atr=2.5,
                atr_long_line=147.5,
                atr_short_line=152.5
            )
        ),
        Signal(
            symbol="MSFT",
            signal_type="short",
            timestamp=datetime.now(),
            price=300.0,
            confidence=0.75,
            indicators=TechnicalIndicators(
                ema5=300.5,
                ema8=301.0,
                ema13=301.2,
                ema21=301.5,
                ema50=302.0,
                atr=5.0,
                atr_long_line=295.0,
                atr_short_line=305.0
            )
        )
    ]


@pytest.mark.asyncio
class TestScannerServiceIntegration:
    """Integration tests for scanner service."""
    
    async def test_scan_stocks_success(self, mock_data_service, mock_algorithm_engine, 
                                     sample_market_data, sample_signals):
        """Test successful stock scanning workflow."""
        # Setup mocks
        symbols = ["AAPL", "MSFT"]
        mock_data_service.fetch_current_data.return_value = {
            "AAPL": sample_market_data,
            "MSFT": sample_market_data
        }
        mock_data_service.fetch_higher_timeframe_data.return_value = {
            "AAPL": sample_market_data[:10],
            "MSFT": sample_market_data[:10]
        }
        
        # Mock algorithm engine to return signals for first symbol only
        def mock_generate_signals(market_data, historical_data, htf_market_data, htf_historical_data, settings):
            if market_data and market_data.symbol == "AAPL":
                return [sample_signals[0]]
            return []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals
        
        # Create scanner service
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine,
            max_workers=2
        )
        
        # Mock database operations
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock) as mock_save:
            # Execute scan
            result = await scanner.scan_stocks(symbols)
            
            # Verify result
            assert isinstance(result, ScanResult)
            assert result.symbols_scanned == symbols
            assert len(result.signals_found) >= 1
            # Check that we have at least one AAPL signal
            aapl_signals = [s for s in result.signals_found if s.symbol == "AAPL"]
            assert len(aapl_signals) >= 1
            assert aapl_signals[0].signal_type == "long"
            assert result.execution_time > 0
            
            # Verify data service calls
            mock_data_service.fetch_current_data.assert_called_once_with(
                symbols, period="5d", interval="1m"
            )
            mock_data_service.fetch_higher_timeframe_data.assert_called_once()
            
            # Verify algorithm engine calls (should be called for each symbol)
            assert mock_algorithm_engine.generate_signals.call_count == 2
            
            # Verify database save
            mock_save.assert_called_once()
    
    async def test_scan_stocks_empty_symbols(self, mock_data_service, mock_algorithm_engine):
        """Test scanning with empty symbol list."""
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with pytest.raises(ValueError, match="No symbols provided"):
            await scanner.scan_stocks([])
    
    async def test_scan_stocks_invalid_symbols(self, mock_data_service, mock_algorithm_engine):
        """Test scanning with invalid symbols."""
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with pytest.raises(ValueError, match="No valid symbols provided"):
            await scanner.scan_stocks(["", "  ", None])
    
    async def test_scan_stocks_data_fetch_failure(self, mock_data_service, mock_algorithm_engine):
        """Test handling of data fetch failures."""
        symbols = ["AAPL"]
        mock_data_service.fetch_current_data.side_effect = Exception("API Error")
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            with pytest.raises(Exception, match="API Error"):
                await scanner.scan_stocks(symbols)
    
    async def test_scan_stocks_insufficient_data(self, mock_data_service, mock_algorithm_engine):
        """Test handling of insufficient market data."""
        symbols = ["AAPL"]
        # Return insufficient data (less than 50 points)
        insufficient_data = [
            MarketData(
                symbol="AAPL",
                timestamp=datetime.now(),
                open=150.0,
                high=151.0,
                low=149.0,
                close=150.5,
                volume=1000000
            )
        ]
        
        mock_data_service.fetch_current_data.return_value = {"AAPL": insufficient_data}
        mock_data_service.fetch_higher_timeframe_data.return_value = {"AAPL": insufficient_data}
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            result = await scanner.scan_stocks(symbols)
            
            # Should complete but find no signals due to insufficient data
            assert len(result.signals_found) == 0
            assert result.symbols_scanned == symbols
    
    async def test_scan_stocks_algorithm_error(self, mock_data_service, mock_algorithm_engine, 
                                             sample_market_data):
        """Test handling of algorithm engine errors."""
        symbols = ["AAPL"]
        mock_data_service.fetch_current_data.return_value = {"AAPL": sample_market_data}
        mock_data_service.fetch_higher_timeframe_data.return_value = {"AAPL": sample_market_data[:10]}
        
        # Mock algorithm engine to raise error
        mock_algorithm_engine.generate_signals.side_effect = Exception("Algorithm Error")
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            result = await scanner.scan_stocks(symbols)
            
            # Should complete but find no signals due to algorithm error
            assert len(result.signals_found) == 0
            assert result.symbols_scanned == symbols
    
    async def test_scan_stocks_custom_settings(self, mock_data_service, mock_algorithm_engine, 
                                             sample_market_data, sample_signals):
        """Test scanning with custom algorithm settings."""
        symbols = ["AAPL"]
        custom_settings = AlgorithmSettings(
            atr_multiplier=2.5,
            higher_timeframe="15m"
        )
        
        mock_data_service.fetch_current_data.return_value = {"AAPL": sample_market_data}
        mock_data_service.fetch_higher_timeframe_data.return_value = {"AAPL": sample_market_data[:10]}
        mock_algorithm_engine.generate_signals.return_value = [sample_signals[0]]
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            result = await scanner.scan_stocks(symbols, settings=custom_settings)
            
            # Verify custom settings were used
            assert result.settings_used == custom_settings
            
            # Verify higher timeframe data fetch was called
            mock_data_service.fetch_higher_timeframe_data.assert_called_once()
    
    async def test_scan_history_retrieval(self, mock_data_service, mock_algorithm_engine):
        """Test scan history retrieval with filters."""
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        # Mock database query
        with patch('app.services.scanner_service.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock query result
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Test with filters
            filters = ScanFilters(
                start_date=datetime.now() - timedelta(days=7),
                symbols=["AAPL"],
                limit=10
            )
            
            results = await scanner.get_scan_history(filters)
            
            # Verify database interaction
            assert isinstance(results, list)
            mock_db.query.assert_called_once()
            mock_query.filter.assert_called()
            mock_query.limit.assert_called_with(10)
    
    async def test_scan_statistics(self, mock_data_service, mock_algorithm_engine):
        """Test scan statistics retrieval."""
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        # Mock database query
        with patch('app.services.scanner_service.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock query result with sample data
            mock_scan = Mock()
            mock_scan.symbols_scanned = ["AAPL", "MSFT"]
            mock_scan.signals_found = [
                {"signal_type": "long", "symbol": "AAPL"},
                {"signal_type": "short", "symbol": "MSFT"}
            ]
            mock_scan.execution_time = 1.5
            
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_scan]
            
            stats = await scanner.get_scan_statistics(days=30)
            
            # Verify statistics structure
            assert "total_scans" in stats
            assert "total_symbols_scanned" in stats
            assert "total_signals_found" in stats
            assert "average_execution_time" in stats
            assert "signals_by_type" in stats
            assert "most_active_symbols" in stats
            
            # Verify calculated values
            assert stats["total_scans"] == 1
            assert stats["total_symbols_scanned"] == 2
            assert stats["total_signals_found"] == 2
            assert stats["average_execution_time"] == 1.5


@pytest.mark.asyncio
class TestScannerServicePerformance:
    """Performance tests for scanner service."""
    
    async def test_batch_processing_performance(self, mock_data_service, mock_algorithm_engine, 
                                              sample_market_data):
        """Test performance with large symbol batches."""
        # Create large symbol list
        symbols = [f"STOCK{i:03d}" for i in range(100)]
        
        # Mock data service to return data for all symbols
        mock_data_service.fetch_current_data.return_value = {
            symbol: sample_market_data for symbol in symbols
        }
        mock_data_service.fetch_higher_timeframe_data.return_value = {
            symbol: sample_market_data[:10] for symbol in symbols
        }
        
        # Mock algorithm engine to return no signals (for speed)
        mock_algorithm_engine.generate_signals.return_value = []
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine,
            max_workers=10  # Use more workers for performance
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            start_time = datetime.now()
            result = await scanner.scan_stocks(symbols)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Verify all symbols were processed
            assert len(result.symbols_scanned) == 100
            assert result.execution_time > 0
            
            # Performance should be reasonable (less than 30 seconds for 100 symbols)
            assert execution_time < 30.0
            
            # Verify algorithm was called for each symbol
            assert mock_algorithm_engine.generate_signals.call_count == 100
    
    async def test_concurrent_scan_handling(self, mock_data_service, mock_algorithm_engine, 
                                          sample_market_data):
        """Test handling of concurrent scan requests."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        mock_data_service.fetch_current_data.return_value = {
            symbol: sample_market_data for symbol in symbols
        }
        mock_data_service.fetch_higher_timeframe_data.return_value = {
            symbol: sample_market_data[:10] for symbol in symbols
        }
        mock_algorithm_engine.generate_signals.return_value = []
        
        scanner = ScannerService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine
        )
        
        with patch.object(scanner, '_save_scan_result', new_callable=AsyncMock):
            # Run multiple scans concurrently
            tasks = [
                scanner.scan_stocks(symbols),
                scanner.scan_stocks(symbols),
                scanner.scan_stocks(symbols)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all scans completed successfully
            assert len(results) == 3
            for result in results:
                assert isinstance(result, ScanResult)
                assert len(result.symbols_scanned) == 3
                assert result.execution_time >= 0