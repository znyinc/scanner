"""
Pydantic models for data validation and API serialization.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class SymbolStatus(str, Enum):
    """Enumeration for symbol processing status."""
    SUCCESS = "success"
    NO_DATA = "no_data"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


class ScanStatus(str, Enum):
    """Enumeration for scan status."""
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ExportFormat(str, Enum):
    """Enumeration for export formats."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class SymbolDiagnosticModel(BaseModel):
    """Pydantic model for symbol diagnostic information."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    status: SymbolStatus = Field(..., description="Processing status of the symbol")
    data_points_1m: int = Field(ge=0, description="Number of 1-minute data points")
    data_points_15m: int = Field(ge=0, description="Number of 15-minute data points")
    timeframe_coverage: Dict[str, bool] = Field(..., description="Timeframe data availability")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    fetch_time: float = Field(ge=0, description="Time taken to fetch data in seconds")
    processing_time: float = Field(ge=0, description="Time taken to process data in seconds")

    @field_validator('timeframe_coverage')
    @classmethod
    def validate_timeframe_coverage(cls, v):
        """Validate timeframe coverage dictionary."""
        valid_timeframes = {'1m', '15m', '4h', '1d'}
        if not all(tf in valid_timeframes for tf in v.keys()):
            raise ValueError(f"Invalid timeframes. Must be one of: {valid_timeframes}")
        return v

    model_config = ConfigDict(use_enum_values=True)


class PerformanceMetricsModel(BaseModel):
    """Pydantic model for system performance metrics."""
    memory_usage_mb: float = Field(ge=0, description="Memory usage in megabytes")
    api_requests_made: int = Field(ge=0, description="Number of API requests made")
    api_rate_limit_remaining: int = Field(ge=0, description="Remaining API rate limit")
    cache_hit_rate: float = Field(ge=0, le=1, description="Cache hit rate as percentage")
    concurrent_requests: int = Field(ge=0, description="Number of concurrent requests")
    bottleneck_phase: Optional[str] = Field(None, description="Phase that caused bottleneck")

    @field_validator('cache_hit_rate')
    @classmethod
    def validate_cache_hit_rate(cls, v):
        """Validate cache hit rate is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Cache hit rate must be between 0 and 1")
        return v


class SignalAnalysisModel(BaseModel):
    """Pydantic model for signal analysis."""
    signals_found: int = Field(ge=0, description="Number of signals found")
    symbols_meeting_partial_criteria: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Symbols meeting partial criteria"
    )
    rejection_reasons: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Rejection reasons grouped by type"
    )
    confidence_distribution: Dict[str, int] = Field(
        default_factory=dict, 
        description="Distribution of confidence scores"
    )

    @field_validator('confidence_distribution')
    @classmethod
    def validate_confidence_distribution(cls, v):
        """Validate confidence distribution keys are valid ranges."""
        valid_ranges = {'0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0', 'low', 'medium', 'high'}
        if v and not all(key in valid_ranges for key in v.keys()):
            raise ValueError(f"Invalid confidence ranges. Must be one of: {valid_ranges}")
        return v


