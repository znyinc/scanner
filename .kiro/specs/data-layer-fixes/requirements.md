# Requirements Document

## Introduction

This specification addresses critical data layer issues in the Stock Scanner application that are causing scan failures, "no data" errors, and unreliable signal generation. The root cause analysis has identified problems with Yahoo Finance fetch parameters, thin data windows, market hours gaps, and unhandled JSON errors that must be systematically resolved.

## Requirements

### Requirement 1: Robust Yahoo Finance Data Fetching

**User Story:** As a system administrator, I want reliable market data fetching that handles Yahoo Finance API limitations and errors, so that stock scans consistently return valid data.

#### Acceptance Criteria

1. WHEN fetching 1-minute data THEN the system SHALL use maximum 7-day periods with yfinance parameters: prepost=True, repair=True, threads=False
2. WHEN fetching 15-minute data THEN the system SHALL use maximum 60-day periods with same configuration parameters
3. WHEN processing data THEN the system SHALL require ≥100 bars for 1m and ≥50 bars for 15m before EMA/ATR calculations
4. WHEN Yahoo Finance returns JSON errors or empty frames THEN the system SHALL implement exponential backoff retry logic
5. WHEN data fetching fails after retries THEN the system SHALL mark symbols with specific status: OK|EMPTY|STALE|INSUFFICIENT_BARS|API_ERROR
6. WHEN processing OHLC data THEN the system SHALL drop NaN/zero values and enforce high >= max(open,close), low <= min(open,close)
7. IF ticker validation fails THEN the system SHALL check yf.Ticker(sym).fast_info before processing and drop invalid tickers

### Requirement 2: Market Hours and Time Zone Handling

**User Story:** As a trader, I want the system to respect market hours and time zones, so that I don't get false "no data" errors when markets are closed.

#### Acceptance Criteria

1. WHEN current time is outside regular or extended trading hours AND last bar is stale (≥2min for 1m, ≥20min for 15m) THEN the system SHALL mark as STALE_DATA
2. WHEN processing multi-timezone data THEN the system SHALL align all timestamps to exchange timezone (America/New_York for NASDAQ/NYSE)
3. WHEN joining 1-minute and 15-minute data THEN the system SHALL reject mixed timezone data and ensure consistent timezone handling
4. WHEN handling holidays or missing sessions THEN the system SHALL skip cleanly without errors
5. IF market is closed THEN the system SHALL provide clear messaging about market status and use last available close data

### Requirement 3: Data Quality and Validation

**User Story:** As an algorithm developer, I want clean, validated market data with sufficient history, so that technical indicators calculate correctly and signals are reliable.

#### Acceptance Criteria

1. WHEN processing market data THEN the system SHALL require minimum bars for EMA50 and ATR(14) calculations (≥64 bars with 50-bar warmup)
2. WHEN data contains invalid values THEN the system SHALL drop rows with NaN or zero OHLC values
3. WHEN validating OHLC data THEN the system SHALL enforce high >= max(open, close) and low <= min(open, close)
4. IF insufficient data exists THEN the system SHALL refetch with longer periods or mark symbol as insufficient data
5. WHEN last bar timestamp is stale THEN the system SHALL reject data older than 2 minutes for 1m or 20 minutes for 15m

### Requirement 4: Higher Timeframe Data Consistency

**User Story:** As a technical analyst, I want consistent higher timeframe data that aligns properly with intraday data, so that HTF confirmation signals are accurate.

#### Acceptance Criteria

1. WHEN generating 15-minute data THEN the system SHALL prefer resampling 1-minute data using resample("15T", label="right", closed="right")
2. WHEN resampling data THEN the system SHALL use OHLCV aggregation: Open=first, High=max, Low=min, Close=last, Volume=sum
3. IF separate 15-minute fetches are used THEN the system SHALL align timestamps by right-edge for consistency
4. WHEN combining timeframes THEN the system SHALL ensure no timestamp misalignment issues
5. WHEN corporate actions occur THEN the system SHALL handle via auto_adjust=True and note survivorship bias for current-only symbol lists

### Requirement 5: Enhanced Technical Indicator Calculations

**User Story:** As a trader, I want accurate EMA rising/falling detection and ATR-based filters, so that signal generation reflects true market conditions.

#### Acceptance Criteria

1. WHEN calculating EMA rising/falling condition THEN the system SHALL use slope over 3-bar lookback: EMA_t / EMA_{t-3} - 1 ≥ threshold
2. WHEN applying FOMO filter THEN the system SHALL reject signals where close > ema8 * (1 + fomo_mult * ATR/close)
3. WHEN applying volatility filter THEN the system SHALL reject signals where bar range > volatility_filter * ATR
4. WHEN calculating ATR lines THEN the system SHALL use atr_long = ema21 + atr_mult * ATR(14) and atr_short = ema21 - atr_mult * ATR(14)
5. WHEN using walk-forward or train/test split THEN the system SHALL forbid look-ahead bias and use burn-in bars before first signal
6. IF technical indicators cannot be calculated THEN the system SHALL provide specific failure reasons per symbol with diagnostic output

### Requirement 6: Comprehensive Error Handling and Logging

