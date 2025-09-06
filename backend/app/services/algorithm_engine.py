"""
Algorithm engine for signal generation using EMA-ATR strategy.
Implements the core trading logic with polar formation, EMA positioning, and higher timeframe confirmation.
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from ..models.market_data import MarketData, TechnicalIndicators
from ..models.signals import Signal, AlgorithmSettings
from ..indicators.technical_indicators import TechnicalIndicatorEngine, InsufficientDataError, IndicatorCalculationError

logger = logging.getLogger(__name__)


class AlgorithmEngine:
    """Core algorithm engine for generating trading signals."""
    
    def __init__(self):
        self.indicator_engine = TechnicalIndicatorEngine()
        self._last_analysis = None  # Store detailed analysis for diagnostics
    
    def _check_polar_formation_long(self, market_data: MarketData, indicators: TechnicalIndicators) -> bool:
        """
        Check bullish polar formation conditions.
        
        Args:
            market_data: Current market data
            indicators: Technical indicators
            
        Returns:
            True if bullish polar formation is present
        """
        try:
            # Bullish polar formation: close > open, close > ema8, close > ema21
            close_above_open = market_data.close > market_data.open
            close_above_ema8 = market_data.close > indicators.ema8
            close_above_ema21 = market_data.close > indicators.ema21
            
            return close_above_open and close_above_ema8 and close_above_ema21
            
        except Exception as e:
            logger.error(f"Error checking bullish polar formation: {str(e)}")
            return False
    
    def _check_polar_formation_short(self, market_data: MarketData, indicators: TechnicalIndicators) -> bool:
        """
        Check bearish polar formation conditions.
        
        Args:
            market_data: Current market data
            indicators: Technical indicators
            
        Returns:
            True if bearish polar formation is present
        """
        try:
            # Bearish polar formation: close < open, close < ema8, close < ema21
            close_below_open = market_data.close < market_data.open
            close_below_ema8 = market_data.close < indicators.ema8
            close_below_ema21 = market_data.close < indicators.ema21
            
            return close_below_open and close_below_ema8 and close_below_ema21
            
        except Exception as e:
            logger.error(f"Error checking bearish polar formation: {str(e)}")
            return False
    
    def _check_ema_positioning_long(self, indicators: TechnicalIndicators) -> bool:
        """
        Check EMA positioning for long signals.
        
        Args:
            indicators: Technical indicators
            
        Returns:
            True if EMA5 is below ATR long line
        """
        try:
            return indicators.ema5 < indicators.atr_long_line
        except Exception as e:
            logger.error(f"Error checking long EMA positioning: {str(e)}")
            return False
    
    def _check_ema_positioning_short(self, indicators: TechnicalIndicators) -> bool:
        """
        Check EMA positioning for short signals.
        
        Args:
            indicators: Technical indicators
            
        Returns:
            True if EMA5 is above ATR short line
        """
        try:
            return indicators.ema5 > indicators.atr_short_line
        except Exception as e:
            logger.error(f"Error checking short EMA positioning: {str(e)}")
            return False
    
    def _check_rising_emas(self, historical_indicators: List[TechnicalIndicators], 
                          settings: AlgorithmSettings) -> bool:
        """
        Check if EMAs are rising based on configurable thresholds.
        
        Args:
            historical_indicators: List of indicators (most recent last)
            settings: Algorithm settings with thresholds
            
        Returns:
            True if EMAs are rising above thresholds
        """
        try:
            if len(historical_indicators) < 2:
                logger.warning("Insufficient historical data for EMA rising check")
                return False
            
            current = historical_indicators[-1]
            previous = historical_indicators[-2]
            
            # Calculate percentage changes
            ema5_change = (current.ema5 - previous.ema5) / previous.ema5
            ema8_change = (current.ema8 - previous.ema8) / previous.ema8
            ema21_change = (current.ema21 - previous.ema21) / previous.ema21
            
            # Check if changes exceed thresholds
            ema5_rising = ema5_change >= settings.ema5_rising_threshold
            ema8_rising = ema8_change >= settings.ema8_rising_threshold
            ema21_rising = ema21_change >= settings.ema21_rising_threshold
            
            return ema5_rising and ema8_rising and ema21_rising
            
        except Exception as e:
            logger.error(f"Error checking rising EMAs: {str(e)}")
            return False
    
    def _check_falling_emas(self, historical_indicators: List[TechnicalIndicators], 
                           settings: AlgorithmSettings) -> bool:
        """
        Check if EMAs are falling based on configurable thresholds.
        
        Args:
            historical_indicators: List of indicators (most recent last)
            settings: Algorithm settings with thresholds
            
        Returns:
            True if EMAs are falling below negative thresholds
        """
        try:
            if len(historical_indicators) < 2:
                logger.warning("Insufficient historical data for EMA falling check")
                return False
            
            current = historical_indicators[-1]
            previous = historical_indicators[-2]
            
            # Calculate percentage changes
            ema5_change = (current.ema5 - previous.ema5) / previous.ema5
            ema8_change = (current.ema8 - previous.ema8) / previous.ema8
            ema21_change = (current.ema21 - previous.ema21) / previous.ema21
            
            # Check if changes are below negative thresholds
            ema5_falling = ema5_change <= -settings.ema5_rising_threshold
            ema8_falling = ema8_change <= -settings.ema8_rising_threshold
            ema21_falling = ema21_change <= -settings.ema21_rising_threshold
            
            return ema5_falling and ema8_falling and ema21_falling
            
        except Exception as e:
            logger.error(f"Error checking falling EMAs: {str(e)}")
            return False
    
    def _check_fomo_filter(self, market_data: MarketData, indicators: TechnicalIndicators, 
                          settings: AlgorithmSettings) -> bool:
        """
        Check FOMO filter condition.
        
        Args:
            market_data: Current market data
            indicators: Technical indicators
            settings: Algorithm settings
            
        Returns:
            True if FOMO filter passes (no FOMO condition detected)
        """
        try:
            # FOMO filter: check if price is not too far from EMAs
            # Using ATR as a measure of acceptable distance
            max_distance = indicators.atr * settings.fomo_filter
            
            # Check distance from key EMAs
            distance_from_ema8 = abs(market_data.close - indicators.ema8)
            distance_from_ema21 = abs(market_data.close - indicators.ema21)
            
            # Pass filter if distances are within acceptable range
            return distance_from_ema8 <= max_distance and distance_from_ema21 <= max_distance
            
        except Exception as e:
            logger.error(f"Error checking FOMO filter: {str(e)}")
            return False
    
    def _check_volatility_filter(self, indicators: TechnicalIndicators, 
                                settings: AlgorithmSettings) -> bool:
        """
        Check volatility filter condition.
        
        Args:
            indicators: Technical indicators
            settings: Algorithm settings
            
        Returns:
            True if volatility is acceptable
        """
        try:
            # Simple volatility check using ATR
            # ATR should be above a minimum threshold (e.g., 1.0 for reasonable volatility)
            min_atr_threshold = 1.0 / settings.volatility_filter
            return indicators.atr >= min_atr_threshold
            
        except Exception as e:
            logger.error(f"Error checking volatility filter: {str(e)}")
            return False   
 
    def _check_higher_timeframe_confirmation_long(self, htf_market_data: MarketData, 
                                                 htf_indicators: TechnicalIndicators) -> bool:
        """
        Check higher timeframe confirmation for long signals.
        
        Args:
            htf_market_data: Higher timeframe market data
            htf_indicators: Higher timeframe technical indicators
            
        Returns:
            True if higher timeframe confirms long signal
        """
        try:
            # HTF confirmation: HTF EMA5 > HTF EMA8, close > open (bullish candle)
            ema5_above_ema8 = htf_indicators.ema5 > htf_indicators.ema8
            bullish_candle = htf_market_data.close > htf_market_data.open
            
            return ema5_above_ema8 and bullish_candle
            
        except Exception as e:
            logger.error(f"Error checking HTF confirmation for long: {str(e)}")
            return False
    
    def _check_higher_timeframe_confirmation_short(self, htf_market_data: MarketData, 
                                                  htf_indicators: TechnicalIndicators) -> bool:
        """
        Check higher timeframe confirmation for short signals.
        
        Args:
            htf_market_data: Higher timeframe market data
            htf_indicators: Higher timeframe technical indicators
            
        Returns:
            True if higher timeframe confirms short signal
        """
        try:
            # HTF confirmation: HTF EMA5 < HTF EMA8, close < open (bearish candle)
            ema5_below_ema8 = htf_indicators.ema5 < htf_indicators.ema8
            bearish_candle = htf_market_data.close < htf_market_data.open
            
            return ema5_below_ema8 and bearish_candle
            
        except Exception as e:
            logger.error(f"Error checking HTF confirmation for short: {str(e)}")
            return False
    
    def evaluate_long_conditions(self, market_data: MarketData, indicators: TechnicalIndicators,
                               historical_indicators: List[TechnicalIndicators],
                               htf_market_data: Optional[MarketData],
                               htf_indicators: Optional[TechnicalIndicators],
                               settings: AlgorithmSettings) -> Tuple[bool, float]:
        """
        Evaluate all long signal conditions.
        
        Args:
            market_data: Current market data
            indicators: Current technical indicators
            historical_indicators: Historical indicators for trend analysis
            htf_market_data: Higher timeframe market data (optional)
            htf_indicators: Higher timeframe indicators (optional)
            settings: Algorithm settings
            
        Returns:
            Tuple of (signal_valid, confidence_score)
        """
        try:
            conditions_met = 0
            total_conditions = 5  # Will be 6 if HTF data is available
            rejection_reasons = []
            partial_criteria = []
            
            # Check polar formation
            if self._check_polar_formation_long(market_data, indicators):
                conditions_met += 1
                partial_criteria.append("Bullish polar formation")
                logger.debug(f"Long polar formation check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed bullish polar formation")
            
            # Check EMA positioning
            if self._check_ema_positioning_long(indicators):
                conditions_met += 1
                partial_criteria.append("EMA5 below ATR long line")
                logger.debug(f"Long EMA positioning check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("EMA5 not below ATR long line")
            
            # Check rising EMAs
            if self._check_rising_emas(historical_indicators, settings):
                conditions_met += 1
                partial_criteria.append("Rising EMAs")
                logger.debug(f"Rising EMAs check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("EMAs not rising sufficiently")
            
            # Check FOMO filter
            if self._check_fomo_filter(market_data, indicators, settings):
                conditions_met += 1
                partial_criteria.append("FOMO filter passed")
                logger.debug(f"FOMO filter check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed FOMO filter (price too extended)")
            
            # Check volatility filter
            if self._check_volatility_filter(indicators, settings):
                conditions_met += 1
                partial_criteria.append("Volatility filter passed")
                logger.debug(f"Volatility filter check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed volatility filter")
            
            # Check higher timeframe confirmation if available
            htf_confirmed = True
            if htf_market_data and htf_indicators:
                total_conditions = 6
                if self._check_higher_timeframe_confirmation_long(htf_market_data, htf_indicators):
                    conditions_met += 1
                    partial_criteria.append("HTF confirmation")
                    logger.debug(f"HTF confirmation check passed for {market_data.symbol}")
                else:
                    htf_confirmed = False
                    rejection_reasons.append("Failed HTF confirmation")
            else:
                rejection_reasons.append("No HTF data available")
            
            # Calculate confidence score
            confidence = conditions_met / total_conditions
            
            # Signal is valid if all conditions are met
            signal_valid = conditions_met == total_conditions
            
            # Store analysis for diagnostics
            self._last_analysis = {
                'signal_type': 'long',
                'conditions_met': conditions_met,
                'total_conditions': total_conditions,
                'rejection_reasons': rejection_reasons,
                'partial_criteria': partial_criteria,
                'confidence': confidence,
                'signal_valid': signal_valid
            }
            
            if signal_valid:
                logger.info(f"Long signal generated for {market_data.symbol} with confidence {confidence:.2f}")
            
            return signal_valid, confidence
            
        except Exception as e:
            logger.error(f"Error evaluating long conditions for {market_data.symbol}: {str(e)}")
            self._last_analysis = {
                'signal_type': 'long',
                'error': str(e),
                'rejection_reasons': [f"Algorithm error: {str(e)}"],
                'partial_criteria': [],
                'confidence': 0.0,
                'signal_valid': False
            }
            return False, 0.0
    
    def evaluate_short_conditions(self, market_data: MarketData, indicators: TechnicalIndicators,
                                historical_indicators: List[TechnicalIndicators],
                                htf_market_data: Optional[MarketData],
                                htf_indicators: Optional[TechnicalIndicators],
                                settings: AlgorithmSettings) -> Tuple[bool, float]:
        """
        Evaluate all short signal conditions.
        
        Args:
            market_data: Current market data
            indicators: Current technical indicators
            historical_indicators: Historical indicators for trend analysis
            htf_market_data: Higher timeframe market data (optional)
            htf_indicators: Higher timeframe indicators (optional)
            settings: Algorithm settings
            
        Returns:
            Tuple of (signal_valid, confidence_score)
        """
        try:
            conditions_met = 0
            total_conditions = 5  # Will be 6 if HTF data is available
            rejection_reasons = []
            partial_criteria = []
            
            # Check polar formation
            if self._check_polar_formation_short(market_data, indicators):
                conditions_met += 1
                partial_criteria.append("Bearish polar formation")
                logger.debug(f"Short polar formation check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed bearish polar formation")
            
            # Check EMA positioning
            if self._check_ema_positioning_short(indicators):
                conditions_met += 1
                partial_criteria.append("EMA5 above ATR short line")
                logger.debug(f"Short EMA positioning check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("EMA5 not above ATR short line")
            
            # Check falling EMAs
            if self._check_falling_emas(historical_indicators, settings):
                conditions_met += 1
                partial_criteria.append("Falling EMAs")
                logger.debug(f"Falling EMAs check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("EMAs not falling sufficiently")
            
            # Check FOMO filter
            if self._check_fomo_filter(market_data, indicators, settings):
                conditions_met += 1
                partial_criteria.append("FOMO filter passed")
                logger.debug(f"FOMO filter check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed FOMO filter (price too extended)")
            
            # Check volatility filter
            if self._check_volatility_filter(indicators, settings):
                conditions_met += 1
                partial_criteria.append("Volatility filter passed")
                logger.debug(f"Volatility filter check passed for {market_data.symbol}")
            else:
                rejection_reasons.append("Failed volatility filter")
            
            # Check higher timeframe confirmation if available
            if htf_market_data and htf_indicators:
                total_conditions = 6
                if self._check_higher_timeframe_confirmation_short(htf_market_data, htf_indicators):
                    conditions_met += 1
                    partial_criteria.append("HTF confirmation")
                    logger.debug(f"HTF confirmation check passed for {market_data.symbol}")
                else:
                    rejection_reasons.append("Failed HTF confirmation")
            else:
                rejection_reasons.append("No HTF data available")
            
            # Calculate confidence score
            confidence = conditions_met / total_conditions
            
            # Signal is valid if all conditions are met
            signal_valid = conditions_met == total_conditions
            
            # Store analysis for diagnostics
            self._last_analysis = {
                'signal_type': 'short',
                'conditions_met': conditions_met,
                'total_conditions': total_conditions,
                'rejection_reasons': rejection_reasons,
                'partial_criteria': partial_criteria,
                'confidence': confidence,
                'signal_valid': signal_valid
            }
            
            if signal_valid:
                logger.info(f"Short signal generated for {market_data.symbol} with confidence {confidence:.2f}")
            
            return signal_valid, confidence
            
        except Exception as e:
            logger.error(f"Error evaluating short conditions for {market_data.symbol}: {str(e)}")
            self._last_analysis = {
                'signal_type': 'short',
                'error': str(e),
                'rejection_reasons': [f"Algorithm error: {str(e)}"],
                'partial_criteria': [],
                'confidence': 0.0,
                'signal_valid': False
            }
            return False, 0.0
    
    def generate_signals(self, market_data: MarketData, 
                        historical_data: List[MarketData],
                        htf_market_data: Optional[MarketData] = None,
                        htf_historical_data: Optional[List[MarketData]] = None,
                        settings: AlgorithmSettings = None) -> List[Signal]:
        """
        Generate trading signals for given market data.
        
        Args:
            market_data: Current market data
            historical_data: Historical market data for indicator calculation
            htf_market_data: Higher timeframe market data (optional)
            htf_historical_data: Higher timeframe historical data (optional)
            settings: Algorithm settings (uses defaults if None)
            
        Returns:
            List of generated signals
        """
        if settings is None:
            settings = AlgorithmSettings()
        
        signals = []
        
        try:
            # Prepare price data for indicator calculation
            all_data = historical_data + [market_data]
            high_prices = [d.high for d in all_data]
            low_prices = [d.low for d in all_data]
            close_prices = [d.close for d in all_data]
            
            # Calculate current indicators
            indicators = self.indicator_engine.calculate_all_indicators(
                high_prices, low_prices, close_prices, settings.atr_multiplier
            )
            
            # Calculate historical indicators for trend analysis
            historical_indicators = []
            for i in range(len(historical_data)):
                hist_high = [d.high for d in historical_data[:i+1]]
                hist_low = [d.low for d in historical_data[:i+1]]
                hist_close = [d.close for d in historical_data[:i+1]]
                
                if len(hist_close) >= 50:  # Minimum data for all indicators
                    hist_indicators = self.indicator_engine.calculate_all_indicators(
                        hist_high, hist_low, hist_close, settings.atr_multiplier
                    )
                    historical_indicators.append(hist_indicators)
            
            # Add current indicators
            historical_indicators.append(indicators)
            
            # Calculate HTF indicators if data is available
            htf_indicators = None
            if htf_market_data and htf_historical_data:
                htf_all_data = htf_historical_data + [htf_market_data]
                htf_high_prices = [d.high for d in htf_all_data]
                htf_low_prices = [d.low for d in htf_all_data]
                htf_close_prices = [d.close for d in htf_all_data]
                
                htf_indicators = self.indicator_engine.calculate_all_indicators(
                    htf_high_prices, htf_low_prices, htf_close_prices, settings.atr_multiplier
                )
            
            # Evaluate long conditions
            long_valid, long_confidence = self.evaluate_long_conditions(
                market_data, indicators, historical_indicators,
                htf_market_data, htf_indicators, settings
            )
            
            if long_valid:
                long_signal = Signal(
                    symbol=market_data.symbol,
                    signal_type="long",
                    timestamp=market_data.timestamp,
                    price=market_data.close,
                    indicators=indicators,
                    confidence=long_confidence
                )
                signals.append(long_signal)
            
            # Evaluate short conditions
            short_valid, short_confidence = self.evaluate_short_conditions(
                market_data, indicators, historical_indicators,
                htf_market_data, htf_indicators, settings
            )
            
            if short_valid:
                short_signal = Signal(
                    symbol=market_data.symbol,
                    signal_type="short",
                    timestamp=market_data.timestamp,
                    price=market_data.close,
                    indicators=indicators,
                    confidence=short_confidence
                )
                signals.append(short_signal)
            
            return signals
            
        except (InsufficientDataError, IndicatorCalculationError) as e:
            logger.warning(f"Cannot generate signals for {market_data.symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error generating signals for {market_data.symbol}: {str(e)}")
            return []
    
    def get_last_analysis(self) -> Optional[dict]:
        """
        Get the detailed analysis from the last signal evaluation.
        
        Returns:
            Dictionary with analysis details or None if no analysis available
        """
        return self._last_analysis