class DataQualityMetricsModel(BaseModel):
    """Pydantic model for data quality metrics."""
    total_data_points: int = Field(ge=0, description="Total number of data points")
    success_rate: float = Field(ge=0, le=1, description="Success rate as percentage")
    average_fetch_time: float = Field(ge=0, description="Average fetch time in seconds")
    data_completeness: float = Field(ge=0, le=1, description="Data completeness as percentage")
    quality_score: float = Field(ge=0, le=1, description="Overall quality score")

    @field_validator('success_rate', 'data_completeness')
    @classmethod
    def validate_percentage(cls, v):
        """Validate percentage values are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Percentage values must be between 0 and 1")
        return v
    
    @field_validator('quality_score')
    @classmethod
    def validate_quality_score(cls, v):
        """Validate quality score and normalize if needed."""
        if v is None:
            return v
        # If score is > 1, assume it's on 0-100 scale and normalize
        if v > 1:
            v = v / 100.0
        if not 0 <= v <= 1:
            raise ValueError("Quality score must be between 0 and 1")
        return v


class AlgorithmSettingsModel(BaseModel):
    """Pydantic model for algorithm settings."""
    atr_multiplier: float = Field(default=2.0, gt=0, description="ATR multiplier")
    ema5_rising_threshold: float = Field(default=0.02, ge=0, description="EMA5 rising threshold")
    ema8_rising_threshold: float = Field(default=0.01, ge=0, description="EMA8 rising threshold")
    ema21_rising_threshold: float = Field(default=0.005, ge=0, description="EMA21 rising threshold")
    volatility_filter: float = Field(default=1.5, gt=0, description="Volatility filter")
    fomo_filter: float = Field(default=1.0, gt=0, description="FOMO filter")
    higher_timeframe: str = Field(default="4h", description="Higher timeframe for confirmation")

    @field_validator('higher_timeframe')
    @classmethod
    def validate_higher_timeframe(cls, v):
        """Validate higher timeframe is valid."""
        valid_timeframes = {'1m', '2m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'}
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
        return v


class EnhancedScanDiagnosticsModel(BaseModel):
    """Pydantic model for enhanced scan diagnostics."""
    # Existing fields
    symbols_with_data: List[str] = Field(..., description="Symbols with successful data")
    symbols_without_data: List[str] = Field(..., description="Symbols without data")
    symbols_with_errors: Dict[str, str] = Field(..., description="Symbols with errors")
    data_fetch_time: float = Field(ge=0, description="Data fetch time in seconds")
    algorithm_time: float = Field(ge=0, description="Algorithm processing time in seconds")
    total_data_points: Dict[str, int] = Field(..., description="Data points per symbol")
    error_summary: Dict[str, int] = Field(..., description="Error summary by type")
    
    # Enhanced fields
    symbol_details: Dict[str, SymbolDiagnosticModel] = Field(
        ..., description="Detailed symbol diagnostics"
    )
    performance_metrics: PerformanceMetricsModel = Field(..., description="Performance metrics")
    signal_analysis: SignalAnalysisModel = Field(..., description="Signal analysis")
    data_quality_metrics: DataQualityMetricsModel = Field(..., description="Data quality metrics")
    settings_snapshot: AlgorithmSettingsModel = Field(..., description="Algorithm settings used")

    @field_validator('total_data_points')
    @classmethod
    def validate_total_data_points(cls, v):
        """Validate data points are non-negative."""
        if any(count < 0 for count in v.values()):
            raise ValueError("Data point counts must be non-negative")
        return v

    @field_validator('error_summary')
    @classmethod
    def validate_error_summary(cls, v):
        """Validate error summary counts are non-negative."""
        if any(count < 0 for count in v.values()):
            raise ValueError("Error counts must be non-negative")
        return v


class EnhancedScanResultModel(BaseModel):
    """Pydantic model for enhanced scan result."""
    id: str = Field(..., description="Unique scan identifier")
    timestamp: datetime = Field(..., description="Scan execution timestamp")
    symbols_scanned: List[str] = Field(..., description="List of symbols scanned")
    signals_found: List[Dict[str, Any]] = Field(..., description="Signals found during scan")
    settings_used: AlgorithmSettingsModel = Field(..., description="Algorithm settings used")
    execution_time: float = Field(ge=0, description="Total execution time in seconds")
    enhanced_diagnostics: Optional[EnhancedScanDiagnosticsModel] = Field(
        None, description="Enhanced diagnostic information"
    )
    scan_status: ScanStatus = Field(default=ScanStatus.COMPLETED, description="Scan status")
    error_message: Optional[str] = Field(None, description="Error message if scan failed")
    data_quality_score: Optional[float] = Field(
        None, ge=0, le=1, description="Overall data quality score"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ScanComparisonModel(BaseModel):
    """Pydantic model for scan comparison."""
    scan_ids: List[str] = Field(..., min_length=2, description="Scan IDs to compare")
    settings_differences: Dict[str, Dict[str, Any]] = Field(
        ..., description="Settings differences by scan"
    )
    performance_trends: Dict[str, List[float]] = Field(
        ..., description="Performance trends by metric"
    )
    symbol_status_changes: Dict[str, Dict[str, str]] = Field(
        ..., description="Symbol status changes between scans"
    )
    insights: List[str] = Field(..., description="Generated insights about differences")


class ExportRequestModel(BaseModel):
    """Pydantic model for export request."""
    scan_ids: List[str] = Field(..., min_length=1, description="Scan IDs to export")
    format: ExportFormat = Field(..., description="Export format")
    include_diagnostics: bool = Field(default=True, description="Include diagnostic data")
    include_symbols: bool = Field(default=True, description="Include symbol data")
    include_errors: bool = Field(default=True, description="Include error data")
    date_range_start: Optional[datetime] = Field(None, description="Start date for filtering")
    date_range_end: Optional[datetime] = Field(None, description="End date for filtering")

    @field_validator('date_range_end')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate end date is after start date."""
        if v and info.data.get('date_range_start'):
            if v <= info.data['date_range_start']:
                raise ValueError("End date must be after start date")
        return v

    model_config = ConfigDict(use_enum_values=True)


class HistoryFiltersModel(BaseModel):
    """Pydantic model for history filters."""
    date_range_start: Optional[datetime] = Field(None, description="Start date filter")
    date_range_end: Optional[datetime] = Field(None, description="End date filter")
    scan_status: Optional[ScanStatus] = Field(None, description="Scan status filter")
    min_symbols: Optional[int] = Field(None, ge=0, description="Minimum symbols filter")
    max_symbols: Optional[int] = Field(None, ge=0, description="Maximum symbols filter")
    min_execution_time: Optional[float] = Field(None, ge=0, description="Minimum execution time")
    max_execution_time: Optional[float] = Field(None, ge=0, description="Maximum execution time")
    min_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Minimum quality score")
    max_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Maximum quality score")
    search_text: Optional[str] = Field(None, max_length=255, description="Search text")

    @field_validator('max_symbols')
    @classmethod
    def validate_symbol_range(cls, v, info):
        """Validate max symbols is greater than min symbols."""
        if v and info.data.get('min_symbols'):
            if v <= info.data['min_symbols']:
                raise ValueError("Maximum symbols must be greater than minimum symbols")
        return v

    @field_validator('max_execution_time')
    @classmethod
    def validate_execution_time_range(cls, v, info):
        """Validate max execution time is greater than min execution time."""
        if v and info.data.get('min_execution_time'):
            if v <= info.data['min_execution_time']:
                raise ValueError("Maximum execution time must be greater than minimum execution time")
        return v

    @field_validator('max_quality_score')
    @classmethod
    def validate_quality_score_range(cls, v, info):
        """Validate max quality score is greater than min quality score."""
        if v and info.data.get('min_quality_score'):
            if v <= info.data['min_quality_score']:
                raise ValueError("Maximum quality score must be greater than minimum quality score")
        return v

    @field_validator('date_range_end')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate end date is after start date."""
        if v and info.data.get('date_range_start'):
            if v <= info.data['date_range_start']:
                raise ValueError("End date must be after start date")
        return v

    model_config = ConfigDict(use_enum_values=True)