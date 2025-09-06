"""
Unit tests for Pydantic validation models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.pydantic_models import (
    SymbolDiagnosticModel,
    PerformanceMetricsModel,
    SignalAnalysisModel,
    DataQualityMetricsModel,
    AlgorithmSettingsModel,
    EnhancedScanDiagnosticsModel,
    EnhancedScanResultModel,
    ScanComparisonModel,
    ExportRequestModel,
    HistoryFiltersModel,
    SymbolStatus,
    ScanStatus,
    ExportFormat
)


class TestSymbolDiagnosticModel:
    """Test SymbolDiagnosticModel validation."""
    
    def test_valid_symbol_diagnostic(self):
        """Test valid SymbolDiagnosticModel creation."""
        data = {
            "symbol": "AAPL",
            "status": "success",
            "data_points_1m": 390,
            "data_points_15m": 26,
            "timeframe_coverage": {"1m": True, "15m": True},
            "error_message": None,
            "fetch_time": 1.2,
            "processing_time": 0.3
        }
        
        model = SymbolDiagnosticModel(**data)
        assert model.symbol == "AAPL"
        assert model.status == SymbolStatus.SUCCESS
        assert model.data_points_1m == 390
    
    def test_invalid_symbol_status(self):
        """Test invalid symbol status validation."""
        data = {
            "symbol": "AAPL",
            "status": "invalid_status",
            "data_points_1m": 390,
            "data_points_15m": 26,
            "timeframe_coverage": {"1m": True},
            "fetch_time": 1.2,
            "processing_time": 0.3
        }
        
        with pytest.raises(ValidationError):
            SymbolDiagnosticModel(**data)
    
    def test_negative_data_points(self):
        """Test negative data points validation."""
        data = {
            "symbol": "AAPL",
            "status": "success",
            "data_points_1m": -1,
            "data_points_15m": 26,
            "timeframe_coverage": {"1m": True},
            "fetch_time": 1.2,
            "processing_time": 0.3
        }
        
        with pytest.raises(ValidationError):
            SymbolDiagnosticModel(**data)
    
    def test_invalid_timeframe_coverage(self):
        """Test invalid timeframe coverage validation."""
        data = {
            "symbol": "AAPL",
            "status": "success",
            "data_points_1m": 390,
            "data_points_15m": 26,
            "timeframe_coverage": {"invalid_timeframe": True},
            "fetch_time": 1.2,
            "processing_time": 0.3
        }
        
        with pytest.raises(ValidationError):
            SymbolDiagnosticModel(**data)


class TestPerformanceMetricsModel:
    """Test PerformanceMetricsModel validation."""
    
    def test_valid_performance_metrics(self):
        """Test valid PerformanceMetricsModel creation."""
        data = {
            "memory_usage_mb": 256.5,
            "api_requests_made": 150,
            "api_rate_limit_remaining": 850,
            "cache_hit_rate": 0.75,
            "concurrent_requests": 5,
            "bottleneck_phase": "data_fetch"
        }
        
        model = PerformanceMetricsModel(**data)
        assert model.memory_usage_mb == 256.5
        assert model.cache_hit_rate == 0.75
    
    def test_invalid_cache_hit_rate(self):
        """Test invalid cache hit rate validation."""
        data = {
            "memory_usage_mb": 256.5,
            "api_requests_made": 150,
            "api_rate_limit_remaining": 850,
            "cache_hit_rate": 1.5,  # Invalid: > 1.0
            "concurrent_requests": 5
        }
        
        with pytest.raises(ValidationError):
            PerformanceMetricsModel(**data)
    
    def test_negative_memory_usage(self):
        """Test negative memory usage validation."""
        data = {
            "memory_usage_mb": -10.0,
            "api_requests_made": 150,
            "api_rate_limit_remaining": 850,
            "cache_hit_rate": 0.75,
            "concurrent_requests": 5
        }
        
        with pytest.raises(ValidationError):
            PerformanceMetricsModel(**data)


class TestSignalAnalysisModel:
    """Test SignalAnalysisModel validation."""
    
    def test_valid_signal_analysis(self):
        """Test valid SignalAnalysisModel creation."""
        data = {
            "signals_found": 3,
            "symbols_meeting_partial_criteria": {
                "AAPL": ["ema_rising", "polar_formation"]
            },
            "rejection_reasons": {
                "fomo_filter": ["MSFT", "TSLA"]
            },
            "confidence_distribution": {
                "0.8-1.0": 2,
                "0.6-0.8": 1
            }
        }
        
        model = SignalAnalysisModel(**data)
        assert model.signals_found == 3
        assert "AAPL" in model.symbols_meeting_partial_criteria
    
    def test_invalid_confidence_distribution(self):
        """Test invalid confidence distribution validation."""
        data = {
            "signals_found": 1,
            "confidence_distribution": {
                "invalid_range": 1  # Invalid range format
            }
        }
        
        with pytest.raises(ValidationError):
            SignalAnalysisModel(**data)
    
    def test_negative_signals_found(self):
        """Test negative signals found validation."""
        data = {
            "signals_found": -1
        }
        
        with pytest.raises(ValidationError):
            SignalAnalysisModel(**data)


class TestDataQualityMetricsModel:
    """Test DataQualityMetricsModel validation."""
    
    def test_valid_data_quality_metrics(self):
        """Test valid DataQualityMetricsModel creation."""
        data = {
            "total_data_points": 1500,
            "success_rate": 0.85,
            "average_fetch_time": 2.3,
            "data_completeness": 0.92,
            "quality_score": 0.88
        }
        
        model = DataQualityMetricsModel(**data)
        assert model.total_data_points == 1500
        assert model.success_rate == 0.85
    
    def test_invalid_success_rate(self):
        """Test invalid success rate validation."""
        data = {
            "total_data_points": 1500,
            "success_rate": 1.5,  # Invalid: > 1.0
            "average_fetch_time": 2.3,
            "data_completeness": 0.92,
            "quality_score": 0.88
        }
        
        with pytest.raises(ValidationError):
            DataQualityMetricsModel(**data)
    
    def test_negative_total_data_points(self):
        """Test negative total data points validation."""
        data = {
            "total_data_points": -100,
            "success_rate": 0.85,
            "average_fetch_time": 2.3,
            "data_completeness": 0.92,
            "quality_score": 0.88
        }
        
        with pytest.raises(ValidationError):
            DataQualityMetricsModel(**data)


class TestAlgorithmSettingsModel:
    """Test AlgorithmSettingsModel validation."""
    
    def test_valid_algorithm_settings(self):
        """Test valid AlgorithmSettingsModel creation."""
        data = {
            "atr_multiplier": 2.5,
            "ema5_rising_threshold": 0.02,
            "ema8_rising_threshold": 0.01,
            "ema21_rising_threshold": 0.005,
            "volatility_filter": 1.5,
            "fomo_filter": 1.0,
            "higher_timeframe": "4h"
        }
        
        model = AlgorithmSettingsModel(**data)
        assert model.atr_multiplier == 2.5
        assert model.higher_timeframe == "4h"
    
    def test_default_values(self):
        """Test default values for AlgorithmSettingsModel."""
        model = AlgorithmSettingsModel()
        assert model.atr_multiplier == 2.0
        assert model.higher_timeframe == "4h"
    
    def test_invalid_higher_timeframe(self):
        """Test invalid higher timeframe validation."""
        data = {
            "higher_timeframe": "invalid_timeframe"
        }
        
        with pytest.raises(ValidationError):
            AlgorithmSettingsModel(**data)
    
    def test_negative_atr_multiplier(self):
        """Test negative ATR multiplier validation."""
        data = {
            "atr_multiplier": -1.0
        }
        
        with pytest.raises(ValidationError):
            AlgorithmSettingsModel(**data)


class TestEnhancedScanResultModel:
    """Test EnhancedScanResultModel validation."""
    
    def test_valid_enhanced_scan_result(self):
        """Test valid EnhancedScanResultModel creation."""
        data = {
            "id": "test-scan-1",
            "timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "symbols_scanned": ["AAPL", "GOOGL"],
            "signals_found": [],
            "settings_used": {
                "atr_multiplier": 2.0,
                "higher_timeframe": "4h"
            },
            "execution_time": 2.5,
            "scan_status": "completed",
            "data_quality_score": 0.95
        }
        
        model = EnhancedScanResultModel(**data)
        assert model.id == "test-scan-1"
        assert model.scan_status == ScanStatus.COMPLETED
        assert model.data_quality_score == 0.95
    
    def test_invalid_data_quality_score(self):
        """Test invalid data quality score validation."""
        data = {
            "id": "test-scan-1",
            "timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "symbols_scanned": ["AAPL"],
            "signals_found": [],
            "settings_used": {"atr_multiplier": 2.0},
            "execution_time": 2.5,
            "data_quality_score": 1.5  # Invalid: > 1.0
        }
        
        with pytest.raises(ValidationError):
            EnhancedScanResultModel(**data)
    
    def test_negative_execution_time(self):
        """Test negative execution time validation."""
        data = {
            "id": "test-scan-1",
            "timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "symbols_scanned": ["AAPL"],
            "signals_found": [],
            "settings_used": {"atr_multiplier": 2.0},
            "execution_time": -1.0  # Invalid: negative
        }
        
        with pytest.raises(ValidationError):
            EnhancedScanResultModel(**data)


class TestExportRequestModel:
    """Test ExportRequestModel validation."""
    
    def test_valid_export_request(self):
        """Test valid ExportRequestModel creation."""
        data = {
            "scan_ids": ["scan-1", "scan-2"],
            "format": "csv",
            "include_diagnostics": True,
            "date_range_start": datetime(2024, 1, 1),
            "date_range_end": datetime(2024, 1, 31)
        }
        
        model = ExportRequestModel(**data)
        assert len(model.scan_ids) == 2
        assert model.format == ExportFormat.CSV
    
    def test_empty_scan_ids(self):
        """Test empty scan IDs validation."""
        data = {
            "scan_ids": [],  # Invalid: empty list
            "format": "csv"
        }
        
        with pytest.raises(ValidationError):
            ExportRequestModel(**data)
    
    def test_invalid_date_range(self):
        """Test invalid date range validation."""
        data = {
            "scan_ids": ["scan-1"],
            "format": "csv",
            "date_range_start": datetime(2024, 1, 31),
            "date_range_end": datetime(2024, 1, 1)  # Invalid: end before start
        }
        
        with pytest.raises(ValidationError):
            ExportRequestModel(**data)


class TestHistoryFiltersModel:
    """Test HistoryFiltersModel validation."""
    
    def test_valid_history_filters(self):
        """Test valid HistoryFiltersModel creation."""
        data = {
            "date_range_start": datetime(2024, 1, 1),
            "date_range_end": datetime(2024, 1, 31),
            "scan_status": "completed",
            "min_symbols": 5,
            "max_symbols": 50,
            "min_quality_score": 0.8,
            "max_quality_score": 1.0
        }
        
        model = HistoryFiltersModel(**data)
        assert model.scan_status == ScanStatus.COMPLETED
        assert model.min_symbols == 5
    
    def test_invalid_symbol_range(self):
        """Test invalid symbol range validation."""
        data = {
            "min_symbols": 50,
            "max_symbols": 5  # Invalid: max < min
        }
        
        with pytest.raises(ValidationError):
            HistoryFiltersModel(**data)
    
    def test_invalid_quality_score_range(self):
        """Test invalid quality score range validation."""
        data = {
            "min_quality_score": 0.9,
            "max_quality_score": 0.8  # Invalid: max < min
        }
        
        with pytest.raises(ValidationError):
            HistoryFiltersModel(**data)
    
    def test_invalid_execution_time_range(self):
        """Test invalid execution time range validation."""
        data = {
            "min_execution_time": 5.0,
            "max_execution_time": 2.0  # Invalid: max < min
        }
        
        with pytest.raises(ValidationError):
            HistoryFiltersModel(**data)
    
    def test_long_search_text(self):
        """Test search text length validation."""
        data = {
            "search_text": "A" * 300  # Invalid: too long
        }
        
        with pytest.raises(ValidationError):
            HistoryFiltersModel(**data)