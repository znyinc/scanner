"""
Data service for fetching market data using yfinance API with AlphaVantage fallback.
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

try:
    from alpha_vantage.timeseries import TimeSeries
    ALPHAVANTAGE_AVAILABLE = True
except ImportError:
    ALPHAVANTAGE_AVAILABLE = False
    TimeSeries = None

from ..models.market_data import MarketData
from ..config import get_settings


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
    """Service for fetching and managing market data with yfinance primary and AlphaVantage fallback."""
    
    def __init__(self, cache_ttl_minutes: int = 5, max_retries: int = 3):
        self.cache = DataCache(cache_ttl_minutes)
        self.max_retries = max_retries
        self._executor = ThreadPoolExecutor(max_workers=10)
        self.settings = get_settings()
        
        # Initialize AlphaVantage client if available
        self._alphavantage_client = None
        if ALPHAVANTAGE_AVAILABLE:
            try:
                self._alphavantage_client = TimeSeries(
                    key=self.settings.alphavantage_api_key,
                    output_format='pandas'
                )
                if self.settings.alphavantage_api_key == "demo":
                    logger.warning("AlphaVantage initialized with demo key - limited functionality")
                else:
                    logger.info("AlphaVantage client initialized successfully with API key")
            except Exception as e:
                logger.warning(f"Failed to initialize AlphaVantage client: {e}")
        else:
            logger.warning("AlphaVantage library not available - install with: pip install alpha-vantage")
        
        # Rate limiting (optimized for manual scans)
        self._last_request_time = 0
        self._min_request_interval = 0.3  # 300ms between requests (reasonable for manual use)
        self._last_alphavantage_request = 0
        self._alphavantage_min_interval = 6.0  # 6 seconds (still respects API limits but faster)
    
    def _rate_limit(self) -> None:
        """Implement minimal rate limiting for manual scans."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        # Minimal rate limiting for manual scans (not automated)
        min_interval = 0.3  # 300ms between requests (reduced from 1s)
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)  # Keep synchronous but minimal delay
        
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
    
    async def _rate_limit_alphavantage(self) -> None:
        """Implement rate limiting for AlphaVantage API (optimized for manual scans)."""
        current_time = time.time()
        time_since_last = current_time - self._last_alphavantage_request
        
        # Reduced rate limiting for manual scans
        min_interval = 6.0  # 6 seconds instead of 12 (still respects API limits)
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.info(f"AlphaVantage rate limiting: waiting {sleep_time:.1f}s")
            # Use async sleep to avoid blocking the server
            await asyncio.sleep(sleep_time)
        
        self._last_alphavantage_request = time.time()
    
    async def _fetch_alphavantage_intraday(self, symbol: str, interval: str = "60min") -> pd.DataFrame:
        """
        Fetch intraday data from AlphaVantage.
        
        Args:
            symbol: Stock symbol
            interval: Data interval (1min, 5min, 15min, 30min, 60min)
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self._alphavantage_client:
            raise ValueError("AlphaVantage client not available")
        
        await self._rate_limit_alphavantage()
        
        # Map our intervals to AlphaVantage intervals
        av_interval_map = {
            "1m": "1min",
            "5m": "5min", 
            "15m": "15min",
            "30m": "30min",
            "1h": "60min",
            "60min": "60min"
        }
        
        av_interval = av_interval_map.get(interval, "60min")
        
        try:
            logger.info(f"Fetching AlphaVantage intraday data for {symbol} with interval {av_interval}")
            data, meta_data = self._alphavantage_client.get_intraday(
                symbol=symbol,
                interval=av_interval,
                outputsize='compact'  # Last 100 data points
            )
            
            if data.empty:
                logger.warning(f"AlphaVantage returned empty data for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to match yfinance format
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data.index.name = 'Datetime'
            
            # Sort by timestamp (newest first, then reverse to match yfinance)
            data = data.sort_index()
            
            logger.info(f"AlphaVantage returned {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"AlphaVantage intraday fetch failed for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _fetch_alphavantage_daily(self, symbol: str) -> pd.DataFrame:
        """
        Fetch daily data from AlphaVantage.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self._alphavantage_client:
            raise ValueError("AlphaVantage client not available")
        
        await self._rate_limit_alphavantage()
        
        try:
            logger.info(f"Fetching AlphaVantage daily data for {symbol}")
            data, meta_data = self._alphavantage_client.get_daily(
                symbol=symbol,
                outputsize='compact'  # Last 100 data points
            )
            
            if data.empty:
                logger.warning(f"AlphaVantage returned empty daily data for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to match yfinance format
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data.index.name = 'Date'
            
            # Sort by timestamp
            data = data.sort_index()
            
            logger.info(f"AlphaVantage returned {len(data)} daily data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"AlphaVantage daily fetch failed for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _fetch_single_symbol_data(self, symbol: str, period: str = "5d", interval: str = "1h") -> pd.DataFrame:
        """
        Fetch data for a single symbol with optimized fallback for manual scans.
        
        Args:
            symbol: Stock symbol
            period: Data period for yfinance
            interval: Data interval
        
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching current data for {symbol} with fallback support")
        return await self._fetch_data_with_fallback(symbol, period, interval)
    
    async def _fetch_data_with_fallback(self, symbol: str, period: str = "5d", interval: str = "1h") -> pd.DataFrame:
        """
        Fetch data with yfinance first, fallback to AlphaVantage if yfinance fails.
        
        Args:
            symbol: Stock symbol
            period: Data period for yfinance
            interval: Data interval
        
        Returns:
            DataFrame with OHLCV data
        """
        # Try yfinance first (optimized for manual scans)
        yfinance_attempts = 0
        yfinance_max_attempts = 1  # Reduced from 3 to 1 for manual scans
        
        while yfinance_attempts < yfinance_max_attempts:
            try:
                self._rate_limit()
                yfinance_attempts += 1
                
                logger.info(f"Attempting yfinance fetch for {symbol} (attempt {yfinance_attempts}/{yfinance_max_attempts})")
                
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if not df.empty:
                    logger.info(f"yfinance success for {symbol}: {len(df)} data points")
                    return df
                else:
                    logger.warning(f"yfinance returned empty data for {symbol} (attempt {yfinance_attempts})")
                    
            except Exception as e:
                logger.warning(f"yfinance attempt {yfinance_attempts} failed for {symbol}: {e}")
                
                # No retries for manual scans - user can click "Start Scan" again
                # This eliminates blocking delays and makes the UI more responsive
        
        # For manual scans, skip AlphaVantage fallback to avoid long delays
        # Users can click "Start Scan" again if needed
        logger.warning(f"yfinance failed for {symbol}, skipping AlphaVantage fallback for faster manual scan")
        logger.info(f"Tip: Try again in a few minutes or check if {symbol} is a valid symbol")
        return pd.DataFrame()
    
    async def fetch_current_data(self, symbols: List[str], period: str = "1d", interval: str = "1h") -> Dict[str, List[MarketData]]:
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
        
        # Fetch data for symbols in parallel (optimized for manual scans)
        tasks = []
        for symbol in valid_symbols:
            task = asyncio.create_task(self._fetch_single_symbol_data(symbol, period, interval))
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                df = await task
                
                if df.empty:
                    logger.warning(f"No data available for symbol {symbol} from any source")
                    result[symbol] = []
                else:
                    cleaned_data = self._clean_market_data(df, symbol)
                    result[symbol] = cleaned_data
                    logger.info(f"Successfully fetched {len(cleaned_data)} data points for {symbol}")
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching data for {symbol}: {e}")
                result[symbol] = []
        
        # Cache the results
        cache_data = {symbol: [d.to_dict() for d in data] for symbol, data in result.items()}
        self.cache.set(cache_key, cache_data, ttl_minutes=5)
        
        return result
    
    async def fetch_higher_timeframe_data(self, symbols: List[str], timeframe: str = "4h", period: str = "1d") -> Dict[str, List[MarketData]]:
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
            # Single attempt for historical data (optimized for manual scans)
            try:
                self._rate_limit()
                
                logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
                
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval=interval)
                
                if df.empty:
                    logger.warning(f"No historical data available for {symbol}")
                    result[symbol] = []
                else:
                    cleaned_data = self._clean_market_data(df, symbol)
                    result[symbol] = cleaned_data
                    logger.info(f"Successfully fetched {len(cleaned_data)} historical data points for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {e}")
                result[symbol] = []
        
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