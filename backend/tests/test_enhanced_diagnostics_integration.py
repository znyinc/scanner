"""
Integration tests for enhanced diagnostic models with database.
"""
import pytest
from datetime import datetime
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
    EnhancedScanResult
)
from app.models.signals import AlgorithmSettings
from app.models.database_models import ScanResultDB


class TestEnhancedDiagnosticsIntegration:
    """Test enhanced diagnostics integration with database."""
    
    def test_enhanced_scan_result_database_storage(self):
        """Test storing enhanced scan result in database."""
        # Create enhanced diagnostics
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
        
        enhanced_diagnostics = EnhancedScanDiagnostics(
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
        
        # Create database record
        scan_result_db = ScanResultDB(
            timestamp=datetime.now(),
            symbols_scanned=["AAPL"],
            signals_found=[],
            settings_used=settings.to_dict(),
            execution_time=1.5,
            enhanced_diagnostics=enhanced_diagnostics.to_dict(),
            performance_metrics=performance_metrics.to_dict(),
            signal_analysis=signal_analysis.to_dict(),
            data_quality_score=0.95,
            scan_status="completed"
        )
        
        # Test that the data can be serialized to JSON (database storage)
        enhanced_diagnostics_json = json.dumps(enhanced_diagnostics.to_dict())
        performance_metrics_json = json.dumps(performance_metrics.to_dict())
        signal_analysis_json = json.dumps(signal_analysis.to_dict())
        
        # Test that the data can be deserialized from JSON
        restored_diagnostics = EnhancedScanDiagnostics.from_dict(
            json.loads(enhanced_diagnostics_json)
        )
        restored_performance = PerformanceMetrics.from_dict(
            json.loads(performance_metrics_json)
        )
        restored_signal_analysis = SignalAnalysis.from_dict(
            json.loads(signal_analysis_json)
        )
        
        # Verify data integrity
        assert restored_diagnostics.symbols_with_data == enhanced_diagnostics.symbols_with_data
        assert restored_diagnostics.data_quality_metrics.quality_score == 0.95
        assert "AAPL" in restored_diagnostics.symbol_details
        assert restored_diagnostics.symbol_details["AAPL"].symbol == "AAPL"
        
        assert restored_performance.memory_usage_mb == performance_metrics.memory_usage_mb
        assert restored_performance.cache_hit_rate == performance_metrics.cache_hit_rate
        
        assert restored_signal_analysis.signals_found == signal_analysis.signals_found
        assert restored_signal_analysis.confidence_distribution == signal_analysis.confidence_distribution
        
        print("✅ Enhanced diagnostics database integration test passed!")
    
    def test_enhanced_scan_result_creation_and_serialization(self):
        """Test creating and serializing enhanced scan result."""
        settings = AlgorithmSettings(atr_multiplier=2.5)
        
        # Create minimal enhanced diagnostics for testing
        enhanced_diagnostics = EnhancedScanDiagnostics(
            symbols_with_data=["AAPL", "GOOGL"],
            symbols_without_data=["INVALID"],
            symbols_with_errors={"TSLA": "API timeout"},
            data_fetch_time=2.1,
            algorithm_time=0.4,
            total_data_points={"AAPL": 390, "GOOGL": 385},
            error_summary={"timeout": 1},
            symbol_details={},
            performance_metrics=PerformanceMetrics(
                memory_usage_mb=128.0, api_requests_made=3, api_rate_limit_remaining=997,
                cache_hit_rate=0.33, concurrent_requests=2, bottleneck_phase="data_fetch"
            ),
            signal_analysis=SignalAnalysis(
                signals_found=2, symbols_meeting_partial_criteria={"AAPL": ["ema_rising"]},
                rejection_reasons={"fomo_filter": ["GOOGL"]}, confidence_distribution={"0.8-1.0": 2}
            ),
            data_quality_metrics=DataQualityMetrics(
                total_data_points=775, success_rate=0.67, average_fetch_time=0.7,
                data_completeness=0.85, quality_score=0.76
            ),
            settings_snapshot=settings
        )
        
        enhanced_result = EnhancedScanResult(
            id="test-enhanced-scan-1",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            symbols_scanned=["AAPL", "GOOGL", "INVALID", "TSLA"],
            signals_found=[],
            settings_used=settings,
            execution_time=2.5,
            enhanced_diagnostics=enhanced_diagnostics,
            data_quality_score=0.76
        )
        
        # Test serialization
        result_dict = enhanced_result.to_dict()
        assert result_dict["id"] == "test-enhanced-scan-1"
        assert result_dict["data_quality_score"] == 0.76
        assert "enhanced_diagnostics" in result_dict
        
        # Test JSON serialization
        result_json = enhanced_result.to_json()
        restored_result = EnhancedScanResult.from_json(result_json)
        
        assert restored_result.id == enhanced_result.id
        assert restored_result.data_quality_score == enhanced_result.data_quality_score
        assert restored_result.enhanced_diagnostics is not None
        assert restored_result.enhanced_diagnostics.data_quality_metrics.quality_score == 0.76
        
        print("✅ Enhanced scan result creation and serialization test passed!")
    
    def test_pydantic_model_validation_integration(self):
        """Test that Pydantic models work correctly with the dataclass models."""
        from app.models.pydantic_models import (
            EnhancedScanDiagnosticsModel,
            SymbolDiagnosticModel,
            PerformanceMetricsModel
        )
        
        # Create dataclass instance
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
        
        # Test Pydantic validation
        pydantic_symbol = SymbolDiagnosticModel(**symbol_diagnostic.to_dict())
        assert pydantic_symbol.symbol == "AAPL"
        assert pydantic_symbol.status == "success"
        
        # Test invalid data validation
        with pytest.raises(Exception):  # Should raise ValidationError
            SymbolDiagnosticModel(
                symbol="AAPL",
                status="invalid_status",  # Invalid status
                data_points_1m=390,
                data_points_15m=26,
                timeframe_coverage={"1m": True},
                fetch_time=1.2,
                processing_time=0.3
            )
        
        print("✅ Pydantic model validation integration test passed!")