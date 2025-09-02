# Design Document

## Overview

This design addresses critical data layer issues in the Stock Scanner application by implementing robust Yahoo Finance data fetching, proper market hours handling, enhanced data validation, and reliable technical indicator calculations. The solution focuses on eliminating "no data" errors, JSON decode failures, and unreliable signal generation through systematic improvements to the data pipeline.

## Architecture

### High-Level Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Symbol Input  │───►│   Cache Layer   │───►│  Data Fetcher   │───►│  Data Validator │
│                 │    │                 │    │                 │    │                 │
│ - Ticker List   │    │ - Redis/Memory  │    │ - Yahoo Finance │    │ - OHLC Checks   │
│ - Validation    │    │ - TTL: 30-60s   │    │ - Retry Logic   │    │ - Bar Count     │
│ - Market Hours  │    │ - Rate Limiting │    │ - Circuit Break │    │ - Timezone      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │                        │
                              ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │ Indicator Engine│───►│ Result Compiler │───►│   PostgreSQL    │
                       │                 │    │                 │    │    Database     │
                       │ - EMA/ATR Calc  │    │ - Signal Output │    │ - Scan Results  │
                       │ - Signal Logic  │    │ - Error Summary │    │ - Symbol Status │
                       │ - HTF Confirm   │    │ - Diagnostics   │    │ - Indexed Data  │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Enhanced DataService

**Purpose**: Robust market data fetching with proper error handling and validation

**Key Methods**:
```python
class EnhancedDataService:
    def fetch_intraday_data(self, tickers: List[str], interval: str, period: str) -> DataFetchResult
    def validate_tickers(self, tickers: List[str]) -> TickerValidationResult
    def check_market_hours(self, exchange: str = "NYSE") -> MarketStatus
    def resample_to_higher_timeframe(self, df: pd.DataFrame, target_interval: str) -> pd.DataFrame
    def apply_data_quality_checks(self, df: pd.DataFrame) -> DataQualityResult
```

**Configuration**:
```python
@dataclass
class DataFetchConfig:
    # Yahoo Finance parameters
    prepost: bool = True
    repair: bool = True  
    threads: bool = False
    auto_adjust: bool = True
    
    # Data requirements
    min_bars_1m: int = 100
    min_bars_15m: int = 50
    warmup_bars: int = 50
    
    # Retry configuration
    max_retries: int = 3
    backoff_factor: float = 1.5
    retry_delay: float = 1.0
    
    # Staleness thresholds
    stale_threshold_1m: int = 2  # minutes
    stale_threshold_15m: int = 20  # minutes
```

### 2. Market Hours Manager

**Purpose**: Handle market hours, timezone alignment, and trading session validation

**Key Methods**:
```python
class MarketHoursManager:
    def is_market_open(self, exchange: str = "NYSE") -> bool
    def get_last_trading_session(self, exchange: str = "NYSE") -> datetime
    def align_timezone(self, df: pd.DataFrame, target_tz: str = "America/New_York") -> pd.DataFrame
    def validate_data_freshness(self, last_timestamp: datetime, interval: str) -> bool
    def get_trading_calendar(self, start_date: date, end_date: date) -> List[date]
```

### 3. Data Quality Validator

**Purpose**: Comprehensive data validation and cleaning

**Key Methods**:
```python
class DataQualityValidator:
    def validate_ohlc_integrity(self, df: pd.DataFrame) -> ValidationResult
    def remove_invalid_bars(self, df: pd.DataFrame) -> pd.DataFrame
    def check_sufficient_data(self, df: pd.DataFrame, min_bars: int) -> bool
    def detect_data_gaps(self, df: pd.DataFrame, interval: str) -> List[Gap]
    def validate_volume_data(self, df: pd.DataFrame) -> ValidationResult
```

