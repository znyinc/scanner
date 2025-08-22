"""
Unit tests for technical indicators calculation engine.
"""

import pytest
import numpy as np
from backend.app.indicators.technical_indicators import (
    TechnicalIndicatorEngine,
    InsufficientDataError,
    IndicatorCalculationError
)
from backend.app.models.market_data import TechnicalIndicators


class TestTechnicalIndicatorEngine:
    """Test cases for TechnicalIndicatorEngine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = TechnicalIndicatorEngine()
        
        # Sample price data for testing (100 data points)
        np.random.seed(42)  # For reproducible tests
        base_price = 100.0
        self.sample_closes = []
        self.sample_highs = []
        self.sample_lows = []
        
        for i in range(100):
            # Generate realistic OHLC data
            close = base_price + np.random.normal(0, 2)
            high = close + abs(np.random.normal(0, 1))
            low = close - abs(np.random.normal(0, 1))
            
            self.sample_closes.append(close)
            self.sample_highs.append(high)
            self.sample_lows.append(low)
            base_price = close  # Trend continuation
    
    def test_ema_calculation_valid_data(self):
        """Test EMA calculation with valid data"""
        # Test EMA5
        ema5 = self.engine.calculate_ema(self.sample_closes, 5)
        assert isinstance(ema5, float)
        assert not np.isnan(ema5)
        assert not np.isinf(ema5)
        
        # Test EMA50
        ema50 = self.engine.calculate_ema(self.sample_closes, 50)
        assert isinstance(ema50, float)
        assert not np.isnan(ema50)
        assert not np.isinf(ema50)
    
    def test_ema_calculation_insufficient_data(self):
        """Test EMA calculation with insufficient data"""
        short_data = [100.0, 101.0, 102.0]  # Only 3 data points
        
        with pytest.raises(InsufficientDataError):
            self.engine.calculate_ema(short_data, 5)
    
    def test_ema_calculation_empty_data(self):
        """Test EMA calculation with empty data"""
        with pytest.raises(InsufficientDataError):
            self.engine.calculate_ema([], 5)
    
    def test_ema_calculation_invalid_data(self):
        """Test EMA calculation with invalid data"""
        invalid_data = [float('nan')] * 10
        
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_ema(invalid_data, 5)
    
    def test_ema_different_periods(self):
        """Test EMA calculation for different periods"""
        periods = [5, 8, 13, 21, 50]
        emas = {}
        
        for period in periods:
            emas[period] = self.engine.calculate_ema(self.sample_closes, period)
        
        # Longer period EMAs should be smoother (less responsive to recent changes)
        # This is a general property but not always true for every data point
        assert all(isinstance(ema, float) for ema in emas.values())
    
    def test_atr_calculation_valid_data(self):
        """Test ATR calculation with valid data"""
        atr = self.engine.calculate_atr(
            self.sample_highs, 
            self.sample_lows, 
            self.sample_closes, 
            14
        )
        
        assert isinstance(atr, float)
        assert atr > 0
        assert not np.isnan(atr)
        assert not np.isinf(atr)
    
    def test_atr_calculation_insufficient_data(self):
        """Test ATR calculation with insufficient data"""
        short_highs = [101.0, 102.0]
        short_lows = [99.0, 100.0]
        short_closes = [100.0, 101.0]
        
        with pytest.raises(InsufficientDataError):
            self.engine.calculate_atr(short_highs, short_lows, short_closes, 14)
    
    def test_atr_calculation_mismatched_arrays(self):
        """Test ATR calculation with mismatched array lengths"""
        highs = [101.0] * 20
        lows = [99.0] * 15  # Different length
        closes = [100.0] * 20
        
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_atr(highs, lows, closes, 14)
    
    def test_atr_calculation_invalid_data(self):
        """Test ATR calculation with invalid price relationships"""
        # Create data where low > high (invalid)
        invalid_highs = [99.0] * 20
        invalid_lows = [101.0] * 20  # Low higher than high
        closes = [100.0] * 20
        
        # Should still calculate but result might be unusual
        atr = self.engine.calculate_atr(invalid_highs, invalid_lows, closes, 14)
        assert isinstance(atr, float)
        assert atr >= 0
    
    def test_atr_lines_calculation(self):
        """Test ATR lines calculation"""
        close_price = 100.0
        atr = 2.0
        multiplier = 2.0
        
        long_line, short_line = self.engine.calculate_atr_lines(close_price, atr, multiplier)
        
        assert isinstance(long_line, float)
        assert isinstance(short_line, float)
        assert long_line == 96.0  # 100 - (2 * 2)
        assert short_line == 104.0  # 100 + (2 * 2)
    
    def test_atr_lines_invalid_inputs(self):
        """Test ATR lines calculation with invalid inputs"""
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_atr_lines(-100.0, 2.0, 2.0)  # Negative close
        
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_atr_lines(100.0, -2.0, 2.0)  # Negative ATR
        
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_atr_lines(100.0, 2.0, -2.0)  # Negative multiplier
    
    def test_data_sufficiency_validation(self):
        """Test data sufficiency validation"""
        # Should pass with sufficient data
        self.engine.validate_data_sufficiency(100)
        
        # Should fail with insufficient data
        with pytest.raises(InsufficientDataError):
            self.engine.validate_data_sufficiency(10)
    
    def test_calculate_all_indicators_valid_data(self):
        """Test calculation of all indicators with valid data"""
        indicators = self.engine.calculate_all_indicators(
            self.sample_highs,
            self.sample_lows,
            self.sample_closes,
            atr_multiplier=2.0
        )
        
        assert isinstance(indicators, TechnicalIndicators)
        
        # Check all EMAs are calculated
        assert isinstance(indicators.ema5, float)
        assert isinstance(indicators.ema8, float)
        assert isinstance(indicators.ema13, float)
        assert isinstance(indicators.ema21, float)
        assert isinstance(indicators.ema50, float)
        
        # Check ATR and lines are calculated
        assert isinstance(indicators.atr, float)
        assert indicators.atr > 0
        assert isinstance(indicators.atr_long_line, float)
        assert isinstance(indicators.atr_short_line, float)
        
        # ATR lines should be on opposite sides of current price
        current_close = self.sample_closes[-1]
        assert indicators.atr_long_line < current_close
        assert indicators.atr_short_line > current_close
    
    def test_calculate_all_indicators_insufficient_data(self):
        """Test calculation of all indicators with insufficient data"""
        short_highs = [101.0] * 10
        short_lows = [99.0] * 10
        short_closes = [100.0] * 10
        
        with pytest.raises(InsufficientDataError):
            self.engine.calculate_all_indicators(short_highs, short_lows, short_closes)
    
    def test_calculate_all_indicators_mismatched_arrays(self):
        """Test calculation of all indicators with mismatched arrays"""
        highs = [101.0] * 100
        lows = [99.0] * 50  # Different length
        closes = [100.0] * 100
        
        with pytest.raises(IndicatorCalculationError):
            self.engine.calculate_all_indicators(highs, lows, closes)
    
    def test_ema_mathematical_properties(self):
        """Test mathematical properties of EMA calculation"""
        # Create trending data
        trending_up = list(range(1, 101))  # 1 to 100
        trending_down = list(range(100, 0, -1))  # 100 to 1
        
        ema5_up = self.engine.calculate_ema(trending_up, 5)
        ema21_up = self.engine.calculate_ema(trending_up, 21)
        
        ema5_down = self.engine.calculate_ema(trending_down, 5)
        ema21_down = self.engine.calculate_ema(trending_down, 21)
        
        # In uptrend, shorter EMA should be higher than longer EMA
        assert ema5_up > ema21_up
        
        # In downtrend, shorter EMA should be lower than longer EMA
        assert ema5_down < ema21_down
    
    def test_atr_with_different_volatility(self):
        """Test ATR calculation with different volatility scenarios"""
        # Low volatility data
        low_vol_highs = [100.1] * 50
        low_vol_lows = [99.9] * 50
        low_vol_closes = [100.0] * 50
        
        # High volatility data
        high_vol_highs = [110.0, 90.0] * 25
        high_vol_lows = [90.0, 110.0] * 25
        high_vol_closes = [100.0] * 50
        
        atr_low = self.engine.calculate_atr(low_vol_highs, low_vol_lows, low_vol_closes, 14)
        atr_high = self.engine.calculate_atr(high_vol_highs, high_vol_lows, high_vol_closes, 14)
        
        # High volatility should result in higher ATR
        assert atr_high > atr_low
    
    def test_edge_case_single_price_level(self):
        """Test indicators with constant price data"""
        constant_price = 100.0
        constant_highs = [constant_price] * 60
        constant_lows = [constant_price] * 60
        constant_closes = [constant_price] * 60
        
        indicators = self.engine.calculate_all_indicators(
            constant_highs, constant_lows, constant_closes
        )
        
        # All EMAs should equal the constant price
        assert abs(indicators.ema5 - constant_price) < 0.001
        assert abs(indicators.ema8 - constant_price) < 0.001
        assert abs(indicators.ema13 - constant_price) < 0.001
        assert abs(indicators.ema21 - constant_price) < 0.001
        assert abs(indicators.ema50 - constant_price) < 0.001
        
        # ATR should be very close to zero
        assert indicators.atr < 0.001
    
    def test_custom_atr_multiplier(self):
        """Test ATR lines with custom multiplier"""
        indicators_2x = self.engine.calculate_all_indicators(
            self.sample_highs, self.sample_lows, self.sample_closes, atr_multiplier=2.0
        )
        
        indicators_3x = self.engine.calculate_all_indicators(
            self.sample_highs, self.sample_lows, self.sample_closes, atr_multiplier=3.0
        )
        
        current_close = self.sample_closes[-1]
        
        # Higher multiplier should create wider bands
        assert (current_close - indicators_3x.atr_long_line) > (current_close - indicators_2x.atr_long_line)
        assert (indicators_3x.atr_short_line - current_close) > (indicators_2x.atr_short_line - current_close)


class TestTechnicalIndicatorsDataClass:
    """Test the TechnicalIndicators dataclass"""
    
    def test_technical_indicators_creation(self):
        """Test creation of TechnicalIndicators object"""
        indicators = TechnicalIndicators(
            ema5=100.5,
            ema8=100.3,
            ema13=100.1,
            ema21=99.9,
            ema50=99.5,
            atr=2.5,
            atr_long_line=95.0,
            atr_short_line=105.0
        )
        
        assert indicators.ema5 == 100.5
        assert indicators.ema8 == 100.3
        assert indicators.ema13 == 100.1
        assert indicators.ema21 == 99.9
        assert indicators.ema50 == 99.5
        assert indicators.atr == 2.5
        assert indicators.atr_long_line == 95.0
        assert indicators.atr_short_line == 105.0


if __name__ == "__main__":
    pytest.main([__file__])