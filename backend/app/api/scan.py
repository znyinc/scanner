"""
Scan API endpoints for stock scanning operations.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import uuid

from ..services.scanner_service import ScannerService, ScanFilters
from ..models.signals import AlgorithmSettings
from ..models.results import ScanResult
from ..utils.validation import StockSymbolValidator, AlgorithmSettingsValidator, GeneralValidator
from ..utils.error_handling import (
    ErrorHandler, ValidationError, handle_errors, ErrorContext,
    StockScannerError
)

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanRequest(BaseModel):
    """Request model for stock scanning."""
    symbols: List[str] = Field(..., description="List of stock symbols to scan")
    settings: Optional[dict] = Field(None, description="Algorithm settings override")


class ScanResponse(BaseModel):
    """Response model for scan results."""
    id: str
    timestamp: datetime
    symbols_scanned: List[str]
    signals_found: List[dict]
    settings_used: dict
    execution_time: float


@router.post("/", response_model=ScanResponse)
async def scan_stocks(request: ScanRequest, http_request: Request):
    """
    Initiate a stock scan using the EMA-ATR algorithm.
    
    - **symbols**: List of stock symbols to scan (1-100 symbols)
    - **settings**: Optional algorithm settings override
    
    Returns scan results with any signals found.
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("scan_stocks", request_id=request_id, symbols_count=len(request.symbols)):
            # Validate symbols
            symbol_validation = StockSymbolValidator.validate_symbols(request.symbols, max_symbols=100)
            if not symbol_validation.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in symbol_validation.errors]
                raise ValidationError(
                    message=f"Symbol validation failed: {'; '.join(error_messages)}",
                    recovery_suggestions=[
                        "Check symbol format (e.g., AAPL, MSFT)",
                        "Remove invalid symbols and try again",
                        "Ensure symbols are valid stock tickers"
                    ]
                )
            
            validated_symbols = symbol_validation.cleaned_data["symbols"]
            
            # Validate algorithm settings
            settings = AlgorithmSettings()
            if request.settings:
                settings_validation = AlgorithmSettingsValidator.validate_settings(request.settings)
                if not settings_validation.is_valid:
                    error_messages = [f"{error.field}: {error.message}" for error in settings_validation.errors]
                    raise ValidationError(
                        message=f"Settings validation failed: {'; '.join(error_messages)}",
                        recovery_suggestions=[
                            "Check parameter ranges in documentation",
                            "Use default values if unsure",
                            "Ensure all numeric values are valid"
                        ]
                    )
                
                # Create settings from validated data
                settings = AlgorithmSettings.from_dict(settings_validation.cleaned_data)
            
            # Initialize scanner service
            scanner_service = ScannerService()
            
            # Perform scan
            result = await scanner_service.scan_stocks(validated_symbols, settings)
            
            # Convert to response format
            return ScanResponse(
                id=result.id,
                timestamp=result.timestamp,
                symbols_scanned=result.symbols_scanned,
                signals_found=[signal.to_dict() for signal in result.signals_found],
                settings_used=result.settings_used.to_dict(),
                execution_time=result.execution_time
            )
            
    except StockScannerError:
        # Re-raise our custom errors
        raise
    except Exception as exc:
        # Handle unexpected errors
        error = ErrorHandler.handle_exception(exc, {
            "operation": "scan_stocks",
            "request_id": request_id,
            "symbols_count": len(request.symbols)
        })
        ErrorHandler.log_error(error, request_id)
        
        # Convert to HTTP exception
        error_response = ErrorHandler.create_error_response(error)
        raise HTTPException(
            status_code=500 if error.error_details.category.value == "system" else 400,
            detail=error_response["error"]
        )


