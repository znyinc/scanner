"""
Enhanced diagnostic models for comprehensive scan analysis.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from .signals import AlgorithmSettings


@dataclass
class SymbolDiagnostic:
    """Detailed diagnostic information for a single symbol."""
    symbol: str
    status: str  # success, no_data, insufficient_data, error
    data_points_1m: int
    data_points_15m: int
    timeframe_coverage: Dict[str, bool]  # timeframe -> has_data
    error_message: Optional[str]
    fetch_time: float
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolDiagnostic':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class PerformanceMetrics:
    """System performance metrics during scan execution."""
    memory_usage_mb: float
    api_requests_made: int
    api_rate_limit_remaining: int
    cache_hit_rate: float
    concurrent_requests: int
    bottleneck_phase: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class SignalAnalysis:
    """Analysis of signal generation during scan."""
    signals_found: int
    symbols_meeting_partial_criteria: Dict[str, List[str]]  # symbol -> list of criteria met
    rejection_reasons: Dict[str, List[str]]  # reason -> list of symbols
    confidence_distribution: Dict[str, int]  # confidence_range -> count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignalAnalysis':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics."""
    total_data_points: int
    success_rate: float
    average_fetch_time: float
    data_completeness: float
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataQualityMetrics':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class EnhancedScanDiagnostics:
    """Comprehensive diagnostic information for a scan operation."""
    # Existing fields from ScanDiagnostics
    symbols_with_data: List[str]
    symbols_without_data: List[str]
    symbols_with_errors: Dict[str, str]  # symbol -> error message
    data_fetch_time: float
    algorithm_time: float
    total_data_points: Dict[str, int]  # symbol -> number of data points
    error_summary: Dict[str, int]  # error type -> count
    
    # New enhanced fields
    symbol_details: Dict[str, SymbolDiagnostic]
    performance_metrics: PerformanceMetrics
    signal_analysis: SignalAnalysis
    data_quality_metrics: DataQualityMetrics
    settings_snapshot: AlgorithmSettings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert nested objects
        data['symbol_details'] = {k: v.to_dict() for k, v in self.symbol_details.items()}
        data['performance_metrics'] = self.performance_metrics.to_dict()
        data['signal_analysis'] = self.signal_analysis.to_dict()
        data['data_quality_metrics'] = self.data_quality_metrics.to_dict()
        data['settings_snapshot'] = self.settings_snapshot.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedScanDiagnostics':
        """Create instance from dictionary."""
        data = data.copy()
        
        # Convert nested objects
        if 'symbol_details' in data:
            data['symbol_details'] = {
                k: SymbolDiagnostic.from_dict(v) 
                for k, v in data['symbol_details'].items()
            }
        
        if 'performance_metrics' in data:
            data['performance_metrics'] = PerformanceMetrics.from_dict(data['performance_metrics'])
        
        if 'signal_analysis' in data:
            data['signal_analysis'] = SignalAnalysis.from_dict(data['signal_analysis'])
        
        if 'data_quality_metrics' in data:
            data['data_quality_metrics'] = DataQualityMetrics.from_dict(data['data_quality_metrics'])
        
        if 'settings_snapshot' in data:
            data['settings_snapshot'] = AlgorithmSettings.from_dict(data['settings_snapshot'])
        
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'EnhancedScanDiagnostics':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class EnhancedScanResult:
    """Enhanced scan result with comprehensive diagnostics."""
    id: str
    timestamp: datetime
    symbols_scanned: List[str]
    signals_found: List[Any]  # Will be Signal objects
    settings_used: AlgorithmSettings
    execution_time: float
    enhanced_diagnostics: Optional[EnhancedScanDiagnostics] = None
    scan_status: str = "completed"  # completed, failed, partial
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        # signals_found will be handled by the calling code
        data['settings_used'] = self.settings_used.to_dict()
        if self.enhanced_diagnostics:
            data['enhanced_diagnostics'] = self.enhanced_diagnostics.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedScanResult':
        """Create instance from dictionary."""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data['settings_used'], dict):
            data['settings_used'] = AlgorithmSettings.from_dict(data['settings_used'])
        if 'enhanced_diagnostics' in data and data['enhanced_diagnostics']:
            data['enhanced_diagnostics'] = EnhancedScanDiagnostics.from_dict(data['enhanced_diagnostics'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'EnhancedScanResult':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ScanComparison:
    """Comparison result between multiple scans."""
    scan_ids: List[str]
    settings_differences: Dict[str, Dict[str, Any]]  # scan_id -> changed_settings
    performance_trends: Dict[str, List[float]]  # metric_name -> values_by_scan
    symbol_status_changes: Dict[str, Dict[str, str]]  # symbol -> scan_id -> status
    insights: List[str]  # Generated insights about differences
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanComparison':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ExportRequest:
    """Request parameters for exporting scan data."""
    scan_ids: List[str]
    format: str  # csv, json, excel
    include_diagnostics: bool = True
    include_symbols: bool = True
    include_errors: bool = True
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.date_range_start:
            data['date_range_start'] = self.date_range_start.isoformat()
        if self.date_range_end:
            data['date_range_end'] = self.date_range_end.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportRequest':
        """Create instance from dictionary."""
        data = data.copy()
        if 'date_range_start' in data and data['date_range_start']:
            data['date_range_start'] = datetime.fromisoformat(data['date_range_start'])
        if 'date_range_end' in data and data['date_range_end']:
            data['date_range_end'] = datetime.fromisoformat(data['date_range_end'])
        return cls(**data)


@dataclass
class HistoryFilters:
    """Filters for scan history queries."""
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    scan_status: Optional[str] = None
    min_symbols: Optional[int] = None
    max_symbols: Optional[int] = None
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    min_quality_score: Optional[float] = None
    max_quality_score: Optional[float] = None
    search_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.date_range_start:
            data['date_range_start'] = self.date_range_start.isoformat()
        if self.date_range_end:
            data['date_range_end'] = self.date_range_end.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryFilters':
        """Create instance from dictionary."""
        data = data.copy()
        if 'date_range_start' in data and data['date_range_start']:
            data['date_range_start'] = datetime.fromisoformat(data['date_range_start'])
        if 'date_range_end' in data and data['date_range_end']:
            data['date_range_end'] = datetime.fromisoformat(data['date_range_end'])
        return cls(**data)