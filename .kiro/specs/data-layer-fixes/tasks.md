# Implementation Plan

- [ ] 1. Implement Enhanced DataService with Yahoo Finance constraints
  - Create EnhancedDataService class with proper yfinance parameter handling (prepost=True, repair=True, threads=False, auto_adjust=True)
  - Implement period validation: 1m ≤ 7d, 15m ≤ 60d with YahooConstraints class
  - Add ticker validation using yf.Ticker(sym).fast_info before data fetching
  - Implement data sufficiency checks: require ≥100 bars for 1m, ≥50 bars for 15m
  - Add OHLC data cleansing: drop NaN/zero values, enforce high >= max(open,close), low <= min(open,close)
  - Write unit tests for all data fetching scenarios and edge cases
  - _Requirements: 1.1, 1.2, 1.3, 1.7_

- [ ] 2. Build robust retry and error handling system
  - Implement RetryManager with exponential backoff and jittered delays (1s, 2.5s, 6.25s)
  - Add JSONDecodeError handling specific to yfinance API failures
  - Create ErrorTaxonomy class with Yahoo-specific error codes (PERIOD_LIMIT_EXCEEDED, JSON_DECODE_ERROR)
  - Implement circuit breaker: blacklist symbols after 3 failures in 5-minute window
  - Add per-symbol status tracking: OK|EMPTY|STALE|INSUFFICIENT_BARS|API_ERROR|CIRCUIT_BREAKER
  - Write unit tests for retry logic, circuit breaker, and error classification
  - _Requirements: 1.4, 1.5, 6.1, 6.2, 6.3_

- [ ] 3. Implement MarketHoursManager and timezone handling
  - Create MarketHoursManager class with is_market_open() and get_last_trading_session() methods
  - Add timezone alignment to America/New_York for NASDAQ/NYSE symbols
  - Implement staleness detection: reject data older than 2min for 1m, 20min for 15m
  - Add trading calendar integration for holiday handling
  - Create market status validation and clear messaging for closed markets
  - Write unit tests for market hours logic across different timezones and holidays
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Build DataQualityValidator with comprehensive validation
  - Implement DataQualityValidator class with validate_ohlc_integrity() and remove_invalid_bars() methods
  - Add data gap detection for missing bars in time series
  - Create volume validation: non-negative, reasonable volume checks (< 10x average)
  - Implement minimum bar count validation with specific error messaging
  - Add data quality scoring system (0.0-1.0) based on completeness and integrity
  - Write unit tests for all validation rules and edge cases
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 5. Enhance technical indicators with slope-based trend detection
  - Update EnhancedIndicatorEngine with calculate_ema_with_validation() and calculate_atr_with_validation() methods
  - Implement slope-based EMA trend detection: (EMA_t / EMA_{t-3}) - 1 >= threshold over 3-bar lookback
  - Create enhanced FOMO filter: reject if close > ema8 * (1 + fomo_mult * ATR/close)
  - Add volatility filter: reject if bar range > volatility_filter * ATR
  - Implement ATR line calculations: atr_long = ema21 + k*ATR(14), atr_short = ema21 - k*ATR(14)
  - Write unit tests for all indicator calculations with known datasets
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

- [ ] 6. Implement higher timeframe data consistency
  - Create resample_to_higher_timeframe() method using resample("15T", label="right", closed="right")
  - Implement OHLCV aggregation: Open=first, High=max, Low=min, Close=last, Volume=sum
  - Add right-edge timestamp alignment for HTF data consistency
  - Handle corporate actions via auto_adjust=True with survivorship bias documentation
  - Prefer 1m→15m resampling over separate Yahoo fetches for alignment
  - Write integration tests for HTF data consistency and timestamp alignment
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 7. Build caching layer with TTL and rate limiting
  - Implement DataCache class with 30-60 second TTL for market data
  - Add cache key generation: {tickers_hash}_{interval}_{period}_{date}
  - Implement LRU eviction for memory management
  - Add jittered backoff for rate limiting to prevent thundering herd
  - Create cache warming for frequently requested symbols
  - Write unit tests for cache hit/miss scenarios and TTL expiration
  - _Requirements: 11.1, 11.3, 11.4_