**Validation Rules**:
```python
@dataclass
class OHLCValidationRules:
    # Price sanity checks
    high_ge_open_close: bool = True  # high >= max(open, close)
    low_le_open_close: bool = True   # low <= min(open, close)
    positive_prices: bool = True     # all prices > 0
    no_nan_values: bool = True       # no NaN in OHLC
    
    # Volume checks
    non_negative_volume: bool = True
    reasonable_volume: bool = True   # volume < 10x average
```

### 4. Enhanced Technical Indicators Engine

**Purpose**: Accurate technical indicator calculations with proper error handling

**Key Methods**:
```python
class EnhancedIndicatorEngine:
    def calculate_ema_with_validation(self, prices: pd.Series, period: int) -> IndicatorResult
    def calculate_atr_with_validation(self, df: pd.DataFrame, period: int = 14) -> IndicatorResult
    def detect_ema_trend(self, ema: pd.Series, lookback: int = 3, threshold: float = 0.01) -> TrendResult
    def calculate_atr_lines(self, ema21: pd.Series, atr: pd.Series, multiplier: float = 2.0) -> ATRLines
    def apply_fomo_filter(self, close: pd.Series, ema8: pd.Series, atr: pd.Series, multiplier: float = 1.0) -> pd.Series
```

**Enhanced EMA Trend Detection**:
```python
def detect_ema_trend(self, ema: pd.Series, lookback: int = 3, threshold: float = 0.01) -> TrendResult:
    """
    Detect EMA trend using slope over lookback period
    Formula: (EMA_t / EMA_{t-lookback}) - 1 >= threshold
    """
    if len(ema) < lookback + 1:
        return TrendResult(trend="insufficient_data", confidence=0.0)
    
    current_ema = ema.iloc[-1]
    past_ema = ema.iloc[-(lookback + 1)]
    
    slope = (current_ema / past_ema) - 1
    
    if slope >= threshold:
        return TrendResult(trend="rising", confidence=min(slope / threshold, 2.0))
    elif slope <= -threshold:
        return TrendResult(trend="falling", confidence=min(abs(slope) / threshold, 2.0))
    else:
        return TrendResult(trend="sideways", confidence=1.0 - abs(slope) / threshold)
```

### 5. Retry and Circuit Breaker System

**Purpose**: Handle API failures and prevent cascading errors

**Key Components**:
```python
class RetryManager:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.failed_symbols = defaultdict(list)
    
    async def fetch_with_retry(self, fetch_func: Callable, *args, **kwargs) -> FetchResult:
        """Implement exponential backoff with jitter"""
        
    def should_circuit_break(self, symbol: str) -> bool:
        """Check if symbol should be temporarily blacklisted"""
        
    def reset_circuit_breaker(self, symbol: str):
        """Reset circuit breaker for symbol"""
```

**Circuit Breaker Logic**:
- Blacklist symbol after 3 consecutive failures within 5-minute window
- Exponential backoff: 1s, 2.5s, 6.25s delays
- Automatic retry window: 15 minutes for blacklisted symbols
- Jittered delays to prevent thundering herd

### 6. Caching Layer

**Purpose**: Reduce API calls and improve performance

**Implementation**:
```python
class DataCache:
    def __init__(self, ttl_seconds: int = 45):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data if not expired"""
        
    def cache_data(self, cache_key: str, data: pd.DataFrame):
        """Cache data with timestamp"""
        
    def generate_cache_key(self, tickers: List[str], interval: str, period: str) -> str:
        """Generate consistent cache key"""
```

**Cache Strategy**:
- TTL: 30-60 seconds for intraday data
- Key format: `{tickers_hash}_{interval}_{period}_{date}`
- LRU eviction for memory management
- Cache warming for frequently requested symbols

## Data Models

### Enhanced Result Models

