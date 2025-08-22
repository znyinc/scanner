# Stock Scanner API Documentation

## Overview

The Stock Scanner API provides RESTful endpoints for stock scanning, backtesting, and configuration management. All endpoints return JSON responses and use standard HTTP status codes.

**Base URL**: `http://localhost:8000/api`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Common Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Endpoints

### 1. Stock Scanning

#### POST /api/scan

Initiates a stock scan using the specified symbols and algorithm settings.

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "settings": {
    "atr_multiplier": 2.0,
    "ema5_rising_threshold": 0.02,
    "ema8_rising_threshold": 0.01,
    "ema21_rising_threshold": 0.005,
    "volatility_filter": 1.5,
    "fomo_filter": 1.0,
    "higher_timeframe": "15m"
  }
}
```

**Parameters:**
- `symbols` (array, required): List of stock symbols to scan
- `settings` (object, optional): Algorithm configuration settings

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "scan_123456789",
    "timestamp": "2024-01-15T10:30:00Z",
    "symbols_scanned": ["AAPL", "GOOGL", "MSFT"],
    "signals_found": [
      {
        "symbol": "AAPL",
        "signal_type": "long",
        "timestamp": "2024-01-15T10:30:00Z",
        "price": 150.25,
        "indicators": {
          "ema5": 149.80,
          "ema8": 149.50,
          "ema13": 149.20,
          "ema21": 148.90,
          "ema50": 148.00,
          "atr": 2.15,
          "atr_long_line": 144.60,
          "atr_short_line": 153.20
        },
        "confidence": 85.5
      }
    ],
    "settings_used": {
      "atr_multiplier": 2.0,
      "ema5_rising_threshold": 0.02,
      "ema8_rising_threshold": 0.01,
      "ema21_rising_threshold": 0.005,
      "volatility_filter": 1.5,
      "fomo_filter": 1.0,
      "higher_timeframe": "15m"
    },
    "execution_time": 2.34
  }
}
```

**Status Codes:**
- `200 OK`: Scan completed successfully
- `400 Bad Request`: Invalid input parameters
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### 2. Historical Backtesting

#### POST /api/backtest

Runs a historical backtest using the specified parameters.

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOGL"],
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "settings": {
    "atr_multiplier": 2.0,
    "ema5_rising_threshold": 0.02,
    "ema8_rising_threshold": 0.01,
    "ema21_rising_threshold": 0.005,
    "volatility_filter": 1.5,
    "fomo_filter": 1.0,
    "higher_timeframe": "15m"
  }
}
```

**Parameters:**
- `symbols` (array, required): List of stock symbols to backtest
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `settings` (object, optional): Algorithm configuration settings

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "backtest_123456789",
    "timestamp": "2024-01-15T10:30:00Z",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "symbols": ["AAPL", "GOOGL"],
    "trades": [
      {
        "symbol": "AAPL",
        "entry_date": "2024-01-02T09:30:00Z",
        "entry_price": 148.50,
        "exit_date": "2024-01-03T15:30:00Z",
        "exit_price": 151.20,
        "trade_type": "long",
        "pnl": 2.70,
        "pnl_percent": 1.82
      }
    ],
    "performance": {
      "total_trades": 15,
      "winning_trades": 9,
      "losing_trades": 6,
      "win_rate": 60.0,
      "total_return": 8.5,
      "average_return": 0.57,
      "max_drawdown": -3.2,
      "sharpe_ratio": 1.45
    },
    "settings_used": {
      "atr_multiplier": 2.0,
      "ema5_rising_threshold": 0.02,
      "ema8_rising_threshold": 0.01,
      "ema21_rising_threshold": 0.005,
      "volatility_filter": 1.5,
      "fomo_filter": 1.0,
      "higher_timeframe": "15m"
    }
  }
}
```

**Status Codes:**
- `200 OK`: Backtest completed successfully
- `400 Bad Request`: Invalid input parameters
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### 3. History Management