- [ ] 8. Update PostgreSQL schema with enhanced indexing
  - Add symbol indexing to scan_results table: CREATE INDEX idx_scan_results_symbol ON scan_results(symbol)
  - Create symbol_status table for tracking per-symbol failure states and blacklisting
  - Add scan_performance table for monitoring success rates and timing metrics
  - Implement cursor-based pagination for large result sets
  - Add data retention policies and automated purge jobs configuration
  - Write database migration scripts and test data integrity
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 9. Enhance signal generation with comprehensive diagnostics
  - Update EnhancedSignal model with status field to distinguish "no signal" from "no data"
  - Add timezone field to all market data models for exchange consistency
  - Implement per-symbol failure reason logging with specific diagnostic messages
  - Add data quality scoring to signal output (0.0-1.0 based on data completeness)
  - Create processing time tracking and performance metrics per symbol
  - Write unit tests for signal generation with various market scenarios and failure modes
  - _Requirements: 5.6, 6.4, 6.5_

- [ ] 10. Implement enhanced backtesting with realistic constraints
  - Add default fees ($0.005/share) and slippage (2 basis points) to backtest calculations
  - Implement walk-forward methodology with burn-in bars before first signal
  - Add comprehensive performance metrics: max drawdown, Sharpe ratio, profit factor, exposure time
  - Create CSV export functionality for trade analysis
  - Handle corporate actions and document survivorship bias for current-only symbol lists
  - Write integration tests for complete backtesting workflow with realistic constraints
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 11. Build enhanced settings management with validation
  - Implement parameter validation: ATR multiplier 0.5-10, volatility filter 0.5-5, EMA thresholds 0-0.05
  - Add higher timeframe options: {5m, 15m, 30m, 1h} with validation
  - Create preset configurations: Conservative, Balanced, Aggressive parameter sets
  - Add pre/post-market toggle options for data fetching
  - Implement settings persistence with PostgreSQL backend
  - Write unit tests for all parameter validation and preset configurations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 12. Implement comprehensive monitoring and logging
  - Add structured JSON logging with correlation IDs and performance metrics
  - Implement Prometheus metrics for success rates, response times, and error counts
  - Create health check endpoints for data provider availability
  - Add error taxonomy tracking and alerting for system monitoring
  - Implement performance SLO monitoring: ≤8s for 50 tickers, ≤60s for 1 symbol/month backtest
  - Write monitoring integration tests and alerting validation
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 11.4, 11.5_

- [ ] 13. Implement data layer hardening with Yahoo Finance constraints
  - Normalize timezone per exchange and reject mixed timezone data in joins
  - Enforce strict fetch limits: 1m≤7d, 15m≤60d with prepost=True, repair=True, threads=False
  - Implement 1m→15m resampling with right-edge alignment, fallback to native 15m if 1m insufficient
  - Add min-bars gate: ≥100 bars (1m), ≥50 bars (15m) with INSUFFICIENT_BARS classification
  - Implement retries with jitter on JSONDecodeError and empty frames with per-symbol status codes
  - Write unit tests for all Yahoo Finance constraint validations and edge cases
  - _Requirements: 1.1, 1.2, 1.3, 2.2, 2.3, 4.1, 4.2_

- [ ] 14. Build Redis caching and rate limiting system
  - Implement Redis cache with TTL 30-60s for recent candles and calculated EMA/ATR values
  - Add session reuse for yfinance to reduce connection handshakes and improve performance
  - Create circuit breaker for repeatedly failing tickers with exponential backoff
  - Implement jittered delays to prevent thundering herd problems
  - Add cache warming strategies for frequently requested symbols
  - Write integration tests for cache performance and circuit breaker functionality
  - _Requirements: 11.1, 11.4, 11.5_

