"""
Unit tests for enhanced diagnostic models.
"""
import pytest
from datetime import datetime
from decimal import Decimal
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.enhanced_diagnostics import (
    SymbolDiagnostic,
    PerformanceMetrics,
    SignalAnalysis,
    DataQualityMetrics,
    EnhancedScanDiagnostics,
    EnhancedScanResult,
    ScanComparison,
    ExportRequest,
    HistoryFilters
)
from app.models.signals import AlgorithmSettings


class TestSymbolDiagnostic:
    """Test SymbolDiagnostic model."""
    
    def test_symbol_diagnostic_creation(self):
        """Test creating SymbolDiagnostic instance."""
        diagnostic = SymbolDiagnostic(
            symbol="AAPL",
            status="success",
            data_points_1m=390,
            data_points_15m=26,
            timeframe_coverage={"1m": True, "15m": True, "4h": False},
            error_message=None,
            fetch_time=1.2,
            processing_time=0.3
        )
        
        assert diagnostic.symbol == "AAPL"
        assert diagnostic.status == "success"
        assert diagnostic.data_points_1m == 390
        assert diagnostic.timeframe_coverage["1m"] is True
        assert diagnostic.error_message is None
    
    def test_symbol_diagnostic_serialization(self):
        """Test SymbolDiagnostic JSON serialization."""
        diagnostic = SymbolDiagnostic(
            symbol="AAPL",
            status="error",
            data_points_1m=0,
            data_points_15m=0,
            timeframe_coverage={"1m": False, "15m": False},
            error_message="API timeout",
            fetch_time=30.0,
            processing_time=0.0
        )
        
        # Test serialization round trip
        data_dict = diagnostic.to_dict()
        restored = SymbolDiagnostic.from_dict(data_dict)
        assert restored.symbol == diagnostic.symbol
        assert restored.error_message == diagnostic.error_message


