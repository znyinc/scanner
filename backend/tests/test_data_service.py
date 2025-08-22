"""
Integration tests for the data service with mocked yfinance responses.
"""
import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
import asyncio
from typing import Dict, List

from backend.app.services.data_service import DataService, DataCache
from backend.app.models.market_data import MarketData


class TestDataCache:
    """Test the data caching functionality."""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = DataCache(default_ttl_minutes=5)
        
        test_data = {"symbol": "AAPL", "price": 150.0}
        cache.set("test_key", test_data)
        
        retrieved_data = cache.get("test_key")
        assert retrieved_data == test_data
    
    def test_cache_expiration(self):
        """Test that cached data expires correctly."""
        from backend.app.services.data_service import CacheEntry
        
        cache = DataCache(default_ttl_minutes=5)
        
        test_data = {"symbol": "AAPL", "price": 150.0}
        
        # Set data with negative TTL to force immediate expiration
        cache._cache["test_key"] = CacheEntry(
            data=test_data,
            timestamp=datetime.now(),
            expires_at=datetime.now() - timedelta(minutes=1)  # Already expired
        )
        
        # Data should be expired
        retrieved_data = cache.get("test_key")
        assert retrieved_data is None
    
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        cache = DataCache()
        
        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None


class TestDataService:
    """Test the data service functionality."""
    
    @pytest.fixture
    def data_service(self):
        """Create a data service instance for testing."""
        return DataService(cache_ttl_minutes=5, max_retries=2)
    
    @pytest.fixture
    def sample_yfinance_data(self):
        """Create sample yfinance data for testing."""
        dates = pd.date_range(start='2024-01-01 09:30:00', periods=5, freq='1min')
        data = {
            'Open': [150.0, 150.5, 151.0, 150.8, 151.2],
            'High': [150.2, 150.8, 151.3, 151.1, 151.5],  # Fixed: 151.0 -> 151.1 to be >= max(open,close)
            'Low': [149.8, 150.2, 150.7, 150.5, 150.9],
            'Close': [150.1, 150.7, 150.9, 151.1, 151.3],
            'Volume': [1000, 1200, 800, 1500, 900]
        }
        return pd.DataFrame(data, index=dates)
    
    def test_validate_symbol(self, data_service):
        """Test symbol validation."""
        assert data_service._validate_symbol("AAPL") == True
        assert data_service._validate_symbol("MSFT") == True
        assert data_service._validate_symbol("BRK.B") == True
        assert data_service._validate_symbol("BRK-B") == True
        
        # Invalid symbols
        assert data_service._validate_symbol("") == False
        assert data_service._validate_symbol(None) == False
        assert data_service._validate_symbol("TOOLONGSYMBOL") == False
        assert data_service._validate_symbol("INVALID@") == False
    
    def test_clean_market_data(self, data_service, sample_yfinance_data):
        """Test market data cleaning and validation."""
        cleaned_data = data_service._clean_market_data(sample_yfinance_data, "AAPL")
        
        assert len(cleaned_data) == 5
        assert all(isinstance(d, MarketData) for d in cleaned_data)
        assert all(d.symbol == "AAPL" for d in cleaned_data)
        assert all(d.open > 0 and d.close > 0 for d in cleaned_data)
        assert all(d.high >= max(d.open, d.close) for d in cleaned_data)
        assert all(d.low <= min(d.open, d.close) for d in cleaned_data)
    
    def test_clean_market_data_with_invalid_data(self, data_service):
        """Test cleaning data with invalid values."""
        # Create data with NaN and invalid values
        dates = pd.date_range(start='2024-01-01 09:30:00', periods=3, freq='1min')
        invalid_data = pd.DataFrame({
            'Open': [150.0, float('nan'), -10.0],  # NaN and negative
            'High': [150.2, 150.8, 10.0],
            'Low': [149.8, 150.2, 5.0],
            'Close': [150.1, 150.7, 8.0],
            'Volume': [1000, 1200, 800]
        }, index=dates)
        
        cleaned_data = data_service._clean_market_data(invalid_data, "TEST")
        
        # Should only have 1 valid data point
        assert len(cleaned_data) == 1
        assert cleaned_data[0].open == 150.0
    
    @pytest.mark.asyncio
    async def test_fetch_current_data_success(self, data_service, sample_yfinance_data):
        """Test successful current data fetching."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance response
            mock_instance = Mock()
            mock_instance.history.return_value = sample_yfinance_data
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["AAPL"])
            
            assert "AAPL" in result
            assert len(result["AAPL"]) == 5
            assert all(isinstance(d, MarketData) for d in result["AAPL"])
            assert all(d.symbol == "AAPL" for d in result["AAPL"])
    
    @pytest.mark.asyncio
    async def test_fetch_current_data_empty_response(self, data_service):
        """Test handling of empty yfinance response."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock empty response
            mock_instance = Mock()
            mock_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["INVALID"])
            
            assert "INVALID" in result
            assert len(result["INVALID"]) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_current_data_with_retries(self, data_service, sample_yfinance_data):
        """Test retry mechanism on API failures."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            # First call fails, second succeeds
            mock_instance.history.side_effect = [
                Exception("API Error"),
                sample_yfinance_data
            ]
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["AAPL"])
            
            assert "AAPL" in result
            assert len(result["AAPL"]) == 5
            # Should have been called twice due to retry
            assert mock_instance.history.call_count == 2
    
    @pytest.mark.asyncio
    async def test_fetch_current_data_max_retries_exceeded(self, data_service):
        """Test behavior when max retries are exceeded."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            # All calls fail
            mock_instance.history.side_effect = Exception("Persistent API Error")
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["AAPL"])
            
            assert "AAPL" in result
            assert len(result["AAPL"]) == 0
            # Should have been called max_retries times
            assert mock_instance.history.call_count == data_service.max_retries
    
    @pytest.mark.asyncio
    async def test_fetch_higher_timeframe_data(self, data_service, sample_yfinance_data):
        """Test higher timeframe data fetching."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_yfinance_data
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_higher_timeframe_data(["AAPL"], timeframe="15m")
            
            assert "AAPL" in result
            assert len(result["AAPL"]) == 5
            # Verify it was called with correct interval
            mock_instance.history.assert_called_with(period="1d", interval="15m")
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data(self, data_service, sample_yfinance_data):
        """Test historical data fetching."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_yfinance_data
            mock_ticker.return_value = mock_instance
            
            start_date = date(2024, 1, 1)
            end_date = date(2024, 1, 2)
            
            result = await data_service.fetch_historical_data(["AAPL"], start_date, end_date)
            
            assert "AAPL" in result
            assert len(result["AAPL"]) == 5
            # Verify it was called with correct dates
            mock_instance.history.assert_called_with(start=start_date, end=end_date, interval="1d")
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, data_service, sample_yfinance_data):
        """Test that data is properly cached and retrieved."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_yfinance_data
            mock_ticker.return_value = mock_instance
            
            # First call should fetch from API
            result1 = await data_service.fetch_current_data(["AAPL"])
            assert mock_instance.history.call_count == 1
            
            # Second call should use cache
            result2 = await data_service.fetch_current_data(["AAPL"])
            assert mock_instance.history.call_count == 1  # No additional API call
            
            # Results should be identical
            assert len(result1["AAPL"]) == len(result2["AAPL"])
            assert result1["AAPL"][0].symbol == result2["AAPL"][0].symbol
    
    @pytest.mark.asyncio
    async def test_invalid_symbols_handling(self, data_service):
        """Test handling of invalid symbols."""
        result = await data_service.fetch_current_data(["", None, "INVALID@SYMBOL"])
        assert result == {}
        
        result = await data_service.fetch_current_data([])
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_multiple_symbols_fetch(self, data_service, sample_yfinance_data):
        """Test fetching data for multiple symbols."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = sample_yfinance_data
            mock_ticker.return_value = mock_instance
            
            result = await data_service.fetch_current_data(["AAPL", "MSFT", "GOOGL"])
            
            assert len(result) == 3
            assert "AAPL" in result
            assert "MSFT" in result
            assert "GOOGL" in result
            
            # Each symbol should have data
            for symbol in ["AAPL", "MSFT", "GOOGL"]:
                assert len(result[symbol]) == 5
                assert all(d.symbol == symbol for d in result[symbol])
    
    def test_cache_stats(self, data_service):
        """Test cache statistics functionality."""
        stats = data_service.get_cache_stats()
        assert "size" in stats
        assert "entries" in stats
        assert stats["size"] == 0
        
        # Add some data to cache
        data_service.cache.set("test", {"data": "value"})
        stats = data_service.get_cache_stats()
        assert stats["size"] == 1
    
    def test_clear_cache(self, data_service):
        """Test cache clearing functionality."""
        # Add data to cache
        data_service.cache.set("test", {"data": "value"})
        assert data_service.cache.size() == 1
        
        # Clear cache
        data_service.clear_cache()
        assert data_service.cache.size() == 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, data_service):
        """Test that rate limiting is applied."""
        with patch('time.sleep') as mock_sleep:
            # Reset the last request time
            data_service._last_request_time = 0
            
            # Mock time to simulate rapid successive calls
            with patch('time.time', side_effect=[1.0, 1.05, 1.1, 1.15]):  # More values to avoid StopIteration
                # First call should not sleep (no previous request)
                data_service._rate_limit()
                
                # Second call too soon should sleep
                data_service._rate_limit()
                mock_sleep.assert_called_once()
                # Should sleep for approximately 0.05 seconds (100ms - 50ms)
                call_args = mock_sleep.call_args[0]
                assert abs(call_args[0] - 0.05) < 0.01
    
    @pytest.mark.asyncio
    async def test_historical_data_invalid_date_range(self, data_service):
        """Test historical data with invalid date range."""
        start_date = date(2024, 1, 2)
        end_date = date(2024, 1, 1)  # End before start
        
        result = await data_service.fetch_historical_data(["AAPL"], start_date, end_date)
        assert result == {}


@pytest.mark.integration
class TestDataServiceIntegration:
    """Integration tests that can be run with real API calls (optional)."""
    
    @pytest.mark.skip(reason="Requires real API calls - enable for integration testing")
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test with real yfinance API call (disabled by default)."""
        data_service = DataService()
        
        # Test with a reliable stock symbol
        result = await data_service.fetch_current_data(["AAPL"], period="1d", interval="1m")
        
        assert "AAPL" in result
        assert len(result["AAPL"]) > 0
        assert all(isinstance(d, MarketData) for d in result["AAPL"])
        assert all(d.symbol == "AAPL" for d in result["AAPL"])