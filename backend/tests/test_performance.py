"""
Performance tests for stock scanner system.
Tests system behavior with large datasets and concurrent operations.
"""

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from app.services.scanner_service import ScannerService
from app.services.backtest_service import BacktestService
from app.services.data_service import DataService
from app.models.signals import AlgorithmSettings


class TestPerformance:
    """Performance tests for the stock scanner system."""
    
    @pytest.fixture
    def scanner_service(self):
        """Create scanner service instance."""
        with patch('app.services.scanner_service.get_session'):
            return ScannerService()
    
    @pytest.fixture
    def backtest_service(self):
        """Create backtest service instance."""
        with patch('app.services.backtest_service.get_session'):
            return BacktestService()
    
    @pytest.fixture
    def data_service(self):
        """Create data service instance."""
        return DataService()
    
    @pytest.fixture
    def sample_settings(self):
        """Sample algorithm settings for testing."""
        return AlgorithmSettings()
    
    def generate_large_market_data(self, periods=10000):
        """Generate large market data for performance testing."""
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='1min')
        return pd.DataFrame({
            'Open': [100 + (i % 100) * 0.1 for i in range(periods)],
            'High': [101 + (i % 100) * 0.1 for i in range(periods)],
            'Low': [99 + (i % 100) * 0.1 for i in range(periods)],
            'Close': [100.5 + (i % 100) * 0.1 for i in range(periods)],
            'Volume': [1000 + i * 10 for i in range(periods)]
        }, index=dates)
    
    def generate_stock_symbols(self, count=100):
        """Generate list of stock symbols for testing."""
        return [f"STOCK{i:03d}" for i in range(count)]
    
    @pytest.mark.performance
    @patch('app.services.data_service.DataService.fetch_current_data')
    @patch('app.services.scanner_service.ScannerService._save_scan_result')
    async def test_large_stock_list_scan_performance(self, mock_save, mock_data, scanner_service, sample_settings):
        """Test scanning performance with large stock lists."""
        # Generate 100 stock symbols
        symbols = self.generate_stock_symbols(100)
        large_data = self.generate_large_market_data(1000)
        
        # Mock data for all symbols
        mock_data.return_value = {symbol: large_data for symbol in symbols}
        
        # Measure performance
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        result = await scanner_service.scan_stocks(symbols, sample_settings)
        
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Performance assertions
        assert execution_time < 30.0, f"Scan took too long: {execution_time:.2f}s"
        assert memory_used < 500, f"Memory usage too high: {memory_used:.2f}MB"
        assert result is not None
        assert len(result.symbols_scanned) == 100
        
        print(f"Large scan performance: {execution_time:.2f}s, {memory_used:.2f}MB")
    
    @pytest.mark.performance
    @patch('app.services.data_service.DataService.fetch_historical_data')
    @patch('app.services.backtest_service.BacktestService._save_backtest_result')
    async def test_large_historical_data_backtest_performance(self, mock_save, mock_data, backtest_service, sample_settings):
        """Test backtest performance with large historical datasets."""
        symbols = self.generate_stock_symbols(20)
        large_historical_data = self.generate_large_market_data(50000)  # ~35 days of 1-min data
        
        mock_data.return_value = {symbol: large_historical_data for symbol in symbols}
        
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        result = await backtest_service.run_backtest(
            symbols,
            date(2023, 1, 1),
            date(2023, 2, 5),
            sample_settings
        )
        
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Performance assertions
        assert execution_time < 60.0, f"Backtest took too long: {execution_time:.2f}s"
        assert memory_used < 1000, f"Memory usage too high: {memory_used:.2f}MB"
        assert result is not None
        assert len(result.symbols) == 20
        
        print(f"Large backtest performance: {execution_time:.2f}s, {memory_used:.2f}MB")
    
    @pytest.mark.performance
    @patch('app.services.scanner_service.ScannerService._save_scan_result')
    async def test_concurrent_scan_performance(self, mock_save, scanner_service, sample_settings):
        """Test performance with multiple concurrent scans."""
        symbols = self.generate_stock_symbols(10)
        market_data = self.generate_large_market_data(1000)
        
        with patch('app.services.data_service.DataService.fetch_current_data') as mock_data:
            mock_data.return_value = {symbol: market_data for symbol in symbols}
            
            # Run 5 concurrent scans
            start_time = time.time()
            
            tasks = [
                scanner_service.scan_stocks(symbols[:5], sample_settings)
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 20.0, f"Concurrent scans took too long: {execution_time:.2f}s"
            assert len(results) == 5
            assert all(result is not None for result in results)
            
            print(f"Concurrent scan performance: {execution_time:.2f}s for 5 scans")
    
    @pytest.mark.performance
    def test_technical_indicators_calculation_performance(self):
        """Test performance of technical indicators calculation."""
        from app.indicators.technical_indicators import TechnicalIndicatorEngine
        
        # Generate large dataset
        large_data = self.generate_large_market_data(10000)
        
        start_time = time.time()
        
        indicators = TechnicalIndicatorEngine()
        
        # Calculate all indicators (they return single values, not arrays)
        ema5 = indicators.calculate_ema(large_data['Close'].tolist(), 5)
        ema8 = indicators.calculate_ema(large_data['Close'].tolist(), 8)
        ema13 = indicators.calculate_ema(large_data['Close'].tolist(), 13)
        ema21 = indicators.calculate_ema(large_data['Close'].tolist(), 21)
        ema50 = indicators.calculate_ema(large_data['Close'].tolist(), 50)
        atr = indicators.calculate_atr(
            large_data['High'].tolist(), 
            large_data['Low'].tolist(), 
            large_data['Close'].tolist()
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 5.0, f"Indicator calculation took too long: {execution_time:.2f}s"
        assert isinstance(ema5, float)
        assert isinstance(atr, float)
        
        print(f"Indicators calculation performance: {execution_time:.2f}s for 10k data points")
    
    @pytest.mark.performance
    @patch('app.services.scanner_service.ScannerService._save_scan_result')
    @patch('app.services.scanner_service.ScannerService.get_scan_history')
    async def test_database_performance(self, mock_history, mock_save, scanner_service, sample_settings):
        """Test database performance with multiple operations."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        market_data = self.generate_large_market_data(100)
        
        with patch('app.services.data_service.DataService.fetch_current_data') as mock_data:
            mock_data.return_value = {symbol: market_data for symbol in symbols}
            
            # Perform multiple scans and measure database performance
            start_time = time.time()
            
            scan_results = []
            for i in range(10):
                result = await scanner_service.scan_stocks(symbols, sample_settings)
                scan_results.append(result)
            
            # Mock history retrieval
            mock_history.return_value = scan_results
            history = await scanner_service.get_scan_history()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 15.0, f"Database operations took too long: {execution_time:.2f}s"
            assert len(history) >= 10
            assert len(scan_results) == 10
            
            print(f"Database performance: {execution_time:.2f}s for 10 scans + history retrieval")
    
    @pytest.mark.performance
    def test_memory_usage_stability(self):
        """Test memory usage stability during intensive operations."""
        from app.indicators.technical_indicators import TechnicalIndicatorEngine
        
        indicators = TechnicalIndicatorEngine()
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # Perform multiple intensive calculations
        for i in range(100):
            data = self.generate_large_market_data(1000)
            ema = indicators.calculate_ema(data['Close'].tolist(), 21)
            atr = indicators.calculate_atr(
                data['High'].tolist(), 
                data['Low'].tolist(), 
                data['Close'].tolist()
            )
            
            # Force garbage collection periodically
            if i % 10 == 0:
                import gc
                gc.collect()
        
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 200, f"Memory growth too high: {memory_growth:.2f}MB"
        
        print(f"Memory stability test: {memory_growth:.2f}MB growth over 100 iterations")
    
    @pytest.mark.performance
    async def test_api_response_time_performance(self):
        """Test API response time performance."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test scan endpoint response time
        scan_payload = {
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
        
        with patch('app.services.data_service.DataService.fetch_current_data') as mock_data, \
             patch('app.services.scanner_service.ScannerService._save_scan_result') as mock_save:
            
            # Mock the data service to return test data
            mock_data.return_value = {}
            mock_save.return_value = None
            
            start_time = time.time()
            response = client.post("/scan/", json=scan_payload)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0, f"API response too slow: {response_time:.2f}s"
            
            print(f"API response time: {response_time:.2f}s")


# Performance test configuration
def pytest_configure(config):
    """Configure pytest for performance tests."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )


# Custom performance test runner
class PerformanceTestRunner:
    """Custom test runner for performance tests."""
    
    def __init__(self):
        self.results = []
    
    def run_performance_suite(self):
        """Run all performance tests and collect results."""
        import subprocess
        
        # Run performance tests
        result = subprocess.run([
            'python', '-m', 'pytest', 
            'backend/tests/test_performance.py', 
            '-m', 'performance',
            '-v'
        ], capture_output=True, text=True)
        
        return result.returncode == 0, result.stdout, result.stderr


if __name__ == "__main__":
    runner = PerformanceTestRunner()
    success, stdout, stderr = runner.run_performance_suite()
    
    if success:
        print("All performance tests passed!")
        print(stdout)
    else:
        print("Performance tests failed!")
        print(stderr)