class TestPerformanceMetrics:
    """Test PerformanceMetrics model."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            memory_usage_mb=256.5,
            api_requests_made=150,
            api_rate_limit_remaining=850,
            cache_hit_rate=0.75,
            concurrent_requests=5,
            bottleneck_phase="data_fetch"
        )
        
        assert metrics.memory_usage_mb == 256.5
        assert metrics.api_requests_made == 150
        assert metrics.cache_hit_rate == 0.75
        assert metrics.bottleneck_phase == "data_fetch"
    
    def test_performance_metrics_serialization(self):
        """Test PerformanceMetrics JSON serialization."""
        metrics = PerformanceMetrics(
            memory_usage_mb=256.5,
            api_requests_made=150,
            api_rate_limit_remaining=850,
            cache_hit_rate=0.75,
            concurrent_requests=5,
            bottleneck_phase=None
        )
        
        data_dict = metrics.to_dict()
        restored = PerformanceMetrics.from_dict(data_dict)
        assert restored.memory_usage_mb == metrics.memory_usage_mb
        assert restored.bottleneck_phase is None


class TestSignalAnalysis:
    """Test SignalAnalysis model."""
    
    def test_signal_analysis_creation(self):
        """Test creating SignalAnalysis instance."""
        analysis = SignalAnalysis(
            signals_found=3,
            symbols_meeting_partial_criteria={
                "AAPL": ["ema_rising", "polar_formation"],
                "GOOGL": ["ema_rising"]
            },
            rejection_reasons={
                "fomo_filter": ["MSFT", "TSLA"],
                "no_htf_confirmation": ["NVDA"]
            },
            confidence_distribution={
                "0.8-1.0": 2,
                "0.6-0.8": 1,
                "0.4-0.6": 0
            }
        )
        
        assert analysis.signals_found == 3
        assert "AAPL" in analysis.symbols_meeting_partial_criteria
        assert "fomo_filter" in analysis.rejection_reasons
        assert analysis.confidence_distribution["0.8-1.0"] == 2
    
    def test_signal_analysis_serialization(self):
        """Test SignalAnalysis JSON serialization."""
        analysis = SignalAnalysis(
            signals_found=1,
            symbols_meeting_partial_criteria={"AAPL": ["ema_rising"]},
            rejection_reasons={"fomo_filter": ["MSFT"]},
            confidence_distribution={"0.8-1.0": 1}
        )
        
        data_dict = analysis.to_dict()
        restored = SignalAnalysis.from_dict(data_dict)
        assert restored.signals_found == analysis.signals_found
        assert restored.symbols_meeting_partial_criteria == analysis.symbols_meeting_partial_criteria


class TestDataQualityMetrics:
    """Test DataQualityMetrics model."""
    
    def test_data_quality_metrics_creation(self):
        """Test creating DataQualityMetrics instance."""
        metrics = DataQualityMetrics(
            total_data_points=1500,
            success_rate=0.85,
            average_fetch_time=2.3,
            data_completeness=0.92,
            quality_score=0.88
        )
        
        assert metrics.total_data_points == 1500
        assert metrics.success_rate == 0.85
        assert metrics.quality_score == 0.88
    
    def test_data_quality_metrics_serialization(self):
        """Test DataQualityMetrics JSON serialization."""
        metrics = DataQualityMetrics(
            total_data_points=1500,
            success_rate=0.85,
            average_fetch_time=2.3,
            data_completeness=0.92,
            quality_score=0.88
        )
        
        data_dict = metrics.to_dict()
        restored = DataQualityMetrics.from_dict(data_dict)
        assert restored.total_data_points == metrics.total_data_points
        assert restored.quality_score == metrics.quality_score


class TestEnhancedScanDiagnostics:
    """Test EnhancedScanDiagnostics model."""
    
    def test_enhanced_scan_diagnostics_creation(self):
        """Test creating EnhancedScanDiagnostics instance."""
        symbol_diagnostic = SymbolDiagnostic(
            symbol="AAPL",
            status="success",
            data_points_1m=390,
            data_points_15m=26,
            timeframe_coverage={"1m": True, "15m": True},
            error_message=None,
            fetch_time=1.2,
            processing_time=0.3
        )
        
        performance_metrics = PerformanceMetrics(
            memory_usage_mb=256.5,
            api_requests_made=150,
            api_rate_limit_remaining=850,
            cache_hit_rate=0.75,
            concurrent_requests=5,
            bottleneck_phase=None
        )
        
        signal_analysis = SignalAnalysis(
            signals_found=1,
            symbols_meeting_partial_criteria={"AAPL": ["ema_rising"]},
            rejection_reasons={},
            confidence_distribution={"0.8-1.0": 1}
        )
        
        data_quality = DataQualityMetrics(
            total_data_points=416,
            success_rate=1.0,
            average_fetch_time=1.2,
            data_completeness=1.0,
            quality_score=0.95
        )
        
        settings = AlgorithmSettings()
        
        diagnostics = EnhancedScanDiagnostics(
            symbols_with_data=["AAPL"],
            symbols_without_data=[],
            symbols_with_errors={},
            data_fetch_time=1.2,
            algorithm_time=0.3,
            total_data_points={"AAPL": 416},
            error_summary={},
            symbol_details={"AAPL": symbol_diagnostic},
            performance_metrics=performance_metrics,
            signal_analysis=signal_analysis,
            data_quality_metrics=data_quality,
            settings_snapshot=settings
        )
        
        assert len(diagnostics.symbols_with_data) == 1
        assert "AAPL" in diagnostics.symbol_details
        assert diagnostics.data_quality_metrics.quality_score == 0.95
    
    def test_enhanced_scan_diagnostics_serialization(self):
        """Test EnhancedScanDiagnostics JSON serialization."""
        # Create minimal diagnostics for testing
        symbol_diagnostic = SymbolDiagnostic(
            symbol="AAPL", status="success", data_points_1m=390, data_points_15m=26,
            timeframe_coverage={"1m": True}, error_message=None, fetch_time=1.0, processing_time=0.1
        )
        
        diagnostics = EnhancedScanDiagnostics(
            symbols_with_data=["AAPL"],
            symbols_without_data=[],
            symbols_with_errors={},
            data_fetch_time=1.0,
            algorithm_time=0.1,
            total_data_points={"AAPL": 416},
            error_summary={},
            symbol_details={"AAPL": symbol_diagnostic},
            performance_metrics=PerformanceMetrics(
                memory_usage_mb=100.0, api_requests_made=1, api_rate_limit_remaining=999,
                cache_hit_rate=0.0, concurrent_requests=1, bottleneck_phase=None
            ),
            signal_analysis=SignalAnalysis(
                signals_found=0, symbols_meeting_partial_criteria={},
                rejection_reasons={}, confidence_distribution={}
            ),
            data_quality_metrics=DataQualityMetrics(
                total_data_points=416, success_rate=1.0, average_fetch_time=1.0,
                data_completeness=1.0, quality_score=1.0
            ),
            settings_snapshot=AlgorithmSettings()
        )
        
        # Test serialization round trip
        json_str = diagnostics.to_json()
        restored = EnhancedScanDiagnostics.from_json(json_str)
        assert restored.symbols_with_data == diagnostics.symbols_with_data
        assert "AAPL" in restored.symbol_details
        assert restored.symbol_details["AAPL"].symbol == "AAPL"


class TestEnhancedScanResult:
    """Test EnhancedScanResult model."""
    
    def test_enhanced_scan_result_creation(self):
        """Test creating EnhancedScanResult instance."""
        settings = AlgorithmSettings()
        
        # Create minimal enhanced diagnostics
        diagnostics = EnhancedScanDiagnostics(
            symbols_with_data=["AAPL"],
            symbols_without_data=[],
            symbols_with_errors={},
            data_fetch_time=1.0,
            algorithm_time=0.1,
            total_data_points={"AAPL": 416},
            error_summary={},
            symbol_details={},
            performance_metrics=PerformanceMetrics(
                memory_usage_mb=100.0, api_requests_made=1, api_rate_limit_remaining=999,
                cache_hit_rate=0.0, concurrent_requests=1, bottleneck_phase=None
            ),
            signal_analysis=SignalAnalysis(
                signals_found=0, symbols_meeting_partial_criteria={},
                rejection_reasons={}, confidence_distribution={}
            ),
            data_quality_metrics=DataQualityMetrics(
                total_data_points=416, success_rate=1.0, average_fetch_time=1.0,
                data_completeness=1.0, quality_score=0.95
            ),
            settings_snapshot=settings
        )
        
        result = EnhancedScanResult(
            id="test-scan-1",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            symbols_scanned=["AAPL"],
            signals_found=[],
            settings_used=settings,
            execution_time=1.1,
            enhanced_diagnostics=diagnostics,
            data_quality_score=0.95
        )
        
        assert result.id == "test-scan-1"
        assert result.data_quality_score == 0.95
        assert result.enhanced_diagnostics is not None
        assert result.enhanced_diagnostics.data_quality_metrics.quality_score == 0.95


class TestScanComparison:
    """Test ScanComparison model."""
    
    def test_scan_comparison_creation(self):
        """Test creating ScanComparison instance."""
        comparison = ScanComparison(
            scan_ids=["scan-1", "scan-2"],
            settings_differences={
                "scan-1": {"atr_multiplier": 2.0},
                "scan-2": {"atr_multiplier": 3.0}
            },
            performance_trends={
                "execution_time": [2.1, 1.8],
                "quality_score": [0.85, 0.92]
            },
            symbol_status_changes={
                "AAPL": {"scan-1": "success", "scan-2": "success"},
                "GOOGL": {"scan-1": "error", "scan-2": "success"}
            },
            insights=[
                "Increased ATR multiplier improved quality score",
                "GOOGL data issue resolved in scan-2"
            ]
        )
        
        assert len(comparison.scan_ids) == 2
        assert comparison.settings_differences["scan-1"]["atr_multiplier"] == 2.0
        assert len(comparison.insights) == 2


class TestExportRequest:
    """Test ExportRequest model."""
    
    def test_export_request_creation(self):
        """Test creating ExportRequest instance."""
        request = ExportRequest(
            scan_ids=["scan-1", "scan-2"],
            format="csv",
            include_diagnostics=True,
            include_symbols=True,
            include_errors=False,
            date_range_start=datetime(2024, 1, 1),
            date_range_end=datetime(2024, 1, 31)
        )
        
        assert len(request.scan_ids) == 2
        assert request.format == "csv"
        assert request.include_diagnostics is True
        assert request.include_errors is False


class TestHistoryFilters:
    """Test HistoryFilters model."""
    
    def test_history_filters_creation(self):
        """Test creating HistoryFilters instance."""
        filters = HistoryFilters(
            date_range_start=datetime(2024, 1, 1),
            date_range_end=datetime(2024, 1, 31),
            scan_status="completed",
            min_symbols=5,
            max_symbols=50,
            min_quality_score=0.8,
            search_text="AAPL"
        )
        
        assert filters.scan_status == "completed"
        assert filters.min_symbols == 5
        assert filters.min_quality_score == 0.8
        assert filters.search_text == "AAPL"
    
    def test_history_filters_serialization(self):
        """Test HistoryFilters JSON serialization."""
        filters = HistoryFilters(
            scan_status="completed",
            min_quality_score=0.8
        )
        
        data_dict = filters.to_dict()
        restored = HistoryFilters.from_dict(data_dict)
        assert restored.scan_status == filters.scan_status
        assert restored.min_quality_score == filters.min_quality_score