```python
@dataclass
class DataFetchResult:
    success: bool
    data: Optional[pd.DataFrame]
    symbol_status: Dict[str, SymbolStatus]
    fetch_metadata: FetchMetadata
    errors: List[DataError]

@dataclass
class SymbolStatus:
    symbol: str
    status: str  # OK|EMPTY|STALE|INSUFFICIENT_BARS|API_ERROR|CIRCUIT_BREAKER
    bars_count: int
    last_timestamp: Optional[datetime]
    error_message: Optional[str]
    data_quality_score: float
    timezone: str  # Exchange timezone to avoid mixing US/EU exchanges

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timezone: str  # Exchange timezone (America/New_York, Europe/London, etc.)
    interval: str  # 1m, 15m, etc.

@dataclass
class FetchMetadata:
    fetch_timestamp: datetime
    data_provider: str
    interval: str
    period: str
    timezone: str
    market_session: str
    cache_hit: bool

@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    cleaned_data: Optional[pd.DataFrame]
    quality_score: float

@dataclass
class ValidationIssue:
    issue_type: str  # MISSING_DATA|INVALID_OHLC|TIMEZONE_MISMATCH|INSUFFICIENT_BARS
    severity: str    # ERROR|WARNING|INFO
    message: str
    affected_rows: int
    suggestion: str
```

### Enhanced Signal Models

```python
@dataclass
class EnhancedSignal:
    symbol: str
    signal_type: str  # LONG|SHORT|NO_SIGNAL
    confidence: float
    timestamp: datetime
    status: str  # OK|EMPTY|STALE|INSUFFICIENT_BARS|API_ERROR - distinguishes "no signal" from "no data"
    
    # Technical indicators
    ema5: float
    ema8: float
    ema21: float
    atr: float
    atr_long_line: float
    atr_short_line: float
    
    # Trend analysis
    ema5_trend: TrendResult
    ema8_trend: TrendResult
    ema21_trend: TrendResult
    
    # Filter results
    fomo_filter_passed: bool
    volatility_filter_passed: bool
    htf_confirmation: bool
    
    # Data quality
    data_quality_score: float
    bars_used: int
    timezone: str
    
    # Diagnostics
    failure_reasons: List[str]
    processing_time_ms: int
```

## Error Handling

### Error Classification System

```python
class ErrorTaxonomy:
    # Yahoo Finance specific errors
    YAHOO_API_ERROR = "yahoo_api_error"
    JSON_DECODE_ERROR = "json_decode_error"  # Common with yfinance - retry required
    NETWORK_TIMEOUT = "network_timeout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PERIOD_LIMIT_EXCEEDED = "period_limit_exceeded"  # 1m > 7d, 15m > 60d
    
    # Data quality errors
    INSUFFICIENT_DATA = "insufficient_data"  # Skip symbol, log reason
    STALE_DATA = "stale_data"  # Outside market hours, last bar too old
    INVALID_OHLC = "invalid_ohlc"
    TIMEZONE_MISMATCH = "timezone_mismatch"
    
    # Market errors
    MARKET_CLOSED = "market_closed"
    SYMBOL_DELISTED = "symbol_delisted"
    SYMBOL_NOT_FOUND = "symbol_not_found"
    
    # Processing errors
    INDICATOR_CALCULATION_FAILED = "indicator_calculation_failed"
    SIGNAL_GENERATION_FAILED = "signal_generation_failed"

# Yahoo Finance Constraints
class YahooConstraints:
    MAX_PERIOD_1M = "7d"    # 1-minute bars limited to 7 days
    MAX_PERIOD_15M = "60d"  # 15-minute bars limited to 60 days
    REQUIRED_PARAMS = {
        "prepost": True,     # Include pre/post market data
        "repair": True,      # Repair bad data
        "threads": False,    # Avoid threading issues
        "auto_adjust": True  # Handle splits/dividends
    }
```

### Error Recovery Strategies

