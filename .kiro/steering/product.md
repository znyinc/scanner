# Product Overview

Stock Scanner is a sophisticated stock analysis application that identifies trading opportunities using an EMA-ATR algorithm with higher timeframe confirmation.

## Core Features

- **Real-time Stock Scanning**: Analyzes multiple stocks using technical indicators (EMA, ATR, candlestick patterns)
- **Historical Backtesting**: Tests algorithm performance on historical data with comprehensive metrics
- **Algorithm Customization**: Configurable parameters for different market conditions
- **Web Interface**: Modern React frontend with responsive design

## Signal Generation Logic

**Long Signals** require ALL conditions:
- Bullish Polar Formation (close > open, close > EMA8, close > EMA21)
- EMA Positioning (EMA5 below ATR long line)
- Rising EMAs (EMA5, EMA8, EMA21 trending upward)
- FOMO Filter (price not overextended)
- Higher Timeframe Confirmation (HTF trend alignment)

**Short Signals** require ALL conditions:
- Bearish Polar Formation (close < open, close < EMA8, close < EMA21)
- EMA Positioning (EMA5 above ATR short line)
- Falling EMAs (EMA5, EMA8, EMA21 trending downward)
- FOMO Filter (price not overextended)
- Higher Timeframe Confirmation (HTF trend alignment)

## Key Technical Indicators

- Multiple EMAs: 5, 8, 13, 21, 50 period exponential moving averages
- ATR Filters: Average True Range for volatility-based filtering
- Polar Formation: Candlestick pattern recognition
- Higher Timeframe: 15-minute timeframe validation (now 4-hour for better reliability)
- FOMO and Volatility Filters: Risk management components