"""
Integration tests for FastAPI endpoints.
"""
import pytest
import json
import os
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.models.signals import AlgorithmSettings, Signal
from backend.app.models.results import ScanResult, BacktestResult, Trade, PerformanceMetrics
from backend.app.models.market_data import TechnicalIndicators

client = TestClient(app)


@pytest.fixture
def mock_scan_result():
    """Mock scan result for testing."""
    indicators = TechnicalIndicators(
        ema5=100.0, ema8=99.0, ema13=98.0, ema21=97.0, ema50=95.0,
        atr=2.0, atr_long_line=98.0, atr_short_line=102.0
    )
    
    signal = Signal(
        symbol="AAPL",
        signal_type="long",
        timestamp=datetime.now(),
        price=100.0,
        indicators=indicators,
        confidence=0.8
    )
    
    return ScanResult(
        id="test-scan-123",
        timestamp=datetime.now(),
        symbols_scanned=["AAPL", "GOOGL"],
        signals_found=[signal],
        settings_used=AlgorithmSettings(),
        execution_time=1.5
    )


@pytest.fixture
def mock_backtest_result():
    """Mock backtest result for testing."""
    trade = Trade(
        symbol="AAPL",
        entry_date=datetime.now() - timedelta(days=5),
        entry_price=100.0,
        exit_date=datetime.now() - timedelta(days=3),
        exit_price=105.0,
        trade_type="long",
        pnl=5.0,
        pnl_percent=5.0
    )
    
    performance = PerformanceMetrics(
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        win_rate=1.0,
        total_return=5.0,
        average_return=5.0,
        max_drawdown=0.0,
        sharpe_ratio=1.5
    )
    
    return BacktestResult(
        id="test-backtest-123",
        timestamp=datetime.now(),
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() - timedelta(days=1),
        symbols=["AAPL"],
        trades=[trade],
        performance=performance,
        settings_used=AlgorithmSettings()
    )


