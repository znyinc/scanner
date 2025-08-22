"""
Unit tests for the algorithm engine signal generation logic.
Tests various market scenarios and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.app.services.algorithm_engine import AlgorithmEngine
from backend.app.models.market_data import MarketData, TechnicalIndicators
from backend.app.models.signals import Signal, AlgorithmSettings
from backend.app.indicators.technical_indicators import InsufficientDataError, IndicatorCalculationError


class TestAlgorithmEngine:
    """Test cases for AlgorithmEngine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = AlgorithmEngine()
        self.base_timestamp = datetime(2024, 1, 1, 10, 0, 0)
        
        # Sample market data
        self.sample_market_data = MarketData(
            symbol="AAPL",
            timestamp=self.base_timestamp,
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            volume=1000000
        )
        
        # Sample technical indicators
        self.sample_indicators = TechnicalIndicators(
            ema5=150.5,
            ema8=150.2,
            ema13=149.8,
            ema21=149.5,
            ema50=149.0,
            atr=2.0,
            atr_long_line=147.0,  # close - (atr * 2)
            atr_short_line=155.0  # close + (atr * 2)
        )
        
        # Default settings
        self.default_settings = AlgorithmSettings()
    
    def create_historical_data(self, count: int, base_price: float = 150.0) -> list[MarketData]:
        """Create historical market data for testing"""
        historical_data = []
        for i in range(count):
            timestamp = self.base_timestamp - timedelta(minutes=count-i)
            price_variation = (i - count/2) * 0.1  # Small price variations
            
            data = MarketData(
                symbol="AAPL",
                timestamp=timestamp,
                open=base_price + price_variation,
                high=base_price + price_variation + 0.5,
                low=base_price + price_variation - 0.5,
                close=base_price + price_variation + 0.2,
                volume=1000000
            )
            historical_data.append(data)
        
        return historical_data
    
    def create_historical_indicators(self, count: int) -> list[TechnicalIndicators]:
        """Create historical indicators for testing"""
        indicators = []
        for i in range(count):
            # Create slightly varying indicators
            base_ema = 150.0 + (i * 0.01)  # Slightly rising trend
            
            indicator = TechnicalIndicators(
                ema5=base_ema + 0.5,
                ema8=base_ema + 0.2,
                ema13=base_ema - 0.2,
                ema21=base_ema - 0.5,
                ema50=base_ema - 1.0,
                atr=2.0,
                atr_long_line=base_ema - 4.0,
                atr_short_line=base_ema + 4.0
            )
            indicators.append(indicator)
        
        return indicators


class TestPolarFormation:
    """Test polar formation checks"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.base_indicators = TechnicalIndicators(
            ema5=150.5, ema8=150.0, ema13=149.5, ema21=149.0, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
    
    def test_bullish_polar_formation_valid(self):
        """Test valid bullish polar formation"""
        # close > open, close > ema8, close > ema21
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000
        )
        
        result = self.engine._check_polar_formation_long(market_data, self.base_indicators)
        assert result is True
    
    def test_bullish_polar_formation_invalid_close_below_open(self):
        """Test invalid bullish polar formation - close below open"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=151.0, high=151.5, low=149.0, close=150.0, volume=1000000
        )
        
        result = self.engine._check_polar_formation_long(market_data, self.base_indicators)
        assert result is False
    
    def test_bullish_polar_formation_invalid_close_below_ema8(self):
        """Test invalid bullish polar formation - close below ema8"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=150.0, low=148.5, close=149.5, volume=1000000  # below ema8 (150.0)
        )
        
        result = self.engine._check_polar_formation_long(market_data, self.base_indicators)
        assert result is False
    
    def test_bearish_polar_formation_valid(self):
        """Test valid bearish polar formation"""
        # close < open, close < ema8, close < ema21
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=150.0, high=150.5, low=148.0, close=148.5, volume=1000000
        )
        
        result = self.engine._check_polar_formation_short(market_data, self.base_indicators)
        assert result is True
    
    def test_bearish_polar_formation_invalid(self):
        """Test invalid bearish polar formation"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000
        )
        
        result = self.engine._check_polar_formation_short(market_data, self.base_indicators)
        assert result is False