**User Story:** As a system operator, I want detailed error reporting and graceful failure handling, so that I can diagnose issues and maintain system reliability.

#### Acceptance Criteria

1. WHEN data fetching fails THEN the system SHALL distinguish between "no data available" vs "criteria not met"
2. WHEN symbols fail processing THEN the system SHALL log specific failure reasons per symbol
3. WHEN Yahoo Finance errors occur THEN the system SHALL implement circuit breaker for repeatedly failing symbols
4. IF all symbols fail THEN the system SHALL provide actionable error messages with recovery suggestions
5. WHEN processing completes THEN the system SHALL provide summary statistics of successful vs failed symbols

### Requirement 7: Enhanced Backtesting with Realistic Constraints

**User Story:** As a trader, I want realistic backtesting that includes fees, slippage, and proper data handling, so that backtest results reflect actual trading conditions.

#### Acceptance Criteria

1. WHEN running backtests THEN the system SHALL include default fees ($0.005/share) and slippage (2 basis points)
2. WHEN processing historical data THEN the system SHALL use walk-forward or train/test split methodology
3. WHEN calculating performance metrics THEN the system SHALL include max drawdown, Sharpe ratio, profit factor, and exposure time
4. WHEN backtests complete THEN the system SHALL export trades to CSV format for analysis
5. WHEN handling corporate actions THEN the system SHALL use auto_adjust=True and document survivorship bias

### Requirement 8: Historical Data Management and Persistence

**User Story:** As a system operator, I want efficient historical data storage with proper indexing and retention policies, so that system performance remains optimal over time.

#### Acceptance Criteria

1. WHEN storing scan results THEN the system SHALL persist per-symbol diagnostics and dataset hashes (interval, period, timezone, provider)
2. WHEN querying historical data THEN the system SHALL use indexes on timestamp and symbol columns
3. WHEN implementing pagination THEN the system SHALL use cursor-based pagination for large result sets
4. WHEN managing data retention THEN the system SHALL implement configurable retention policies and automated purge jobs
5. WHEN storing metadata THEN the system SHALL include data quality metrics and processing timestamps

### Requirement 9: User Interface and Service Level Objectives

**User Story:** As a trader, I want fast, responsive scans with clear feedback about failures, so that I can quickly identify and resolve issues.

#### Acceptance Criteria

1. WHEN scanning 50 tickers THEN the system SHALL complete within 8 seconds (SLO)
2. WHEN running backtests THEN the system SHALL complete 1 symbol/month of 1m data within 60 seconds (SLO)
3. WHEN symbols fail processing THEN the system SHALL show per-symbol badges with specific failure reasons
4. WHEN failures occur THEN the system SHALL provide retry buttons for individual symbols
5. WHEN displaying results THEN the system SHALL include processing time and data quality indicators

### Requirement 10: Enhanced Settings and Configuration Management

**User Story:** As a trader, I want configurable algorithm parameters with validation and presets, so that I can optimize the strategy for different market conditions.

#### Acceptance Criteria

1. WHEN configuring ATR multiplier THEN the system SHALL validate range 0.5-10.0
2. WHEN setting volatility filter THEN the system SHALL validate range 0.5-5.0
3. WHEN configuring EMA slope thresholds THEN the system SHALL validate range 0.0-0.05 for EMA5/8/21
4. WHEN selecting higher timeframe THEN the system SHALL allow {5m, 15m, 30m, 1h} options
5. WHEN choosing presets THEN the system SHALL provide Conservative, Balanced, and Aggressive configurations
6. WHEN configuring market data THEN the system SHALL provide pre/post-market toggle options

### Requirement 11: Performance and Reliability Enhancements

**User Story:** As a system user, I want fast, reliable scans that handle large symbol lists efficiently, so that I can analyze multiple stocks without timeouts or failures.

#### Acceptance Criteria

1. WHEN fetching data THEN the system SHALL implement 30-60 second TTL caching with jittered backoff for rate limiting
2. WHEN Yahoo Finance is unavailable THEN the system SHALL provide fallback to secondary data providers
3. WHEN processing large symbol lists THEN the system SHALL implement batch processing with progress reporting
4. WHEN monitoring system health THEN the system SHALL implement structured logging with error taxonomy and Prometheus metrics
5. WHEN symbols repeatedly fail THEN the system SHALL implement temporary blacklisting with automatic retry windows

## Non-Functional Requirements

### Performance Requirements
- **Data Caching**: Implement 30-60 second TTL for market data with Redis or in-memory cache
- **Rate Limiting**: Handle Yahoo Finance rate limits with jittered exponential backoff
- **Batch Processing**: Process large symbol lists in configurable batch sizes (default: 20 symbols)

### Reliability Requirements
- **Error Taxonomy**: Structured error classification for monitoring and alerting
- **Circuit Breaker**: Temporary blacklisting for symbols with >3 consecutive failures in 5-minute window
- **Graceful Degradation**: Continue processing remaining symbols when individual symbols fail

### Monitoring Requirements
- **Structured Logging**: JSON-formatted logs with correlation IDs and performance metrics
- **Metrics Collection**: Prometheus metrics for success rates, response times, and error counts
- **Health Checks**: Endpoint monitoring for data provider availability and system health