#### GET /api/history/scans

Retrieves historical scan results with optional filtering.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of results (default: 50)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `start_date` (string, optional): Filter by start date (YYYY-MM-DD)
- `end_date` (string, optional): Filter by end date (YYYY-MM-DD)
- `symbol` (string, optional): Filter by specific symbol

**Example Request:**
```
GET /api/history/scans?limit=10&offset=0&symbol=AAPL
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scans": [
      {
        "id": "scan_123456789",
        "timestamp": "2024-01-15T10:30:00Z",
        "symbols_scanned": ["AAPL", "GOOGL"],
        "signals_count": 2,
        "execution_time": 2.34
      }
    ],
    "total_count": 25,
    "has_more": true
  }
}
```

#### GET /api/history/scans/{scan_id}

Retrieves detailed results for a specific scan.

**Path Parameters:**
- `scan_id` (string, required): Unique scan identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "scan_123456789",
    "timestamp": "2024-01-15T10:30:00Z",
    "symbols_scanned": ["AAPL", "GOOGL"],
    "signals_found": [...],
    "settings_used": {...},
    "execution_time": 2.34
  }
}
```

#### GET /api/history/backtests

Retrieves historical backtest results with optional filtering.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of results (default: 50)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `start_date` (string, optional): Filter by start date (YYYY-MM-DD)
- `end_date` (string, optional): Filter by end date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "backtests": [
      {
        "id": "backtest_123456789",
        "timestamp": "2024-01-15T10:30:00Z",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "symbols": ["AAPL", "GOOGL"],
        "total_trades": 15,
        "win_rate": 60.0,
        "total_return": 8.5
      }
    ],
    "total_count": 10,
    "has_more": false
  }
}
```

#### GET /api/history/backtests/{backtest_id}

Retrieves detailed results for a specific backtest.

