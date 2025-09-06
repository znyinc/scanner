"""
Enhanced history API endpoints for diagnostic data.
Provides comprehensive scan history with detailed diagnostics, comparison, and export functionality.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import io
import csv
import json
import tempfile
import os

from ..services.scanner_service import ScannerService
from ..services.history_service import HistoryService
from ..services.export_service import ExportService
from ..services.comparison_service import ComparisonService
from ..models.pydantic_models import (
    EnhancedScanResultModel, ScanComparisonModel, ExportRequestModel, 
    HistoryFiltersModel, ExportFormat, ScanStatus
)
from ..models.enhanced_diagnostics import HistoryFilters, ExportRequest
from ..utils.validation import GeneralValidator
from ..utils.error_handling import (
    ErrorHandler, ValidationError, handle_errors, ErrorContext,
    StockScannerError
)

router = APIRouter(prefix="/history", tags=["history"])


class EnhancedHistoryResponse(BaseModel):
    """Response model for enhanced scan history."""
    results: List[EnhancedScanResultModel]
    total_count: int
    filtered_count: int
    has_more: bool


class DiagnosticDetailResponse(BaseModel):
    """Response model for detailed diagnostic information."""
    scan_id: str
    enhanced_diagnostics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    signal_analysis: Dict[str, Any]
    data_quality_score: Optional[float]


@router.get("/scan-history", response_model=EnhancedHistoryResponse)
async def get_enhanced_scan_history(
    request: Request,
    # Date filters
    start_date: Optional[datetime] = Query(None, description="Filter scans from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter scans until this date"),
    
    # Status and quality filters
    scan_status: Optional[ScanStatus] = Query(None, description="Filter by scan status"),
    min_quality_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum data quality score"),
    max_quality_score: Optional[float] = Query(None, ge=0, le=1, description="Maximum data quality score"),
    
    # Symbol and execution filters
    min_symbols: Optional[int] = Query(None, ge=0, description="Minimum number of symbols scanned"),
    max_symbols: Optional[int] = Query(None, ge=0, description="Maximum number of symbols scanned"),
    min_execution_time: Optional[float] = Query(None, ge=0, description="Minimum execution time in seconds"),
    max_execution_time: Optional[float] = Query(None, ge=0, description="Maximum execution time in seconds"),
    
    # Search and pagination
    search_text: Optional[str] = Query(None, max_length=255, description="Search in symbols, errors, and settings"),
    include_diagnostics: bool = Query(True, description="Include enhanced diagnostic data"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Retrieve enhanced scan history with comprehensive filtering and diagnostic details.
    
    - **start_date/end_date**: Filter scans by date range
    - **scan_status**: Filter by completion status (completed, failed, partial)
    - **min_quality_score/max_quality_score**: Filter by data quality score (0.0-1.0)
    - **min_symbols/max_symbols**: Filter by number of symbols scanned
    - **min_execution_time/max_execution_time**: Filter by execution time
    - **search_text**: Search across symbols, error messages, and settings
    - **include_diagnostics**: Include detailed diagnostic information
    - **limit/offset**: Pagination controls
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("get_enhanced_scan_history", request_id=request_id):
            # Validate pagination
            pagination_validation = GeneralValidator.validate_pagination(limit, offset)
            if not pagination_validation.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in pagination_validation.errors]
                raise ValidationError(
                    message=f"Pagination validation failed: {'; '.join(error_messages)}",
                    recovery_suggestions=[
                        "Ensure limit is between 1 and 500",
                        "Ensure offset is not negative"
                    ]
                )
            
            # Validate quality score ranges
            if min_quality_score is not None and max_quality_score is not None:
                if min_quality_score > max_quality_score:
                    raise ValidationError(
                        message="Minimum quality score cannot be greater than maximum quality score",
                        recovery_suggestions=["Check quality score range values"]
                    )
            
            # Validate symbol count ranges
            if min_symbols is not None and max_symbols is not None:
                if min_symbols > max_symbols:
                    raise ValidationError(
                        message="Minimum symbols cannot be greater than maximum symbols",
                        recovery_suggestions=["Check symbol count range values"]
                    )
            
            # Validate execution time ranges
            if min_execution_time is not None and max_execution_time is not None:
                if min_execution_time > max_execution_time:
                    raise ValidationError(
                        message="Minimum execution time cannot be greater than maximum execution time",
                        recovery_suggestions=["Check execution time range values"]
                    )
            
            # Create filters
            filters = HistoryFilters(
                date_range_start=start_date,
                date_range_end=end_date,
                scan_status=scan_status.value if scan_status else None,
                min_symbols=min_symbols,
                max_symbols=max_symbols,
                min_execution_time=min_execution_time,
                max_execution_time=max_execution_time,
                min_quality_score=min_quality_score,
                max_quality_score=max_quality_score,
                search_text=search_text
            )
            
            # Initialize history service
            history_service = HistoryService()
            
            # Get enhanced scan history
            results, total_count = await history_service.get_enhanced_scan_history(
                filters=filters,
                include_diagnostics=include_diagnostics,
                limit=limit,
                offset=offset
            )
            
            # Convert to response models
            enhanced_results = []
            for result in results:
                # Convert settings to dict
                settings_dict = result.settings_used.to_dict() if hasattr(result.settings_used, 'to_dict') else result.settings_used.__dict__
                
                # Convert enhanced diagnostics to dict if present
                enhanced_diag_dict = None
                if result.enhanced_diagnostics:
                    if hasattr(result.enhanced_diagnostics, 'to_dict'):
                        enhanced_diag_dict = result.enhanced_diagnostics.to_dict()
                    else:
                        enhanced_diag_dict = result.enhanced_diagnostics.__dict__
                
                # Normalize data quality score to 0-1 range if needed
                quality_score = result.data_quality_score
                if quality_score is not None and quality_score > 1.0:
                    quality_score = quality_score / 100.0  # Convert from 0-100 to 0-1 scale
                
                enhanced_result = EnhancedScanResultModel(
                    id=result.id,
                    timestamp=result.timestamp,
                    symbols_scanned=result.symbols_scanned,
                    signals_found=[signal.to_dict() for signal in result.signals_found],
                    settings_used=settings_dict,
                    execution_time=result.execution_time,
                    enhanced_diagnostics=enhanced_diag_dict,
                    scan_status=result.scan_status,
                    error_message=result.error_message,
                    data_quality_score=quality_score
                )
                enhanced_results.append(enhanced_result)
            
            return EnhancedHistoryResponse(
                results=enhanced_results,
                total_count=total_count,
                filtered_count=len(enhanced_results),
                has_more=(offset + len(enhanced_results)) < total_count
            )
            
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except StockScannerError:
        raise
    except Exception as exc:
        error = ErrorHandler.handle_exception(exc, {
            "operation": "get_enhanced_scan_history",
            "request_id": request_id
        })
        ErrorHandler.log_error(error, request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve enhanced scan history: {str(exc)}"
        )


@router.get("/scan-history/{scan_id}/diagnostics", response_model=DiagnosticDetailResponse)
async def get_scan_diagnostics(
    scan_id: str,
    request: Request
):
    """
    Get detailed diagnostic information for a specific scan.
    
    - **scan_id**: Unique identifier of the scan
    
    Returns comprehensive diagnostic details including:
    - Enhanced diagnostic data with symbol-level details
    - Performance metrics and bottleneck analysis
    - Signal analysis with rejection reasons
    - Data quality scores and metrics
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("get_scan_diagnostics", request_id=request_id, scan_id=scan_id):
            # Validate scan ID format
            try:
                uuid.UUID(scan_id)
            except ValueError:
                raise ValidationError(
                    message="Invalid scan ID format",
                    recovery_suggestions=["Provide a valid UUID format scan ID"]
                )
            
            # Initialize history service
            history_service = HistoryService()
            
            # Get detailed diagnostics
            diagnostics = await history_service.get_scan_diagnostics(scan_id)
            
            if not diagnostics:
                raise HTTPException(
                    status_code=404,
                    detail=f"Scan with ID {scan_id} not found or has no diagnostic data"
                )
            
            # Normalize data quality score
            quality_score = diagnostics.data_quality_score
            if quality_score is not None and quality_score > 1.0:
                quality_score = quality_score / 100.0
            
            return DiagnosticDetailResponse(
                scan_id=scan_id,
                enhanced_diagnostics=diagnostics.enhanced_diagnostics.to_dict() if diagnostics.enhanced_diagnostics else {},
                performance_metrics=diagnostics.enhanced_diagnostics.performance_metrics.to_dict() if diagnostics.enhanced_diagnostics and diagnostics.enhanced_diagnostics.performance_metrics else {},
                signal_analysis=diagnostics.enhanced_diagnostics.signal_analysis.to_dict() if diagnostics.enhanced_diagnostics and diagnostics.enhanced_diagnostics.signal_analysis else {},
                data_quality_score=quality_score
            )
            
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        error = ErrorHandler.handle_exception(exc, {
            "operation": "get_scan_diagnostics",
            "request_id": request_id,
            "scan_id": scan_id
        })
        ErrorHandler.log_error(error, request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve scan diagnostics: {str(exc)}"
        )