```python
class ErrorRecoveryStrategy:
    def handle_yahoo_api_error(self, error: Exception, context: dict) -> RecoveryAction:
        """Handle Yahoo Finance API errors with appropriate retry strategy"""
        
    def handle_insufficient_data(self, symbol: str, bars_available: int, bars_required: int) -> RecoveryAction:
        """Try longer period or mark as insufficient"""
        
    def handle_stale_data(self, symbol: str, last_timestamp: datetime) -> RecoveryAction:
        """Use cached data or skip symbol"""
        
    def handle_market_closed(self, symbols: List[str]) -> RecoveryAction:
        """Use last available data or defer scan"""
```

### Database Schema and Indexing

**PostgreSQL Schema Updates**:
```sql
-- Enhanced scan_results table with symbol indexing
CREATE INDEX idx_scan_results_symbol ON scan_results(symbol);
CREATE INDEX idx_scan_results_timestamp ON scan_results(timestamp);
CREATE INDEX idx_scan_results_status ON scan_results(status);

-- Symbol status tracking
CREATE TABLE symbol_status (
    symbol VARCHAR(10) PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    failure_count INTEGER DEFAULT 0,
    blacklisted_until TIMESTAMP WITH TIME ZONE,
    timezone VARCHAR(50) DEFAULT 'America/New_York'
);

-- Performance monitoring
CREATE TABLE scan_performance (
    scan_id UUID PRIMARY KEY,
    symbol_count INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    total_time_ms INTEGER,
    cache_hit_rate FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Testing Strategy

### Unit Tests
- **Data Fetching**: Mock Yahoo Finance responses, test retry logic
- **Data Validation**: Test OHLC validation rules, edge cases
- **Indicator Calculations**: Test EMA/ATR calculations with known datasets
- **Error Handling**: Test all error scenarios and recovery paths
- **Insufficient Bars**: Test behavior when bars < required minimum
- **Stale Data**: Test detection of outdated market data

### Integration Tests
- **End-to-End Data Pipeline**: Real Yahoo Finance data with validation
- **Market Hours Integration**: Test across different market sessions
- **Cache Integration**: Test cache hit/miss scenarios
- **Circuit Breaker**: Test blacklisting and recovery
- **Full Scan Test**: Complete scan/backtest on AAPL, MSFT, TSLA ticker set

### Performance Tests (SLOs)
- **Scan Performance**: ≤8 seconds for 50 tickers (target SLO)
- **Backtest Performance**: ≤60 seconds for 1 symbol/month of 1m data (target SLO)
- **Large Symbol Lists**: Test with 100+ symbols
- **Data Volume**: Test with full 7-day 1-minute datasets
- **Concurrent Requests**: Test rate limiting and backoff
- **Memory Usage**: Monitor memory consumption during processing

### Reliability Tests
- **Network Failures**: Simulate network timeouts and errors
- **Yahoo Finance Outages**: Test fallback mechanisms
- **Data Corruption**: Test with malformed Yahoo responses
- **JSONDecodeError**: Test retry logic for common yfinance JSON errors
- **Resource Exhaustion**: Test behavior under high load

## Implementation Phases

### Phase 1: Core Data Fetching (Week 1)
- Implement EnhancedDataService with proper Yahoo Finance parameters
- Add retry logic with exponential backoff
- Implement basic data validation and cleaning
- Add comprehensive error handling and status tracking

### Phase 2: Market Hours and Timezone (Week 2)
- Implement MarketHoursManager
- Add timezone alignment and validation
- Implement staleness detection
- Add trading calendar integration

### Phase 3: Enhanced Indicators (Week 3)
- Upgrade technical indicator calculations
- Implement slope-based EMA trend detection
- Add enhanced FOMO and volatility filters
- Implement higher timeframe resampling

### Phase 4: Caching and Performance (Week 4)
- Implement data caching layer
- Add circuit breaker system
- Optimize batch processing
- Add performance monitoring

### Phase 5: Testing and Monitoring (Week 5)
- Comprehensive test suite
- Performance benchmarking
- Monitoring and alerting setup
- Documentation and deployment guides

This design provides a robust foundation for reliable market data processing that eliminates the current "no data" and JSON decode errors while maintaining the existing algorithm logic.