@router.get("/history", response_model=List[ScanResponse])
async def get_scan_history(
    start_date: Optional[datetime] = Query(None, description="Filter scans from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter scans until this date"),
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols to filter by"),
    signal_types: Optional[str] = Query(None, description="Comma-separated list of signal types (long,short)"),
    min_confidence: Optional[float] = Query(None, description="Minimum signal confidence", ge=0.0, le=1.0),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
    offset: int = Query(0, description="Number of results to skip", ge=0)
):
    """
    Retrieve scan history with optional filtering.
    
    - **start_date**: Filter scans from this date
    - **end_date**: Filter scans until this date  
    - **symbols**: Comma-separated symbols to filter by
    - **signal_types**: Comma-separated signal types (long,short)
    - **min_confidence**: Minimum signal confidence (0.0-1.0)
    - **limit**: Maximum results (1-1000)
    - **offset**: Results to skip for pagination
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("get_scan_history", request_id=request_id):
            # Validate pagination parameters
            pagination_validation = GeneralValidator.validate_pagination(limit, offset)
            if not pagination_validation.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in pagination_validation.errors]
                raise ValidationError(
                    message=f"Pagination validation failed: {'; '.join(error_messages)}",
                    recovery_suggestions=[
                        "Ensure limit is between 1 and 1000",
                        "Ensure offset is not negative",
                        "Use reasonable pagination values"
                    ]
                )
            
            # Validate confidence range if provided
            if min_confidence is not None:
                confidence_validation = GeneralValidator.validate_confidence_range(min_confidence)
                if not confidence_validation.is_valid:
                    error_messages = [f"{error.field}: {error.message}" for error in confidence_validation.errors]
                    raise ValidationError(
                        message=f"Confidence validation failed: {'; '.join(error_messages)}",
                        recovery_suggestions=[
                            "Confidence must be between 0.0 and 1.0",
                            "Use decimal values like 0.5 for 50% confidence"
                        ]
                    )
            
            # Validate symbols if provided
            parsed_symbols = None
            if symbols:
                symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
                if symbol_list:
                    symbol_validation = StockSymbolValidator.validate_symbols(symbol_list, max_symbols=50)
                    if not symbol_validation.is_valid:
                        error_messages = [f"{error.field}: {error.message}" for error in symbol_validation.errors]
                        raise ValidationError(
                            message=f"Symbol filter validation failed: {'; '.join(error_messages)}",
                            recovery_suggestions=[
                                "Check symbol format in filter",
                                "Remove invalid symbols from filter",
                                "Use comma-separated valid stock symbols"
                            ]
                        )
                    parsed_symbols = symbol_validation.cleaned_data["symbols"]
            
            # Parse and validate signal types
            parsed_signal_types = None
            if signal_types:
                signal_type_list = [s.strip().lower() for s in signal_types.split(',') if s.strip()]
                valid_signal_types = {'long', 'short'}
                invalid_types = [t for t in signal_type_list if t not in valid_signal_types]
                if invalid_types:
                    raise ValidationError(
                        message=f"Invalid signal types: {', '.join(invalid_types)}",
                        recovery_suggestions=[
                            "Use only 'long' or 'short' as signal types",
                            "Check spelling of signal types",
                            "Use comma-separated values"
                        ]
                    )
                parsed_signal_types = signal_type_list
            
            # Create filters
            filters = ScanFilters(
                start_date=start_date,
                end_date=end_date,
                symbols=parsed_symbols,
                signal_types=parsed_signal_types,
                min_confidence=min_confidence,
                limit=pagination_validation.cleaned_data["limit"],
                offset=pagination_validation.cleaned_data["offset"]
            )
            
            # Initialize scanner service
            scanner_service = ScannerService()
            
            # Get scan history
            results = await scanner_service.get_scan_history(filters)
            
            # Convert to response format
            return [
                ScanResponse(
                    id=result.id,
                    timestamp=result.timestamp,
                    symbols_scanned=result.symbols_scanned,
                    signals_found=[signal.to_dict() for signal in result.signals_found],
                    settings_used=result.settings_used.to_dict(),
                    execution_time=result.execution_time
                )
                for result in results
            ]
            
    except StockScannerError:
        # Re-raise our custom errors
        raise
    except Exception as exc:
        # Handle unexpected errors
        error = ErrorHandler.handle_exception(exc, {
            "operation": "get_scan_history",
            "request_id": request_id
        })
        ErrorHandler.log_error(error, request_id)
        
        # Convert to HTTP exception
        error_response = ErrorHandler.create_error_response(error)
        raise HTTPException(
            status_code=500,
            detail=error_response["error"]
        )