class ComparisonRequest(BaseModel):
    """Request model for scan comparison."""
    scan_ids: List[str] = Field(..., min_length=2, max_length=10, description="Scan IDs to compare")


@router.post("/scan-history/compare", response_model=ScanComparisonModel)
async def compare_scans(
    comparison_request: ComparisonRequest,
    request: Request = None
):
    """
    Compare multiple scans side-by-side to identify differences and trends.
    
    - **scan_ids**: List of 2-10 scan IDs to compare
    
    Returns detailed comparison including:
    - Settings differences between scans
    - Performance trends and changes
    - Symbol status changes across scans
    - Generated insights about significant differences
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("compare_scans", request_id=request_id, scan_count=len(comparison_request.scan_ids)):
            # Validate scan IDs
            if len(comparison_request.scan_ids) < 2:
                raise ValidationError(
                    message="At least 2 scan IDs are required for comparison",
                    recovery_suggestions=["Provide at least 2 valid scan IDs"]
                )
            
            if len(comparison_request.scan_ids) > 10:
                raise ValidationError(
                    message="Maximum 10 scans can be compared at once",
                    recovery_suggestions=["Reduce the number of scans to compare"]
                )
            
            # Validate scan ID formats
            for scan_id in comparison_request.scan_ids:
                try:
                    uuid.UUID(scan_id)
                except ValueError:
                    raise ValidationError(
                        message=f"Invalid scan ID format: {scan_id}",
                        recovery_suggestions=["Provide valid UUID format scan IDs"]
                    )
            
            # Check for duplicate scan IDs
            if len(set(comparison_request.scan_ids)) != len(comparison_request.scan_ids):
                raise ValidationError(
                    message="Duplicate scan IDs are not allowed",
                    recovery_suggestions=["Remove duplicate scan IDs from the list"]
                )
            
            # Initialize comparison service
            comparison_service = ComparisonService()
            
            # Perform comparison
            comparison_result = await comparison_service.compare_scans(comparison_request.scan_ids)
            
            if not comparison_result:
                raise HTTPException(
                    status_code=404,
                    detail="One or more scans not found or insufficient data for comparison"
                )
            
            return ScanComparisonModel(
                scan_ids=comparison_result.scan_ids,
                settings_differences=comparison_result.settings_differences,
                performance_trends=comparison_result.performance_trends,
                symbol_status_changes=comparison_result.symbol_status_changes,
                insights=comparison_result.insights
            )
            
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        error = ErrorHandler.handle_exception(exc, {
            "operation": "compare_scans",
            "request_id": request_id,
            "scan_ids": comparison_request.scan_ids if comparison_request else []
        })
        ErrorHandler.log_error(error, request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare scans: {str(exc)}"
        )


@router.post("/scan-history/export")
async def export_scan_data(
    export_request: ExportRequestModel,
    background_tasks: BackgroundTasks,
    request: Request = None
):
    """
    Export scan data in various formats (CSV, JSON, Excel).
    
    - **scan_ids**: List of scan IDs to export
    - **format**: Export format (csv, json, excel)
    - **include_diagnostics**: Include diagnostic data in export
    - **include_symbols**: Include symbol-level data
    - **include_errors**: Include error information
    - **date_range_start/end**: Optional date range filtering
    
    Returns downloadable file with exported data.
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("export_scan_data", request_id=request_id, 
                         format=export_request.format, scan_count=len(export_request.scan_ids)):
            
            # Validate scan IDs
            if not export_request.scan_ids:
                raise ValidationError(
                    message="At least one scan ID is required for export",
                    recovery_suggestions=["Provide valid scan IDs to export"]
                )
            
            if len(export_request.scan_ids) > 100:
                raise ValidationError(
                    message="Maximum 100 scans can be exported at once",
                    recovery_suggestions=["Reduce the number of scans to export"]
                )
            
            # Validate scan ID formats
            for scan_id in export_request.scan_ids:
                try:
                    uuid.UUID(scan_id)
                except ValueError:
                    raise ValidationError(
                        message=f"Invalid scan ID format: {scan_id}",
                        recovery_suggestions=["Provide valid UUID format scan IDs"]
                    )
            
            # Initialize export service
            export_service = ExportService()
            
            # Convert to domain model
            domain_export_request = ExportRequest(
                scan_ids=export_request.scan_ids,
                format=export_request.format.value,
                include_diagnostics=export_request.include_diagnostics,
                include_symbols=export_request.include_symbols,
                include_errors=export_request.include_errors,
                date_range_start=export_request.date_range_start,
                date_range_end=export_request.date_range_end
            )
            
            # Generate export file
            export_result = await export_service.export_scan_data(domain_export_request)
            
            if not export_result or not os.path.exists(export_result.file_path):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate export file"
                )
            
            # Determine content type and filename
            content_type_map = {
                "csv": "text/csv",
                "json": "application/json",
                "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
            extension_map = {
                "csv": "csv",
                "json": "json", 
                "excel": "xlsx"
            }
            
            content_type = content_type_map.get(export_request.format.value, "application/octet-stream")
            extension = extension_map.get(export_request.format.value, "bin")
            filename = f"scan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
            
            # Schedule cleanup of temporary file
            background_tasks.add_task(export_service.cleanup_export_file, export_result.file_path)
            
            return FileResponse(
                path=export_result.file_path,
                filename=filename,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Export-Record-Count": str(export_result.record_count),
                    "X-Export-File-Size": str(export_result.file_size)
                }
            )
            
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        error = ErrorHandler.handle_exception(exc, {
            "operation": "export_scan_data",
            "request_id": request_id,
            "format": export_request.format if export_request else "unknown"
        })
        ErrorHandler.log_error(error, request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export scan data: {str(exc)}"
        )


@router.get("/scan-history/stats")
async def get_scan_history_stats(
    start_date: Optional[datetime] = Query(None, description="Stats from this date"),
    end_date: Optional[datetime] = Query(None, description="Stats until this date"),
    request: Request = None
):
    """
    Get aggregate statistics for scan history.
    
    - **start_date/end_date**: Optional date range for statistics
    
    Returns summary statistics including:
    - Total scans and success rates
    - Average execution times and quality scores
    - Most common errors and symbols
    - Performance trends over time
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("get_scan_history_stats", request_id=request_id):
            # Initialize history service
            history_service = HistoryService()
            
            # Get statistics
            stats = await history_service.get_scan_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
            return stats
            
    except Exception as exc:
        error = ErrorHandler.handle_exception(exc, {
            "operation": "get_scan_history_stats",
            "request_id": request_id
        })
        ErrorHandler.log_error(error, request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve scan statistics: {str(exc)}"
        )