- [ ] 15. Enhance algorithm with precise filter definitions
  - Implement slope-based rising/falling test: (EMA_t / EMA_{t-3}) - 1 ≥ thresholds
  - Define FOMO filter precisely: reject if close > ema8 * (1 + fomo_mult * ATR/close)
  - Define volatility filter: reject if bar_range > volatility_filter * ATR
  - Add stale-bar guard: last 1m ≤2min old, last 15m ≤20min old, else STALE_DATA
  - Create comprehensive unit tests for all filter edge cases and boundary conditions
  - Write algorithm validation tests with known market scenarios
  - _Requirements: 5.1, 5.2, 5.3, 3.5_

- [ ] 16. Build enhanced API with per-symbol diagnostics
  - Add per-symbol diagnostics in scan response with specific failure reasons
  - Implement preset parameter profiles: Conservative, Balanced, Aggressive configurations
  - Create CSV/JSON export functionality for scans, trades, and performance metrics
  - Add detailed error messaging with recovery suggestions for each failure type
  - Implement batch processing status reporting with progress indicators
  - Write API integration tests for all diagnostic and export functionality
  - _Requirements: 6.4, 6.5, 10.5, 7.4_

- [ ] 17. Implement advanced PostgreSQL schema with indexing
  - Add symbol GIN/GiST index for scan_results.symbols_scanned array field
  - Store dataset_fingerprint (interval, period, timezone, provider, start/end timestamps)
  - Create Alembic migration scripts for schema updates and data migrations
  - Add seed scripts with demo tickers and default settings configurations
  - Implement data retention policies with automated cleanup jobs
  - Write database performance tests and index optimization validation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 18. Build comprehensive observability and monitoring
  - Implement structured JSON logging with error taxonomy and correlation IDs
  - Add Prometheus metrics: fetch latency, empty-frame rate, signals per 1000 bars
  - Create health check endpoints: /healthz (dependencies), /readyz (database + cache)
  - Implement alerting for SLO violations and system degradation
  - Add performance dashboards with real-time metrics visualization
  - Write monitoring integration tests and alerting validation
  - _Requirements: 9.2, 9.3, 9.4, 11.4, 11.5_

- [ ] 19. Implement performance optimization and SLO validation
  - Validate SLO compliance: ≤8s for 50 tickers scan, ≤60s for 1-symbol 1m/month backtest
  - Create load tests with 200-500 tickers recording p95 latency and error rates
  - Implement connection pooling and async processing for improved throughput
  - Add memory usage monitoring and optimization for large dataset processing
  - Create performance regression testing in CI/CD pipeline
  - Write comprehensive performance benchmarking and optimization documentation
  - _Requirements: 9.1, 9.5, 11.3_

- [ ] 20. Build security and operational infrastructure
  - Implement secrets management via environment variables with Pydantic Settings validation
  - Add role-based access control for settings changes and administrative functions
  - Create data retention policy with PIPEDA/GDPR compliance notes for stored history
  - Implement Docker containerization with multi-stage builds for production deployment
  - Add CI/CD pipeline with linting, testing, security scanning, and automated deployment
  - Write security audit documentation and operational runbooks
  - _Requirements: Non-functional security and compliance requirements_

- [ ] 21. Implement scheduled scanning and automation
  - Create cron worker for scheduled scans with idempotent run keys
  - Implement automated history pruning based on retention policies
  - Add scan scheduling interface with configurable intervals and symbol lists
  - Create automated alerting for scan failures and system health issues
  - Implement graceful shutdown and restart capabilities for maintenance
  - Write automation testing and scheduling validation
  - _Requirements: 11.2, 8.4, 8.5_

- [ ] 22. Create comprehensive test suite with SLO validation
  - Write unit tests for insufficient bars and stale data scenarios
  - Add integration tests with full scan/backtest on AAPL, MSFT, TSLA ticker set
  - Implement performance tests to validate SLOs: scan ≤8s for 50 tickers, backtest ≤60s for 1 symbol/month
  - Create reliability tests for JSONDecodeError retry logic and Yahoo Finance outages
  - Add end-to-end workflow tests with real market data validation
  - Write load testing for concurrent requests and memory usage monitoring
  - _Requirements: All requirements validation and SLO compliance_