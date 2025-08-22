# Requirements Document

## Introduction

This feature implements a web-based stock scanner that uses a sophisticated EMA-based trading algorithm with ATR filters and higher timeframe confirmation to identify long and short trading opportunities. The algorithm uses multiple EMAs (5, 8, 13, 21, 50), ATR-based volatility filters, and 15-minute higher timeframe analysis for trade validation. The system will integrate with yfinance API to fetch real-time and historical stock data, provide backtesting capabilities using historical data, and maintain a comprehensive history of all scanning runs and their outcomes for analysis and performance tracking.

## Requirements

### Requirement 1

**User Story:** As a trader, I want to scan stocks using the EMA-ATR algorithm, so that I can identify potential long and short trading opportunities in real-time.

#### Acceptance Criteria

1. WHEN the user initiates a stock scan THEN the system SHALL fetch current 1-minute and 15-minute timeframe data using yfinance API
2. WHEN market data is retrieved THEN the system SHALL calculate EMAs (5, 8, 13, 21, 50) and ATR(14) for each stock on both timeframes
3. WHEN evaluating long conditions THEN the system SHALL check: bullish polar formation (close > open, close > ema8, close > ema21), EMA5 below ATR long line, rising EMAs, no FOMO flag, and higher timeframe confirmation (HTF EMA5 > HTF EMA8, close > HTF close/open)
4. WHEN evaluating short conditions THEN the system SHALL check: bearish polar formation (close < open, close < ema8, close < ema21), EMA5 above ATR short line, falling EMAs, no FOMO flag, and higher timeframe confirmation (HTF EMA5 < HTF EMA8, close < HTF close/open)
5. WHEN qualifying stocks are found THEN the system SHALL display results with stock symbols, signal type (long/short), current price, EMA values, and ATR levels
6. WHEN no stocks meet the criteria THEN the system SHALL display a message indicating no matches found
7. IF the API is unavailable THEN the system SHALL display an appropriate error message and retry mechanism

### Requirement 2

**User Story:** As a trader, I want to run backtests using historical data, so that I can validate the algorithm's performance before using it for live trading.

#### Acceptance Criteria

1. WHEN the user selects a date range for backtesting THEN the system SHALL fetch historical data for the specified period
2. WHEN historical data is available THEN the system SHALL apply the algorithm to each trading day in the selected range
3. WHEN the backtest completes THEN the system SHALL calculate and display performance metrics including win rate, average return, and total return
4. WHEN displaying backtest results THEN the system SHALL show individual trade signals with entry/exit points and outcomes
5. IF insufficient historical data exists THEN the system SHALL notify the user and suggest alternative date ranges

### Requirement 3

**User Story:** As a trader, I want to maintain a history of all scanning runs and backtests, so that I can track performance over time and analyze patterns.

#### Acceptance Criteria

1. WHEN any scan or backtest is executed THEN the system SHALL automatically save the run details to the history
2. WHEN saving run history THEN the system SHALL record timestamp, scan type, parameters used, and results obtained
3. WHEN the user accesses the history THEN the system SHALL display all previous runs in chronological order with filtering options
4. WHEN viewing historical runs THEN the system SHALL allow users to view detailed results of any previous scan or backtest
5. WHEN the history becomes large THEN the system SHALL provide pagination and search functionality

### Requirement 4

**User Story:** As a trader, I want a responsive web interface, so that I can access the stock scanner from any device.

#### Acceptance Criteria

1. WHEN the user accesses the application THEN the system SHALL display a clean, intuitive web interface
2. WHEN the user interacts with controls THEN the system SHALL provide immediate visual feedback
3. WHEN the system is processing requests THEN the system SHALL display loading indicators
4. WHEN viewing on mobile devices THEN the system SHALL adapt the layout for optimal mobile experience
5. IF the user's session expires THEN the system SHALL handle authentication gracefully

### Requirement 5

**User Story:** As a trader, I want to configure scan parameters, so that I can customize the algorithm behavior for different market conditions.

#### Acceptance Criteria

1. WHEN the user accesses scan settings THEN the system SHALL display configurable parameters: ATR multiplier (default 2), EMA rising thresholds (0.02, 0.01, 0.005), ATR volatility filter (1.5x), FOMO filter (1.0x), and higher timeframe period (default 15min)
2. WHEN parameters are modified THEN the system SHALL validate inputs and provide feedback on acceptable ranges
3. WHEN invalid parameters are entered THEN the system SHALL prevent execution and display clear error messages
4. WHEN valid parameters are set THEN the system SHALL save these settings for future scans
5. WHEN the user resets parameters THEN the system SHALL restore default algorithm values