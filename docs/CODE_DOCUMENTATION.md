# Stock Scanner Code Documentation

## Architecture Overview

The Stock Scanner is built using a modern full-stack architecture with clear separation of concerns:

- **Backend**: Python FastAPI with PostgreSQL database
- **Frontend**: React with TypeScript
- **Algorithm Engine**: Custom EMA-ATR trading algorithm
- **Data Layer**: Abstracted data services for market data retrieval

## Backend Architecture

### Core Components

#### 1. API Layer (`app/api/`)
RESTful API endpoints built with FastAPI:

- `scan.py`: Stock scanning endpoints
- `backtest.py`: Historical backtesting endpoints  
- `settings.py`: Configuration management endpoints

#### 2. Services Layer (`app/services/`)
Business logic and orchestration:

- `scanner_service.py`: Real-time stock scanning logic
- `backtest_service.py`: Historical analysis and performance calculation
- `data_service.py`: Market data retrieval and caching
- `algorithm_engine.py`: Core trading algorithm implementation

#### 3. Models (`app/models/`)
Data structures and database models:

- `market_data.py`: Market data and algorithm settings models
- `signals.py`: Trading signal data structures
- `results.py`: Scan and backtest result models
- `database_models.py`: SQLAlchemy database models

#### 4. Indicators (`app/indicators/`)
Technical analysis calculations:

- `technical_indicators.py`: EMA, ATR, and other technical indicators

#### 5. Utilities (`app/utils/`)
Cross-cutting concerns:

- `validation.py`: Input validation and sanitization
- `error_handling.py`: Centralized error handling and logging

### Key Classes and Functions

#### ScannerService
```python
class ScannerService:
    async def scan_stocks(symbols: List[str], settings: AlgorithmSettings) -> ScanResult
    async def get_scan_history() -> List[ScanResult]
```

#### BacktestService  
```python
class BacktestService:
    async def run_backtest(symbols: List[str], start_date: date, end_date: date, settings: AlgorithmSettings) -> BacktestResult
    async def get_backtest_history() -> List[BacktestResult]
```

#### AlgorithmEngine
```python
class AlgorithmEngine:
    def analyze_stock(data: pd.DataFrame, settings: AlgorithmSettings) -> Optional[Signal]
    def _check_long_conditions(data: pd.DataFrame, indicators: dict, settings: AlgorithmSettings) -> bool
    def _check_short_conditions(data: pd.DataFrame, indicators: dict, settings: AlgorithmSettings) -> bool
```

## Frontend Architecture

### Component Structure

#### 1. Main Components (`src/components/`)
- `ScannerDashboard.tsx`: Main scanning interface
- `BacktestInterface.tsx`: Historical analysis interface
- `HistoryViewer.tsx`: Results history display
- `SettingsPanel.tsx`: Algorithm configuration

#### 2. Shared Components
- `StatusIndicator.tsx`: Status display component
- `ProgressIndicator.tsx`: Progress tracking component
- `NotificationSystem.tsx`: User notifications

#### 3. Services (`src/services/`)
- `api.ts`: API communication layer

#### 4. Utilities (`src/utils/`)
- `formatters.ts`: Data formatting utilities
- `errorHandling.ts`: Error handling utilities

#### 5. Context (`src/contexts/`)
- `AppContext.tsx`: Global application state

### State Management

The application uses React Context for global state management:

```typescript
interface AppContextType {
  scanResults: ScanResult[];
  backtestResults: BacktestResult[];
  settings: AlgorithmSettings;
  isScanning: boolean;
  isBacktesting: boolean;
}
```

## Algorithm Implementation

### Core Algorithm Logic

The EMA-ATR algorithm combines multiple technical indicators:

1. **Exponential Moving Averages**: 5, 8, 13, 21, 50 periods
2. **Average True Range**: 14-period ATR with configurable multiplier
3. **Higher Timeframe Confirmation**: 15-minute timeframe validation

### Signal Generation

#### Long Signal Conditions
```python
def _check_long_conditions(self, data, indicators, settings):
    current = data.iloc[-1]
    
    # Polar formation (bullish)
    polar_bullish = (current['Close'] > current['Open'] and 
                    current['Close'] > indicators['ema8'][-1] and
                    current['Close'] > indicators['ema21'][-1])
    
    # EMA positioning
    ema_position = indicators['ema5'][-1] < indicators['atr_long_line'][-1]
    
    # Rising EMAs
    ema_rising = (self._is_rising(indicators['ema5'], settings.ema5_rising_threshold) and
                 self._is_rising(indicators['ema8'], settings.ema8_rising_threshold) and
                 self._is_rising(indicators['ema21'], settings.ema21_rising_threshold))
    
    return polar_bullish and ema_position and ema_rising
```