class TestEMAPositioning:
    """Test EMA positioning checks"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
    
    def test_long_ema_positioning_valid(self):
        """Test valid long EMA positioning - EMA5 below ATR long line"""
        indicators = TechnicalIndicators(
            ema5=146.0,  # Below ATR long line (147.0)
            ema8=150.0, ema13=149.5, ema21=149.0, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_ema_positioning_long(indicators)
        assert result is True
    
    def test_long_ema_positioning_invalid(self):
        """Test invalid long EMA positioning - EMA5 above ATR long line"""
        indicators = TechnicalIndicators(
            ema5=148.0,  # Above ATR long line (147.0)
            ema8=150.0, ema13=149.5, ema21=149.0, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_ema_positioning_long(indicators)
        assert result is False
    
    def test_short_ema_positioning_valid(self):
        """Test valid short EMA positioning - EMA5 above ATR short line"""
        indicators = TechnicalIndicators(
            ema5=156.0,  # Above ATR short line (155.0)
            ema8=150.0, ema13=149.5, ema21=149.0, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_ema_positioning_short(indicators)
        assert result is True
    
    def test_short_ema_positioning_invalid(self):
        """Test invalid short EMA positioning - EMA5 below ATR short line"""
        indicators = TechnicalIndicators(
            ema5=154.0,  # Below ATR short line (155.0)
            ema8=150.0, ema13=149.5, ema21=149.0, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_ema_positioning_short(indicators)
        assert result is False


class TestEMATrends:
    """Test EMA trend detection"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.settings = AlgorithmSettings(
            ema5_rising_threshold=0.02,
            ema8_rising_threshold=0.01,
            ema21_rising_threshold=0.005
        )
    
    def test_rising_emas_valid(self):
        """Test valid rising EMAs"""
        # Previous indicators
        previous = TechnicalIndicators(
            ema5=100.0, ema8=100.0, ema13=100.0, ema21=100.0, ema50=100.0,
            atr=2.0, atr_long_line=96.0, atr_short_line=104.0
        )
        
        # Current indicators with sufficient rises
        current = TechnicalIndicators(
            ema5=102.1,  # 2.1% rise (> 2.0% threshold)
            ema8=101.1,  # 1.1% rise (> 1.0% threshold)
            ema13=100.6, # 0.6% rise (> 0.5% threshold)
            ema21=100.6, # 0.6% rise (> 0.5% threshold)
            ema50=100.0,
            atr=2.0, atr_long_line=98.2, atr_short_line=106.2
        )
        
        historical_indicators = [previous, current]
        result = self.engine._check_rising_emas(historical_indicators, self.settings)
        assert result is True
    
    def test_rising_emas_insufficient_rise(self):
        """Test rising EMAs with insufficient rise"""
        previous = TechnicalIndicators(
            ema5=100.0, ema8=100.0, ema13=100.0, ema21=100.0, ema50=100.0,
            atr=2.0, atr_long_line=96.0, atr_short_line=104.0
        )
        
        current = TechnicalIndicators(
            ema5=101.0,  # 1.0% rise (< 2.0% threshold)
            ema8=100.5,  # 0.5% rise (< 1.0% threshold)
            ema13=100.3, # 0.3% rise (< 0.5% threshold)
            ema21=100.3, # 0.3% rise (< 0.5% threshold)
            ema50=100.0,
            atr=2.0, atr_long_line=97.0, atr_short_line=105.0
        )
        
        historical_indicators = [previous, current]
        result = self.engine._check_rising_emas(historical_indicators, self.settings)
        assert result is False
    
    def test_falling_emas_valid(self):
        """Test valid falling EMAs"""
        previous = TechnicalIndicators(
            ema5=100.0, ema8=100.0, ema13=100.0, ema21=100.0, ema50=100.0,
            atr=2.0, atr_long_line=96.0, atr_short_line=104.0
        )
        
        current = TechnicalIndicators(
            ema5=97.9,   # -2.1% fall (< -2.0% threshold)
            ema8=98.9,   # -1.1% fall (< -1.0% threshold)
            ema13=99.4,  # -0.6% fall (< -0.5% threshold)
            ema21=99.4,  # -0.6% fall (< -0.5% threshold)
            ema50=100.0,
            atr=2.0, atr_long_line=93.9, atr_short_line=101.9
        )
        
        historical_indicators = [previous, current]
        result = self.engine._check_falling_emas(historical_indicators, self.settings)
        assert result is True
    
    def test_insufficient_historical_data(self):
        """Test EMA trend check with insufficient data"""
        indicators = [TechnicalIndicators(
            ema5=100.0, ema8=100.0, ema13=100.0, ema21=100.0, ema50=100.0,
            atr=2.0, atr_long_line=96.0, atr_short_line=104.0
        )]
        
        result = self.engine._check_rising_emas(indicators, self.settings)
        assert result is False
        
        result = self.engine._check_falling_emas(indicators, self.settings)
        assert result is False


