"""
Data service for fetching market data using yfinance API.
Handles current and historical data fetching with caching and error handling.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path

from ..models.market_data import MarketData


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached data entry with expiration."""
    data: Dict
    timestamp: datetime
    expires_at: datetime


class DataCache:
    """Simple in-memory cache for market data."""
    
    def __init__(self, default_ttl_minutes: int = 5):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if not expired."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry.expires_at:
            del self._cache[key]
            return None
        
        return entry.data
    
    def set(self, key: str, data: Dict, ttl_minutes: Optional[int] = None) -> None:
        """Cache data with expiration."""
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self._default_ttl
        expires_at = datetime.now() + ttl
        
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            expires_at=expires_at
        )
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)


class DataService:
    """Service for fetching and managing market data."""
    
    def __init__(self, cache_ttl_minutes: int = 5, max_retries: int = 3):
        self.cache = DataCache(cache_ttl_minutes)
        self.max_retries = max_retries
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self) -> None:
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format."""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation - alphanumeric and common symbols
        symbol = symbol.strip().upper()
        if len(symbol) < 1 or len(symbol) > 10:
            return False
        
        # Allow letters, numbers, dots, and hyphens
        return all(c.isalnum() or c in '.-' for c in symbol)
    
    def _clean_market_data(self, df: pd.DataFrame, symbol: str) -> List[MarketData]:
        """Clean and validate market data from yfinance."""
        if df.empty:
            logger.warning(f"No data received for symbol {symbol}")
            return []
        
        cleaned_data = []
        
        for timestamp, row in df.iterrows():
            try:
                # Skip rows with NaN values
                if pd.isna(row['Open']) or pd.isna(row['Close']):
                    continue
                
                # Validate price data
                if any(val <= 0 for val in [row['Open'], row['High'], row['Low'], row['Close']]):
                    continue
                
                # Validate high/low relationships
                if row['High'] < max(row['Open'], row['Close']) or row['Low'] > min(row['Open'], row['Close']):
                    continue
                
                market_data = MarketData(
                    symbol=symbol.upper(),
                    timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if not pd.isna(row['Volume']) else 0
                )
                
                cleaned_data.append(market_data)
                
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error processing data point for {symbol}: {e}")
                continue
        
        return cleaned_data
    
    async def fetch_current_data(self, symbols: List[str], period: str = "1d", interval: str = "1m") -> Dict[str, List[MarketData]]:
        """
        Fetch current market data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            period: Data period (1d, 5d, 1mo, etc.)
            interval: Data interval (1m, 5m, 15m, 1h, etc.)
        
        Returns:
            Dictionary mapping symbols to their market data
        """
        if not symbols:
            return {}
        
        # Validate symbols
        valid_symbols = [s.upper() for s in symbols if self._validate_symbol(s)]
        if not valid_symbols:
            logger.error("No valid symbols provided")
            return {}
        
        # Check cache first
        cache_key = f"current_{'-'.join(valid_symbols)}_{period}_{interval}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {len(valid_symbols)} symbols")
            return {symbol: [MarketData.from_dict(d) for d in data] 
                   for symbol, data in cached_data.items()}
        
        result = {}
        
        # Fetch data for each symbol
        for symbol in valid_symbols:
            for attempt in range(self.max_retries):
                try:
                    self._rate_limit()
                    
                    logger.info(f"Fetching current data for {symbol} (attempt {attempt + 1})")
                    
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(period=period, interval=interval)
                    
                    if df.empty:
                        logger.warning(f"No data available for symbol {symbol}")
                        result[symbol] = []
                        break
                    
                    cleaned_data = self._clean_market_data(df, symbol)
                    result[symbol] = cleaned_data
                    
                    logger.info(f"Successfully fetched {len(cleaned_data)} data points for {symbol}")
                    break
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol} (attempt {attempt + 1}): {e}")
                    
                    if attempt == self.max_retries - 1:
                        logger.error(f"Failed to fetch data for {symbol} after {self.max_retries} attempts")
                        result[symbol] = []
                    else:
                        # Exponential backoff
                        await asyncio.sleep(2 ** attempt)
        
        # Cache the results
        cache_data = {symbol: [d.to_dict() for d in data] for symbol, data in result.items()}
        self.cache.set(cache_key, cache_data, ttl_minutes=5)
        
        return result
    
    async def fetch_higher_timeframe_data(self, symbols: List[str], timeframe: str = "15m", period: str = "1d") -> Dict[str, List[MarketData]]:
        """
        Fetch higher timeframe data for confirmation.
        
        Args:
            symbols: List of stock symbols
            timeframe: Higher timeframe interval (15m, 1h, etc.)
            period: Data period
        
        Returns:
            Dictionary mapping symbols to their higher timeframe data
        """
        logger.info(f"Fetching {timeframe} data for {len(symbols)} symbols")
        return await self.fetch_current_data(symbols, period=period, interval=timeframe)
    
    async def fetch_historical_data(self, symbols: List[str], start_date: date, end_date: date, interval: str = "1d") -> Dict[str, List[MarketData]]:
        """
        Fetch historical market data for backtesting.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval
        
        Returns:
            Dictionary mapping symbols to their historical data
        """
        if not symbols or start_date >= end_date:
            return {}
        
        valid_symbols = [s.upper() for s in symbols if self._validate_symbol(s)]
        if not valid_symbols:
            return {}
        
        # Check cache
        cache_key = f"historical_{'-'.join(valid_symbols)}_{start_date}_{end_date}_{interval}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached historical data for {len(valid_symbols)} symbols")
            return {symbol: [MarketData.from_dict(d) for d in data] 
                   for symbol, data in cached_data.items()}
        
        result = {}
        
        for symbol in valid_symbols:
            for attempt in range(self.max_retries):
                try:
                    self._rate_limit()
                    
                    logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
                    
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(start=start_date, end=end_date, interval=interval)
                    
                    if df.empty:
                        logger.warning(f"No historical data available for {symbol}")
                        result[symbol] = []
                        break
                    
                    cleaned_data = self._clean_market_data(df, symbol)
                    result[symbol] = cleaned_data
                    
                    logger.info(f"Successfully fetched {len(cleaned_data)} historical data points for {symbol}")
                    break
                    
                except Exception as e:
                    logger.error(f"Error fetching historical data for {symbol} (attempt {attempt + 1}): {e}")
                    
                    if attempt == self.max_retries - 1:
                        result[symbol] = []
                    else:
                        await asyncio.sleep(2 ** attempt)
        
        # Cache historical data for longer (30 minutes)
        cache_data = {symbol: [d.to_dict() for d in data] for symbol, data in result.items()}
        self.cache.set(cache_key, cache_data, ttl_minutes=30)
        
        return result
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "size": self.cache.size(),
            "entries": len(self.cache._cache)
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Data cache cleared")