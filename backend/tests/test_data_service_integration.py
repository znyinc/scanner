"""
Integration tests for data service with other components.
"""
import pytest
import asyncio
from datetime import date, datetime
from unittest.mock import patch, Mock
import pandas as pd

from backend.app.services import DataService
from backend.app.models.market_data import MarketData


class TestDataServiceIntegration:
    """Test data service integration with other components."""
    
    @pytest.fixture
    def data_service(self):
        """Create a data service instance."""
        return DataService(cache_ttl_minutes=1, max_retries=2)
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for testing."""
        dates = pd.date_range(start='2024-01-01 09:30:00', periods=3, freq='1min')
        return pd.DataFrame({
            'Open': [150.0, 150.5, 151.0],
            'High': [150.2, 150.8, 151.3],
            'Low': [149.8, 150.2, 150.7],
            'Close': [150.1, 150.7, 150.9],
            'Volume': [1000, 1200, 800]
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_service_import_and_instantiation(self):
        """Test that the service can be imported and instantiated correctly."""
        service = DataService()
        assert service is not None
        assert hasattr(service, 'fetch_current_data')
        assert hasattr(service, 'fetch_historical_data')
        assert hasattr(service, 'fetch_higher_timeframe_data')
    
    @pytest.mark.asyncio
    async def test_market_data_model_integration(self, data_service, sample_data):
        """Test that the service correctly creates MarketData objects."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_data
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["AAPL"])
            
            assert "AAPL" in result
            market_data_list = result["AAPL"]
            
            # Verify all objects are MarketData instances
            assert all(isinstance(md, MarketData) for md in market_data_list)
            
            # Verify data integrity
            first_data = market_data_list[0]
            assert first_data.symbol == "AAPL"
            assert first_data.open == 150.0
            assert first_data.close == 150.1
            assert isinstance(first_data.timestamp, datetime)
            
            # Test serialization/deserialization
            json_str = first_data.to_json()
            reconstructed = MarketData.from_json(json_str)
            assert reconstructed.symbol == first_data.symbol
            assert reconstructed.open == first_data.open
    
    @pytest.mark.asyncio
    async def test_cache_with_real_objects(self, data_service, sample_data):
        """Test caching functionality with real MarketData objects."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_data
            mock_ticker.return_value = mock_instance
            
            # First call
            result1 = await data_service.fetch_current_data(["AAPL"])
            
            # Second call should use cache
            result2 = await data_service.fetch_current_data(["AAPL"])
            
            # Verify API was called only once
            assert mock_instance.history.call_count == 1
            
            # Verify results are equivalent
            assert len(result1["AAPL"]) == len(result2["AAPL"])
            
            # Compare first data point
            data1 = result1["AAPL"][0]
            data2 = result2["AAPL"][0]
            assert data1.symbol == data2.symbol
            assert data1.open == data2.open
            assert data1.close == data2.close
    
    @pytest.mark.asyncio
    async def test_error_handling_with_logging(self, data_service):
        """Test error handling and logging integration."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.side_effect = Exception("Network error")
            mock_ticker.return_value = mock_instance
            
            # Should handle error gracefully
            result = await data_service.fetch_current_data(["INVALID"])
            
            assert "INVALID" in result
            assert len(result["INVALID"]) == 0
            
            # Should have attempted retries
            assert mock_instance.history.call_count == data_service.max_retries
    
    @pytest.mark.asyncio
    async def test_multiple_timeframes(self, data_service, sample_data):
        """Test fetching different timeframes."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_data
            mock_ticker.return_value = mock_instance
            
            # Test 1-minute data
            result_1m = await data_service.fetch_current_data(["AAPL"], interval="1m")
            
            # Test 15-minute data
            result_15m = await data_service.fetch_higher_timeframe_data(["AAPL"], timeframe="15m")
            
            # Both should return data
            assert len(result_1m["AAPL"]) > 0
            assert len(result_15m["AAPL"]) > 0
            
            # Verify correct intervals were requested
            calls = mock_instance.history.call_args_list
            assert any('1m' in str(call) for call in calls)
            assert any('15m' in str(call) for call in calls)
    
    @pytest.mark.asyncio
    async def test_historical_data_integration(self, data_service, sample_data):
        """Test historical data fetching integration."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_data
            mock_ticker.return_value = mock_instance
            
            start_date = date(2024, 1, 1)
            end_date = date(2024, 1, 2)
            
            result = await data_service.fetch_historical_data(["AAPL"], start_date, end_date)
            
            assert "AAPL" in result
            assert len(result["AAPL"]) > 0
            
            # Verify historical call was made with correct parameters
            mock_instance.history.assert_called_with(start=start_date, end=end_date, interval="1d")
    
    def test_cache_statistics(self, data_service):
        """Test cache statistics functionality."""
        # Initially empty
        stats = data_service.get_cache_stats()
        assert stats["size"] == 0
        
        # Add some data
        data_service.cache.set("test1", {"data": 1})
        data_service.cache.set("test2", {"data": 2})
        
        stats = data_service.get_cache_stats()
        assert stats["size"] == 2
        
        # Clear cache
        data_service.clear_cache()
        stats = data_service.get_cache_stats()
        assert stats["size"] == 0