class TestScanEndpoints:
    """Test scan API endpoints."""
    
    @patch('backend.app.services.scanner_service.ScannerService.scan_stocks')
    def test_scan_stocks_success(self, mock_scan, mock_scan_result):
        """Test successful stock scan."""
        mock_scan.return_value = mock_scan_result
        
        request_data = {
            "symbols": ["AAPL", "GOOGL"],
            "settings": {
                "atr_multiplier": 2.5,
                "higher_timeframe": "15m"
            }
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-scan-123"
        assert data["symbols_scanned"] == ["AAPL", "GOOGL"]
        assert len(data["signals_found"]) == 1
        assert data["signals_found"][0]["symbol"] == "AAPL"
        assert data["settings_used"]["atr_multiplier"] == 2.0  # From mock result
        
        # Verify service was called with correct parameters
        mock_scan.assert_called_once()
        args = mock_scan.call_args
        assert args[0][0] == ["AAPL", "GOOGL"]  # symbols
        assert args[0][1].atr_multiplier == 2.5  # settings
    
    def test_scan_stocks_invalid_symbols(self):
        """Test scan with invalid symbols."""
        request_data = {
            "symbols": ["", "INVALID_SYMBOL_TOO_LONG"],
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_scan_stocks_empty_symbols(self):
        """Test scan with empty symbols list."""
        request_data = {
            "symbols": [],
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_scan_stocks_too_many_symbols(self):
        """Test scan with too many symbols."""
        request_data = {
            "symbols": [f"SYM{i}" for i in range(101)],  # 101 symbols (max is 100)
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_scan_stocks_invalid_settings(self):
        """Test scan with invalid settings."""
        request_data = {
            "symbols": ["AAPL"],
            "settings": {
                "atr_multiplier": "invalid"  # Should be float
            }
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid settings" in response.json()["detail"]
    
    @patch('backend.app.services.scanner_service.ScannerService.scan_stocks')
    def test_scan_stocks_service_error(self, mock_scan):
        """Test scan with service error."""
        mock_scan.side_effect = Exception("Service error")
        
        request_data = {
            "symbols": ["AAPL"],
        }
        
        response = client.post("/scan/", json=request_data)
        
        assert response.status_code == 500
        assert "Scan failed" in response.json()["detail"]
    
    @patch('backend.app.services.scanner_service.ScannerService.get_scan_history')
    def test_get_scan_history_success(self, mock_get_history, mock_scan_result):
        """Test successful scan history retrieval."""
        mock_get_history.return_value = [mock_scan_result]
        
        response = client.get("/scan/history?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test-scan-123"
        
        # Verify service was called with correct filters
        mock_get_history.assert_called_once()
        filters = mock_get_history.call_args[0][0]
        assert filters.limit == 10
        assert filters.offset == 0
    
    @patch('backend.app.services.scanner_service.ScannerService.get_scan_history')
    def test_get_scan_history_with_filters(self, mock_get_history, mock_scan_result):
        """Test scan history with filters."""
        mock_get_history.return_value = [mock_scan_result]
        
        response = client.get(
            "/scan/history"
            "?symbols=AAPL,GOOGL"
            "&signal_types=long,short"
            "&min_confidence=0.5"
            "&limit=50"
            "&offset=10"
        )
        
        assert response.status_code == 200
        
        # Verify filters were applied
        filters = mock_get_history.call_args[0][0]
        assert filters.symbols == ["AAPL", "GOOGL"]
        assert filters.signal_types == ["long", "short"]
        assert filters.min_confidence == 0.5
        assert filters.limit == 50
        assert filters.offset == 10
    
    def test_get_scan_history_invalid_params(self):
        """Test scan history with invalid parameters."""
        response = client.get("/scan/history?limit=2000")  # Max is 1000
        
        assert response.status_code == 422  # Validation error
    
    @patch('backend.app.services.scanner_service.ScannerService.get_scan_history')
    def test_get_scan_history_service_error(self, mock_get_history):
        """Test scan history with service error."""
        mock_get_history.side_effect = Exception("Database error")
        
        response = client.get("/scan/history")
        
        assert response.status_code == 500
        assert "Failed to retrieve scan history" in response.json()["detail"]


class TestBacktestEndpoints:
    """Test backtest API endpoints."""
    
    @patch('backend.app.services.backtest_service.BacktestService.run_backtest')
    def test_run_backtest_success(self, mock_backtest, mock_backtest_result):
        """Test successful backtest run."""
        mock_backtest.return_value = mock_backtest_result
        
        request_data = {
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "settings": {
                "atr_multiplier": 2.5
            }
        }
        
        response = client.post("/backtest/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-backtest-123"
        assert data["symbols"] == ["AAPL"]
        assert len(data["trades"]) == 1
        assert data["performance"]["total_trades"] == 1
        
        # Verify service was called with correct parameters
        mock_backtest.assert_called_once()
        args = mock_backtest.call_args
        assert args[1]["symbols"] == ["AAPL"]
        assert args[1]["start_date"] == date(2023, 1, 1)
        assert args[1]["end_date"] == date(2023, 1, 31)
    
    def test_run_backtest_invalid_date_range(self):
        """Test backtest with invalid date range."""
        request_data = {
            "symbols": ["AAPL"],
            "start_date": "2023-01-31",
            "end_date": "2023-01-01",  # End before start
        }
        
        response = client.post("/backtest/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_run_backtest_future_date(self):
        """Test backtest with future end date."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        
        request_data = {
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": future_date,
        }
        
        response = client.post("/backtest/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_run_backtest_too_many_symbols(self):
        """Test backtest with too many symbols."""
        request_data = {
            "symbols": [f"SYM{i}" for i in range(51)],  # 51 symbols (max is 50)
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        }
        
        response = client.post("/backtest/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('backend.app.services.backtest_service.BacktestService.run_backtest')
    def test_run_backtest_service_error(self, mock_backtest):
        """Test backtest with service error."""
        mock_backtest.side_effect = Exception("Backtest failed")
        
        request_data = {
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        }
        
        response = client.post("/backtest/", json=request_data)
        
        assert response.status_code == 500
        assert "Backtest failed" in response.json()["detail"]
    
    @patch('backend.app.services.backtest_service.BacktestService.get_backtest_history')
    def test_get_backtest_history_success(self, mock_get_history, mock_backtest_result):
        """Test successful backtest history retrieval."""
        mock_get_history.return_value = [mock_backtest_result]
        
        response = client.get("/backtest/history")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test-backtest-123"
    
    @patch('backend.app.services.backtest_service.BacktestService.get_backtest_history')
    def test_get_backtest_history_with_filters(self, mock_get_history, mock_backtest_result):
        """Test backtest history with filters."""
        mock_get_history.return_value = [mock_backtest_result]
        
        response = client.get(
            "/backtest/history"
            "?symbols=AAPL"
            "&min_trades=1"
            "&min_win_rate=0.5"
            "&limit=25"
        )
        
        assert response.status_code == 200
        
        # Verify filters were applied
        filters = mock_get_history.call_args[0][0]
        assert filters.symbols == ["AAPL"]
        assert filters.min_trades == 1
        assert filters.min_win_rate == 0.5
        assert filters.limit == 25


class TestSettingsEndpoints:
    """Test settings API endpoints."""
    
    def setUp(self):
        """Clean up settings file before each test."""
        if os.path.exists("algorithm_settings.json"):
            os.remove("algorithm_settings.json")
    
    def tearDown(self):
        """Clean up settings file after each test."""
        if os.path.exists("algorithm_settings.json"):
            os.remove("algorithm_settings.json")
    
    def test_get_settings_default(self):
        """Test getting default settings."""
        self.setUp()
        
        response = client.get("/settings/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["atr_multiplier"] == 2.0
        assert data["ema5_rising_threshold"] == 0.02
        assert data["higher_timeframe"] == "15m"
        
        self.tearDown()
    
    def test_update_settings_success(self):
        """Test successful settings update."""
        self.setUp()
        
        request_data = {
            "atr_multiplier": 2.5,
            "ema5_rising_threshold": 0.025,
            "higher_timeframe": "30m"
        }
        
        response = client.put("/settings/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["atr_multiplier"] == 2.5
        assert data["ema5_rising_threshold"] == 0.025
        assert data["higher_timeframe"] == "30m"
        # Other settings should remain default
        assert data["ema8_rising_threshold"] == 0.01
        
        self.tearDown()
    
    def test_update_settings_partial(self):
        """Test partial settings update."""
        self.setUp()
        
        # First update some settings
        client.put("/settings/", json={"atr_multiplier": 3.0})
        
        # Then update only one setting
        response = client.put("/settings/", json={"ema5_rising_threshold": 0.03})
        
        assert response.status_code == 200
        data = response.json()
        assert data["atr_multiplier"] == 3.0  # Should remain from previous update
        assert data["ema5_rising_threshold"] == 0.03  # Should be updated
        
        self.tearDown()
    
    def test_update_settings_invalid_values(self):
        """Test settings update with invalid values."""
        self.setUp()
        
        request_data = {
            "atr_multiplier": -1.0,  # Should be >= 0.1
        }
        
        response = client.put("/settings/", json=request_data)
        
        assert response.status_code == 422  # Validation error
        
        self.tearDown()
    
    def test_update_settings_invalid_timeframe(self):
        """Test settings update with invalid timeframe."""
        self.setUp()
        
        request_data = {
            "higher_timeframe": "invalid"
        }
        
        response = client.put("/settings/", json=request_data)
        
        assert response.status_code == 422  # Validation error
        
        self.tearDown()
    
    def test_reset_settings(self):
        """Test settings reset to defaults."""
        self.setUp()
        
        # First update settings
        client.put("/settings/", json={"atr_multiplier": 5.0})
        
        # Then reset
        response = client.post("/settings/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["atr_multiplier"] == 2.0  # Back to default
        assert data["ema5_rising_threshold"] == 0.02  # Back to default
        
        self.tearDown()


class TestAPIIntegration:
    """Test API integration scenarios."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Stock Scanner API"
        assert data["version"] == "1.0.0"
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    @patch('backend.app.services.scanner_service.ScannerService.scan_stocks')
    @patch('backend.app.services.scanner_service.ScannerService.get_scan_history')
    @patch('backend.app.services.backtest_service.BacktestService.run_backtest')
    @patch('backend.app.services.backtest_service.BacktestService.get_backtest_history')
    def test_workflow_integration(self, mock_backtest_history, mock_backtest, mock_scan_history, mock_scan, mock_scan_result, mock_backtest_result):
        """Test complete workflow integration."""
        mock_scan.return_value = mock_scan_result
        mock_backtest.return_value = mock_backtest_result
        mock_scan_history.return_value = [mock_scan_result]
        mock_backtest_history.return_value = [mock_backtest_result]
        
        # 1. Update settings
        settings_response = client.put("/settings/", json={"atr_multiplier": 2.5})
        assert settings_response.status_code == 200
        
        # 2. Run scan
        scan_response = client.post("/scan/", json={"symbols": ["AAPL"]})
        assert scan_response.status_code == 200
        
        # 3. Run backtest
        backtest_response = client.post("/backtest/", json={
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        })
        assert backtest_response.status_code == 200
        
        # 4. Check history
        scan_history_response = client.get("/scan/history")
        assert scan_history_response.status_code == 200
        
        backtest_history_response = client.get("/backtest/history")
        assert backtest_history_response.status_code == 200