class TestFilters:
    """Test FOMO and volatility filters"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.settings = AlgorithmSettings(fomo_filter=1.0, volatility_filter=1.5)
    
    def test_fomo_filter_pass(self):
        """Test FOMO filter passing"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        indicators = TechnicalIndicators(
            ema5=150.5, ema8=149.5, ema13=149.0, ema21=149.8, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        # Distance from ema8: |150.0 - 149.5| = 0.5 <= 2.0 (atr * fomo_filter)
        # Distance from ema21: |150.0 - 149.8| = 0.2 <= 2.0
        result = self.engine._check_fomo_filter(market_data, indicators, self.settings)
        assert result is True
    
    def test_fomo_filter_fail(self):
        """Test FOMO filter failing"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=155.0, low=148.5, close=154.0, volume=1000000
        )
        
        indicators = TechnicalIndicators(
            ema5=150.5, ema8=149.5, ema13=149.0, ema21=149.8, ema50=148.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        # Distance from ema8: |154.0 - 149.5| = 4.5 > 2.0 (atr * fomo_filter)
        result = self.engine._check_fomo_filter(market_data, indicators, self.settings)
        assert result is False
    
    def test_volatility_filter_pass(self):
        """Test volatility filter passing"""
        indicators = TechnicalIndicators(
            ema5=150.5, ema8=149.5, ema13=149.0, ema21=149.8, ema50=148.5,
            atr=2.0,  # 2.0 >= 0.67 (1.0 / volatility_filter = 1.0 / 1.5)
            atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_volatility_filter(indicators, self.settings)
        assert result is True
    
    def test_volatility_filter_fail(self):
        """Test volatility filter failing"""
        indicators = TechnicalIndicators(
            ema5=150.5, ema8=149.5, ema13=149.0, ema21=149.8, ema50=148.5,
            atr=0.5,  # 0.5 < 0.67 (1.0 / volatility_filter = 1.0 / 1.5)
            atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_volatility_filter(indicators, self.settings)
        assert result is False


class TestHigherTimeframeConfirmation:
    """Test higher timeframe confirmation logic"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
    
    def test_htf_long_confirmation_valid(self):
        """Test valid HTF confirmation for long signals"""
        htf_market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000
        )
        
        htf_indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5,  # ema5 > ema8
            ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_higher_timeframe_confirmation_long(htf_market_data, htf_indicators)
        assert result is True
    
    def test_htf_long_confirmation_invalid_ema_order(self):
        """Test invalid HTF confirmation - wrong EMA order"""
        htf_market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000
        )
        
        htf_indicators = TechnicalIndicators(
            ema5=149.0, ema8=150.0,  # ema5 < ema8 (invalid for long)
            ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_higher_timeframe_confirmation_long(htf_market_data, htf_indicators)
        assert result is False
    
    def test_htf_short_confirmation_valid(self):
        """Test valid HTF confirmation for short signals"""
        htf_market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=150.0, high=150.5, low=148.0, close=148.5, volume=1000000
        )
        
        htf_indicators = TechnicalIndicators(
            ema5=149.0, ema8=149.5,  # ema5 < ema8
            ema13=150.0, ema21=150.5, ema50=151.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        result = self.engine._check_higher_timeframe_confirmation_short(htf_market_data, htf_indicators)
        assert result is True


class TestSignalEvaluation:
    """Test complete signal evaluation logic"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.settings = AlgorithmSettings()
        
        # Mock the indicator engine to avoid complex setup
        self.engine.indicator_engine = Mock()
    
    def create_perfect_long_scenario(self):
        """Create a perfect long signal scenario"""
        # Bullish polar formation: close > open, close > ema8, close > ema21
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000
        )
        
        indicators = TechnicalIndicators(
            ema5=146.0,  # Below ATR long line for positioning
            ema8=149.0,  # close (150.5) > ema8 (149.0) ✓, distance = 1.5 <= 2.0 ✓
            ema13=148.5, 
            ema21=149.0, # close (150.5) > ema21 (149.0) ✓, distance = 1.5 <= 2.0 ✓
            ema50=147.5,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        # Historical indicators showing rising trend
        previous_indicators = TechnicalIndicators(
            ema5=143.0,  # Rising: (146.0 - 143.0) / 143.0 = 2.1% > 2.0% ✓
            ema8=147.5,  # Rising: (149.0 - 147.5) / 147.5 = 1.02% > 1.0% ✓
            ema13=147.0, 
            ema21=147.0, # Rising: (149.0 - 147.0) / 147.0 = 1.36% > 0.5% ✓
            ema50=146.5,
            atr=2.0, atr_long_line=145.0, atr_short_line=153.0
        )
        
        historical_indicators = [previous_indicators, indicators]
        
        htf_market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.5, volume=1000000  # close > open ✓
        )
        
        htf_indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5,  # ema5 > ema8 for HTF confirmation ✓
            ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        return market_data, indicators, historical_indicators, htf_market_data, htf_indicators
    
    def test_long_signal_evaluation_all_conditions_met(self):
        """Test long signal evaluation with all conditions met"""
        market_data, indicators, historical_indicators, htf_market_data, htf_indicators = self.create_perfect_long_scenario()
        
        valid, confidence = self.engine.evaluate_long_conditions(
            market_data, indicators, historical_indicators,
            htf_market_data, htf_indicators, self.settings
        )
        
        assert valid is True
        assert confidence == 1.0  # All 6 conditions met
    
    def test_long_signal_evaluation_without_htf(self):
        """Test long signal evaluation without HTF data"""
        market_data, indicators, historical_indicators, _, _ = self.create_perfect_long_scenario()
        
        valid, confidence = self.engine.evaluate_long_conditions(
            market_data, indicators, historical_indicators,
            None, None, self.settings
        )
        
        assert valid is True
        assert confidence == 1.0  # All 5 conditions met (no HTF)
    
    def test_long_signal_evaluation_partial_conditions(self):
        """Test long signal evaluation with partial conditions met"""
        market_data, indicators, historical_indicators, htf_market_data, htf_indicators = self.create_perfect_long_scenario()
        
        # Make polar formation fail
        market_data.close = 148.0  # Below ema8 and ema21
        
        valid, confidence = self.engine.evaluate_long_conditions(
            market_data, indicators, historical_indicators,
            htf_market_data, htf_indicators, self.settings
        )
        
        assert valid is False
        assert confidence < 1.0  # Not all conditions met
    
    def create_perfect_short_scenario(self):
        """Create a perfect short signal scenario"""
        # Bearish polar formation: close < open, close < ema8, close < ema21
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=150.0, high=150.5, low=148.0, close=148.5, volume=1000000  # close < open ✓
        )
        
        indicators = TechnicalIndicators(
            ema5=156.0,  # Above ATR short line for positioning ✓
            ema8=149.0,  # close (148.5) < ema8 (149.0) ✓, distance = 0.5 <= 2.0 ✓
            ema13=149.5, 
            ema21=149.0, # close (148.5) < ema21 (149.0) ✓, distance = 0.5 <= 2.0 ✓
            ema50=150.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        # Historical indicators showing falling trend
        previous_indicators = TechnicalIndicators(
            ema5=160.0,  # Falling: (156.0 - 160.0) / 160.0 = -2.5% < -2.0% ✓
            ema8=151.0,  # Falling: (149.0 - 151.0) / 151.0 = -1.32% < -1.0% ✓
            ema13=150.5, 
            ema21=150.0, # Falling: (149.0 - 150.0) / 150.0 = -0.67% < -0.5% ✓
            ema50=151.0,
            atr=2.0, atr_long_line=155.0, atr_short_line=163.0
        )
        
        historical_indicators = [previous_indicators, indicators]
        
        htf_market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=150.0, high=150.5, low=148.0, close=148.5, volume=1000000  # close < open ✓
        )
        
        htf_indicators = TechnicalIndicators(
            ema5=149.0, ema8=149.5,  # ema5 < ema8 for HTF confirmation ✓
            ema13=150.0, ema21=150.5, ema50=151.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        return market_data, indicators, historical_indicators, htf_market_data, htf_indicators
    
    def test_short_signal_evaluation_all_conditions_met(self):
        """Test short signal evaluation with all conditions met"""
        market_data, indicators, historical_indicators, htf_market_data, htf_indicators = self.create_perfect_short_scenario()
        
        valid, confidence = self.engine.evaluate_short_conditions(
            market_data, indicators, historical_indicators,
            htf_market_data, htf_indicators, self.settings
        )
        
        assert valid is True
        assert confidence == 1.0  # All 6 conditions met


class TestSignalGeneration:
    """Test complete signal generation workflow"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.settings = AlgorithmSettings()
    
    @patch('backend.app.services.algorithm_engine.AlgorithmEngine.evaluate_long_conditions')
    @patch('backend.app.services.algorithm_engine.AlgorithmEngine.evaluate_short_conditions')
    def test_generate_signals_both_directions(self, mock_short_eval, mock_long_eval):
        """Test signal generation for both long and short"""
        # Mock evaluations to return valid signals
        mock_long_eval.return_value = (True, 0.95)
        mock_short_eval.return_value = (True, 0.90)
        
        # Mock indicator engine
        mock_indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        self.engine.indicator_engine.calculate_all_indicators = Mock(return_value=mock_indicators)
        
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        historical_data = [
            MarketData(
                symbol="AAPL", timestamp=datetime.now() - timedelta(minutes=i),
                open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
            ) for i in range(60, 0, -1)  # 60 periods of historical data
        ]
        
        signals = self.engine.generate_signals(market_data, historical_data, settings=self.settings)
        
        assert len(signals) == 2  # Both long and short signals
        assert any(s.signal_type == "long" for s in signals)
        assert any(s.signal_type == "short" for s in signals)
        assert all(s.symbol == "AAPL" for s in signals)
        assert all(s.confidence > 0 for s in signals)
    
    def test_generate_signals_insufficient_data(self):
        """Test signal generation with insufficient data"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        # Only 10 periods - insufficient for EMA50
        historical_data = [
            MarketData(
                symbol="AAPL", timestamp=datetime.now() - timedelta(minutes=i),
                open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
            ) for i in range(10, 0, -1)
        ]
        
        signals = self.engine.generate_signals(market_data, historical_data, settings=self.settings)
        
        assert len(signals) == 0  # No signals due to insufficient data
    
    @patch('backend.app.services.algorithm_engine.AlgorithmEngine.evaluate_long_conditions')
    @patch('backend.app.services.algorithm_engine.AlgorithmEngine.evaluate_short_conditions')
    def test_generate_signals_no_valid_signals(self, mock_short_eval, mock_long_eval):
        """Test signal generation when no conditions are met"""
        # Mock evaluations to return invalid signals
        mock_long_eval.return_value = (False, 0.3)
        mock_short_eval.return_value = (False, 0.2)
        
        # Mock indicator engine
        mock_indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        self.engine.indicator_engine.calculate_all_indicators = Mock(return_value=mock_indicators)
        
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        historical_data = [
            MarketData(
                symbol="AAPL", timestamp=datetime.now() - timedelta(minutes=i),
                open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
            ) for i in range(60, 0, -1)
        ]
        
        signals = self.engine.generate_signals(market_data, historical_data, settings=self.settings)
        
        assert len(signals) == 0  # No valid signals


class TestErrorHandling:
    """Test error handling in algorithm engine"""
    
    def setup_method(self):
        self.engine = AlgorithmEngine()
        self.settings = AlgorithmSettings()
    
    def test_polar_formation_error_handling(self):
        """Test error handling in polar formation checks"""
        # Create invalid market data that might cause errors
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=float('nan'), high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        indicators = TechnicalIndicators(
            ema5=150.0, ema8=149.5, ema13=149.0, ema21=148.5, ema50=148.0,
            atr=2.0, atr_long_line=147.0, atr_short_line=155.0
        )
        
        # Should handle errors gracefully and return False
        result = self.engine._check_polar_formation_long(market_data, indicators)
        assert result is False
        
        result = self.engine._check_polar_formation_short(market_data, indicators)
        assert result is False
    
    def test_signal_generation_error_handling(self):
        """Test error handling in signal generation"""
        market_data = MarketData(
            symbol="AAPL", timestamp=datetime.now(),
            open=149.0, high=151.0, low=148.5, close=150.0, volume=1000000
        )
        
        # Empty historical data should be handled gracefully
        historical_data = []
        
        signals = self.engine.generate_signals(market_data, historical_data, settings=self.settings)
        assert len(signals) == 0  # Should return empty list, not crash


if __name__ == "__main__":
    pytest.main([__file__])