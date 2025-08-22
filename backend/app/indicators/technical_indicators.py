"""
Technical indicators calculation engine for the stock scanner.
Implements EMA and ATR calculations with proper error handling.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import logging
from ..models.market_data import TechnicalIndicators

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when there's insufficient data for indicator calculation"""
    pass


class IndicatorCalculationError(Exception):
    """Raised when indicator calculation fails"""
    pass


class TechnicalIndicatorEngine:
    """Engine for calculating technical indicators"""
    
    def __init__(self):
        self.required_periods = {
            'ema5': 5,
            'ema8': 8,
            'ema13': 13,
            'ema21': 21,
            'ema50': 50,
            'atr': 14
        }
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average for given period.
        
        Args:
            prices: List of price values (most recent last)
            period: EMA period
            
        Returns:
            EMA value
            
        Raises:
            InsufficientDataError: If not enough data points
            IndicatorCalculationError: If calculation fails
        """
        if len(prices) < period:
            raise InsufficientDataError(
                f"Need at least {period} data points for EMA{period}, got {len(prices)}"
            )
        
        try:
            # Convert to pandas Series for efficient calculation
            price_series = pd.Series(prices)
            ema = price_series.ewm(span=period, adjust=False).mean().iloc[-1]
            
            if pd.isna(ema) or np.isinf(ema):
                raise IndicatorCalculationError(f"Invalid EMA{period} calculation result")
                
            return float(ema)
            
        except Exception as e:
            logger.error(f"EMA{period} calculation failed: {str(e)}")
            raise IndicatorCalculationError(f"EMA{period} calculation failed: {str(e)}")
    
    def calculate_atr(self, high_prices: List[float], low_prices: List[float], 
                     close_prices: List[float], period: int = 14) -> float:
        """
        Calculate Average True Range.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices  
            close_prices: List of close prices
            period: ATR period (default 14)
            
        Returns:
            ATR value
            
        Raises:
            InsufficientDataError: If not enough data points
            IndicatorCalculationError: If calculation fails
        """
        if len(high_prices) < period + 1 or len(low_prices) < period + 1 or len(close_prices) < period + 1:
            raise InsufficientDataError(
                f"Need at least {period + 1} data points for ATR{period}"
            )
        
        if not (len(high_prices) == len(low_prices) == len(close_prices)):
            raise IndicatorCalculationError("High, low, and close price arrays must have same length")
        
        try:
            # Calculate True Range for each period
            true_ranges = []
            
            for i in range(1, len(close_prices)):
                high_low = high_prices[i] - low_prices[i]
                high_close_prev = abs(high_prices[i] - close_prices[i-1])
                low_close_prev = abs(low_prices[i] - close_prices[i-1])
                
                true_range = max(high_low, high_close_prev, low_close_prev)
                true_ranges.append(true_range)
            
            if len(true_ranges) < period:
                raise InsufficientDataError(
                    f"Insufficient true range data points for ATR{period}"
                )
            
            # Calculate ATR as EMA of True Range
            tr_series = pd.Series(true_ranges)
            atr = tr_series.ewm(span=period, adjust=False).mean().iloc[-1]
            
            if pd.isna(atr) or np.isinf(atr) or atr < 0:
                raise IndicatorCalculationError("Invalid ATR calculation result")
                
            return float(atr)
            
        except Exception as e:
            logger.error(f"ATR{period} calculation failed: {str(e)}")
            raise IndicatorCalculationError(f"ATR{period} calculation failed: {str(e)}")
    
    def calculate_atr_lines(self, close_price: float, atr: float, 
                           multiplier: float = 2.0) -> tuple[float, float]:
        """
        Calculate ATR long and short lines.
        
        Args:
            close_price: Current close price
            atr: ATR value
            multiplier: ATR multiplier (default 2.0)
            
        Returns:
            Tuple of (atr_long_line, atr_short_line)
            
        Raises:
            IndicatorCalculationError: If calculation fails
        """
        try:
            if close_price <= 0 or atr < 0 or multiplier <= 0:
                raise IndicatorCalculationError("Invalid input values for ATR lines calculation")
            
            atr_long_line = close_price - (atr * multiplier)
            atr_short_line = close_price + (atr * multiplier)
            
            return float(atr_long_line), float(atr_short_line)
            
        except Exception as e:
            logger.error(f"ATR lines calculation failed: {str(e)}")
            raise IndicatorCalculationError(f"ATR lines calculation failed: {str(e)}")
    
    def validate_data_sufficiency(self, data_length: int) -> None:
        """
        Validate if there's sufficient data for all indicators.
        
        Args:
            data_length: Number of available data points
            
        Raises:
            InsufficientDataError: If not enough data
        """
        max_required = max(self.required_periods.values()) + 1  # +1 for ATR calculation
        
        if data_length < max_required:
            raise InsufficientDataError(
                f"Need at least {max_required} data points for all indicators, got {data_length}"
            )
    
    def calculate_all_indicators(self, high_prices: List[float], low_prices: List[float],
                               close_prices: List[float], atr_multiplier: float = 2.0) -> TechnicalIndicators:
        """
        Calculate all technical indicators for the given price data.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of close prices
            atr_multiplier: Multiplier for ATR lines (default 2.0)
            
        Returns:
            TechnicalIndicators object with all calculated values
            
        Raises:
            InsufficientDataError: If not enough data points
            IndicatorCalculationError: If any calculation fails
        """
        try:
            # Validate input data
            if not (len(high_prices) == len(low_prices) == len(close_prices)):
                raise IndicatorCalculationError("Price arrays must have same length")
            
            self.validate_data_sufficiency(len(close_prices))
            
            # Calculate EMAs
            ema5 = self.calculate_ema(close_prices, 5)
            ema8 = self.calculate_ema(close_prices, 8)
            ema13 = self.calculate_ema(close_prices, 13)
            ema21 = self.calculate_ema(close_prices, 21)
            ema50 = self.calculate_ema(close_prices, 50)
            
            # Calculate ATR
            atr = self.calculate_atr(high_prices, low_prices, close_prices, 14)
            
            # Calculate ATR lines
            current_close = close_prices[-1]
            atr_long_line, atr_short_line = self.calculate_atr_lines(
                current_close, atr, atr_multiplier
            )
            
            return TechnicalIndicators(
                ema5=ema5,
                ema8=ema8,
                ema13=ema13,
                ema21=ema21,
                ema50=ema50,
                atr=atr,
                atr_long_line=atr_long_line,
                atr_short_line=atr_short_line
            )
            
        except (InsufficientDataError, IndicatorCalculationError):
            raise
        except Exception as e:
            logger.error(f"Indicator calculation failed: {str(e)}")
            raise IndicatorCalculationError(f"Indicator calculation failed: {str(e)}")