#### Short Signal Conditions
```python
def _check_short_conditions(self, data, indicators, settings):
    current = data.iloc[-1]
    
    # Polar formation (bearish)
    polar_bearish = (current['Close'] < current['Open'] and 
                    current['Close'] < indicators['ema8'][-1] and
                    current['Close'] < indicators['ema21'][-1])
    
    # EMA positioning
    ema_position = indicators['ema5'][-1] > indicators['atr_short_line'][-1]
    
    # Falling EMAs
    ema_falling = (self._is_falling(indicators['ema5'], settings.ema5_rising_threshold) and
                  self._is_falling(indicators['ema8'], settings.ema8_rising_threshold) and
                  self._is_falling(indicators['ema21'], settings.ema21_rising_threshold))
    
    return polar_bearish and ema_position and ema_falling
```

## Database Schema

### Tables

#### scan_results
```sql
CREATE TABLE scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    symbols_scanned JSONB NOT NULL,
    signals_found JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    execution_time DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### backtest_results
```sql
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    symbols JSONB NOT NULL,
    trades JSONB NOT NULL,
    performance JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### trades
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_date TIMESTAMPTZ,
    exit_price DECIMAL(12,4),
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('long', 'short')),
    pnl DECIMAL(12,4),
    pnl_percent DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);
```

## Testing Strategy

### Backend Testing

#### Unit Tests
- Individual function and method testing
- Mock external dependencies
- Test edge cases and error conditions

#### Integration Tests
- End-to-end workflow testing
- Database integration testing
- API endpoint testing

#### Performance Tests
- Load testing with large datasets
- Memory usage monitoring
- Response time validation

### Frontend Testing

#### Component Tests
- React component rendering
- User interaction testing
- Props and state validation

#### Integration Tests
- API integration testing
- Workflow testing
- Error handling validation

## Configuration Management

### Environment Variables

#### Backend Configuration
```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=stock_scanner
DATABASE_USER=username
DATABASE_PASSWORD=password

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# External APIs
YFINANCE_TIMEOUT=30
YFINANCE_RETRY_COUNT=3

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourdomain.com
```

#### Frontend Configuration
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=production
```

### Algorithm Settings
```python
@dataclass
class AlgorithmSettings:
    atr_multiplier: float = 2.0
    ema5_rising_threshold: float = 0.02
    ema8_rising_threshold: float = 0.01
    ema21_rising_threshold: float = 0.005
    volatility_filter: float = 1.5
    fomo_filter: float = 1.0
    higher_timeframe: str = "15m"
```

## Error Handling

### Backend Error Handling
```python
class StockScannerException(Exception):
    """Base exception for stock scanner errors."""
    pass

class ValidationError(StockScannerException):
    """Raised when input validation fails."""
    pass

class DataFetchError(StockScannerException):
    """Raised when market data cannot be retrieved."""
    pass

class AlgorithmError(StockScannerException):
    """Raised when algorithm calculation fails."""
    pass
```

### Frontend Error Handling
```typescript
interface ErrorState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, ErrorState> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): ErrorState {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });
  }
}
```

## Performance Considerations

### Backend Optimizations
- Database connection pooling
- Query optimization with indexes
- Async/await for concurrent operations
- Caching of frequently accessed data

### Frontend Optimizations
- React.memo for component memoization
- useMemo and useCallback for expensive calculations
- Code splitting with React.lazy
- Debounced user inputs

## Security Measures

### Backend Security
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- CORS configuration
- Rate limiting on API endpoints

### Frontend Security
- XSS prevention with proper escaping
- Content Security Policy headers
- Secure API communication over HTTPS
- Input validation on client side

## Deployment Architecture

### Production Setup
- Docker containerization
- Nginx reverse proxy
- PostgreSQL database
- Supervisor process management
- SSL/TLS encryption

### CI/CD Pipeline
- Automated testing on pull requests
- Code quality checks
- Security scanning
- Automated deployment to staging/production

## Monitoring and Logging

### Application Logging
```python
import logging

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
```

### Performance Monitoring
- Response time tracking
- Memory usage monitoring
- Database query performance
- Error rate monitoring

## Development Guidelines

### Code Style
- Python: Black formatter, isort, flake8
- TypeScript: Prettier, ESLint
- Consistent naming conventions
- Comprehensive docstrings and comments

### Git Workflow
- Feature branch development
- Pull request reviews
- Automated testing before merge
- Semantic versioning

### Documentation Standards
- API documentation with OpenAPI/Swagger
- Code comments for complex logic
- README files for setup instructions
- Architecture decision records (ADRs)

---

*This code documentation is maintained alongside the codebase and updated with each release.*