**Path Parameters:**
- `backtest_id` (string, required): Unique backtest identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "backtest_123456789",
    "timestamp": "2024-01-15T10:30:00Z",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "symbols": ["AAPL", "GOOGL"],
    "trades": [...],
    "performance": {...},
    "settings_used": {...}
  }
}
```

### 4. Settings Management

#### GET /api/settings

Retrieves current algorithm settings.

**Response:**
```json
{
  "success": true,
  "data": {
    "atr_multiplier": 2.0,
    "ema5_rising_threshold": 0.02,
    "ema8_rising_threshold": 0.01,
    "ema21_rising_threshold": 0.005,
    "volatility_filter": 1.5,
    "fomo_filter": 1.0,
    "higher_timeframe": "15m"
  }
}
```

#### PUT /api/settings

Updates algorithm settings.

**Request Body:**
```json
{
  "atr_multiplier": 2.5,
  "ema5_rising_threshold": 0.025,
  "ema8_rising_threshold": 0.015,
  "ema21_rising_threshold": 0.008,
  "volatility_filter": 1.8,
  "fomo_filter": 1.2,
  "higher_timeframe": "30m"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "atr_multiplier": 2.5,
    "ema5_rising_threshold": 0.025,
    "ema8_rising_threshold": 0.015,
    "ema21_rising_threshold": 0.008,
    "volatility_filter": 1.8,
    "fomo_filter": 1.2,
    "higher_timeframe": "30m"
  },
  "message": "Settings updated successfully"
}
```

#### POST /api/settings/reset

Resets algorithm settings to default values.

**Response:**
```json
{
  "success": true,
  "data": {
    "atr_multiplier": 2.0,
    "ema5_rising_threshold": 0.02,
    "ema8_rising_threshold": 0.01,
    "ema21_rising_threshold": 0.005,
    "volatility_filter": 1.5,
    "fomo_filter": 1.0,
    "higher_timeframe": "15m"
  },
  "message": "Settings reset to defaults"
}
```

## Data Models

### AlgorithmSettings
```json
{
  "atr_multiplier": 2.0,
  "ema5_rising_threshold": 0.02,
  "ema8_rising_threshold": 0.01,
  "ema21_rising_threshold": 0.005,
  "volatility_filter": 1.5,
  "fomo_filter": 1.0,
  "higher_timeframe": "15m"
}
```

### Signal
```json
{
  "symbol": "AAPL",
  "signal_type": "long",
  "timestamp": "2024-01-15T10:30:00Z",
  "price": 150.25,
  "indicators": {
    "ema5": 149.80,
    "ema8": 149.50,
    "ema13": 149.20,
    "ema21": 148.90,
    "ema50": 148.00,
    "atr": 2.15,
    "atr_long_line": 144.60,
    "atr_short_line": 153.20
  },
  "confidence": 85.5
}
```

### Trade
```json
{
  "symbol": "AAPL",
  "entry_date": "2024-01-02T09:30:00Z",
  "entry_price": 148.50,
  "exit_date": "2024-01-03T15:30:00Z",
  "exit_price": 151.20,
  "trade_type": "long",
  "pnl": 2.70,
  "pnl_percent": 1.82
}
```

### PerformanceMetrics
```json
{
  "total_trades": 15,
  "winning_trades": 9,
  "losing_trades": 6,
  "win_rate": 60.0,
  "total_return": 8.5,
  "average_return": 0.57,
  "max_drawdown": -3.2,
  "sharpe_ratio": 1.45
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `INVALID_SYMBOLS` | One or more stock symbols are invalid |
| `INVALID_DATE_RANGE` | Date range is invalid or too large |
| `INSUFFICIENT_DATA` | Not enough historical data available |
| `API_RATE_LIMIT` | External API rate limit exceeded |
| `DATA_FETCH_ERROR` | Error fetching market data |
| `ALGORITHM_ERROR` | Error in algorithm calculation |
| `DATABASE_ERROR` | Database operation failed |
| `INTERNAL_ERROR` | Unexpected server error |

## Rate Limits

- **Scan Endpoint**: 10 requests per minute
- **Backtest Endpoint**: 5 requests per minute
- **History Endpoints**: 60 requests per minute
- **Settings Endpoints**: 30 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1642248600
```

## Examples

### Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api"

# Run a scan
scan_data = {
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "settings": {
        "atr_multiplier": 2.0,
        "volatility_filter": 1.5
    }
}

response = requests.post(f"{BASE_URL}/scan", json=scan_data)
if response.status_code == 200:
    result = response.json()
    print(f"Found {len(result['data']['signals_found'])} signals")
else:
    print(f"Error: {response.status_code}")

# Run a backtest
backtest_data = {
    "symbols": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}

response = requests.post(f"{BASE_URL}/backtest", json=backtest_data)
if response.status_code == 200:
    result = response.json()
    performance = result['data']['performance']
    print(f"Win Rate: {performance['win_rate']}%")
    print(f"Total Return: {performance['total_return']}%")
```

### JavaScript Client Example

```javascript
// Run a scan
const scanData = {
  symbols: ['AAPL', 'GOOGL', 'MSFT'],
  settings: {
    atr_multiplier: 2.0,
    volatility_filter: 1.5
  }
};

fetch('/api/scan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(scanData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`Found ${data.data.signals_found.length} signals`);
  } else {
    console.error('Scan failed:', data.error);
  }
});

// Get scan history
fetch('/api/history/scans?limit=10')
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`Retrieved ${data.data.scans.length} historical scans`);
  }
});
```

## WebSocket Support (Future)

Real-time updates will be available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'scan_update') {
    // Handle real-time scan updates
  }
};
```

## Changelog

### Version 1.0.0
- Initial API release
- Basic scan and backtest functionality
- History management
- Settings configuration

---

*This API documentation is regularly updated. Check for the latest version to ensure compatibility with your applications.*