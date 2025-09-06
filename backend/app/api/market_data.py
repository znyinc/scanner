"""
Market Data API endpoints for basic stock information.
"""
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional
import yfinance as yf
from datetime import datetime, timedelta
import logging
import time
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

# Simple rate limiting tracker
request_tracker = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # Max requests per window
RATE_LIMIT_WINDOW = 300   # 5 minutes in seconds

router = APIRouter(prefix="/market-data", tags=["market-data"])

# Mock data for testing when APIs are rate limited
MOCK_DATA = {
    "AAPL": {"price": 175.50, "change": 2.30, "volume": 45000000, "exchange": "NASDAQ"},
    "GOOGL": {"price": 135.20, "change": -1.80, "volume": 25000000, "exchange": "NASDAQ"},
    "MSFT": {"price": 420.15, "change": 5.60, "volume": 30000000, "exchange": "NASDAQ"},
    "TSLA": {"price": 250.80, "change": -8.20, "volume": 55000000, "exchange": "NASDAQ"},
    "AMZN": {"price": 145.90, "change": 3.40, "volume": 35000000, "exchange": "NASDAQ"},
}


class MarketDataResponse(BaseModel):
    """Response model for market data."""
    symbol: str
    lastPrice: float
    priceChange: float
    priceChangePercent: float
    volume: int
    exchange: str
    timestamp: datetime


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit."""
    now = time.time()
    client_requests = request_tracker[client_ip]
    
    # Remove old requests outside the window
    client_requests[:] = [req_time for req_time in client_requests if now - req_time < RATE_LIMIT_WINDOW]
    
    # Check if under limit
    if len(client_requests) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    client_requests.append(now)
    return True


@router.get("/test", response_model=dict)
async def test_market_data():
    """
    Test endpoint that returns mock data without hitting external APIs.
    Use this to verify the market data table works without rate limits.
    """
    return {
        "message": "Market data API is working",
        "mock_symbols": list(MOCK_DATA.keys()),
        "rate_limit": f"{RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW//60} minutes",
        "status": "ready"
    }


@router.get("/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str = Path(..., description="Stock symbol to get data for", regex="^[A-Z]{1,5}$")
):
    """
    Get basic market data for a stock symbol.
    
    - **symbol**: Stock symbol (e.g., AAPL, MSFT)
    
    Returns current market data including price, change, volume, and exchange.
    
    **Rate Limited**: Max 10 requests per 5 minutes to prevent API abuse.
    """
    try:
        # Simple rate limiting (in production, use Redis or proper rate limiter)
        client_ip = "default"  # In production, get real client IP
        if not check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait before making more requests. "
                       f"Limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW//60} minutes."
            )
        
        # Clean and validate symbol
        symbol = symbol.upper().strip()
        
        logger.info(f"Fetching market data for {symbol}")
        
        # Add delay to be respectful to Yahoo Finance
        await asyncio.sleep(1)  # 1 second delay between requests
        
        try:
            # Try real data first
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) < 1:
                raise ValueError("No data available")
            
            # Get the most recent data
            latest = hist.iloc[-1]
            current_price = float(latest['Close'])
            
            # Calculate price change
            if len(hist) >= 2:
                previous_close = float(hist.iloc[-2]['Close'])
                price_change = current_price - previous_close
                price_change_percent = (price_change / previous_close) * 100
            else:
                price_change = current_price - float(latest['Open'])
                price_change_percent = (price_change / float(latest['Open'])) * 100
            
            volume = int(latest['Volume']) if latest['Volume'] else 0
            
            # Get exchange info
            exchange = info.get('exchange', 'Unknown')
            if not exchange or exchange == 'NMS':
                exchange = 'NASDAQ'
            elif exchange == 'NYQ':
                exchange = 'NYSE'
            
            logger.info(f"Successfully fetched real data for {symbol}")
            
        except Exception as yf_error:
            # If Yahoo Finance fails, use mock data for testing
            if symbol in MOCK_DATA:
                logger.warning(f"Yahoo Finance failed for {symbol}, using mock data: {str(yf_error)}")
                mock = MOCK_DATA[symbol]
                current_price = mock["price"]
                price_change = mock["change"]
                price_change_percent = (price_change / current_price) * 100
                volume = mock["volume"]
                exchange = mock["exchange"]
            else:
                # Re-raise the original error if no mock data available
                raise yf_error
        
        return MarketDataResponse(
            symbol=symbol,
            lastPrice=current_price,
            priceChange=price_change,
            priceChangePercent=price_change_percent,
            volume=volume,
            exchange=exchange,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching market data for {symbol}: {error_msg}")
        
        # Check if it's a rate limit error
        if "429" in error_msg or "Too Many Requests" in error_msg:
            raise HTTPException(
                status_code=429,
                detail=f"Yahoo Finance rate limit exceeded for {symbol}. "
                       "Please wait 1-2 hours before trying again, or try fewer symbols."
            )
        elif "404" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found or delisted."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch market data for {symbol}. "
                       "This might be due to API rate limits or network issues."
            )