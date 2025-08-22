"""
Integration tests for technical indicators with market data models.
"""

import pytest
from datetime import datetime, timedelta
from backend.app.indicators.technical_indicators import TechnicalIndicatorEngine
from backend.app.models.market_data import MarketData, TechnicalIndicators


class TestIndicatorsIntegration:
    """Integration tests for indicators with market data"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = TechnicalIndicatorEngine()
        
        # Create sample market data
        self.market_data_list = []
        base_price = 100.0
        
        for i in range(60):  # 60 data points for sufficient history
            # Simulate realistic market data
            close = base_price + (i * 0.1) + ((-1) ** i * 0.5)  # Trending up with noise
            high = close + 0.5
            low = close - 0.5
            
            market_data = MarketData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1, 9, 30) + timedelta(minutes=i),
                open=close - 0.1,
                high=high,
                low=low,
                close=close,
                volume=1000000
            )
            self.market_data_list.append(market_data)
    
    def test_calculate_indicators_from_market_data(self):
        """Test calculating indicators from MarketData objects"""
        # Extract price arrays from market data
        highs = [md.high for md in self.market_data_list]
        lows = [md.low for md in self.market_data_list]
        closes = [md.close for md in self.market_data_list]
        
        # Calculate indicators
        indicators = self.engine.calculate_all_indicators(highs, lows, closes)
        
        # Verify indicators are calculated correctly
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.ema5 > 0
        assert indicators.ema8 > 0
        assert indicators.ema13 > 0
        assert indicators.ema21 > 0
        assert indicators.ema50 > 0
        assert indicators.atr > 0
        
        # Verify ATR lines are positioned correctly
        current_close = closes[-1]
        assert indicators.atr_long_line < current_close
        assert indicators.atr_short_line > current_close
    
    def test_indicators_serialization(self):
        """Test that calculated indicators can be serialized/deserialized"""
        # Calculate indicators
        highs = [md.high for md in self.market_data_list]
        lows = [md.low for md in self.market_data_list]
        closes = [md.close for md in self.market_data_list]
        
        indicators = self.engine.calculate_all_indicators(highs, lows, closes)
        
        # Test JSON serialization
        json_str = indicators.to_json()
        assert isinstance(json_str, str)
        
        # Test deserialization
        restored_indicators = TechnicalIndicators.from_json(json_str)
        assert restored_indicators.ema5 == indicators.ema5
        assert restored_indicators.ema8 == indicators.ema8
        assert restored_indicators.atr == indicators.atr
        assert restored_indicators.atr_long_line == indicators.atr_long_line
        assert restored_indicators.atr_short_line == indicators.atr_short_line
    
    def test_indicators_with_trending_data(self):
        """Test indicators behavior with trending market data"""
        # Create strongly trending up data
        trending_data = []
        for i in range(60):
            close = 100.0 + (i * 2.0)  # Strong uptrend
            market_data = MarketData(
                symbol="TSLA",
                timestamp=datetime(2024, 1, 1, 9, 30) + timedelta(minutes=i),
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=2000000
            )
            trending_data.append(market_data)
        
        highs = [md.high for md in trending_data]
        lows = [md.low for md in trending_data]
        closes = [md.close for md in trending_data]
        
        indicators = self.engine.calculate_all_indicators(highs, lows, closes)
        
        # In a strong uptrend, shorter EMAs should be higher than longer EMAs
        assert indicators.ema5 > indicators.ema8
        assert indicators.ema8 > indicators.ema13
        assert indicators.ema13 > indicators.ema21
        assert indicators.ema21 > indicators.ema50
        
        # ATR should reflect the volatility
        assert indicators.atr > 0


if __name__ == "__main__":
    pytest.main([__file__])