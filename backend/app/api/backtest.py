"""
Backtest API endpoints for historical analysis.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, date
import uuid

from ..services.backtest_service import BacktestService, BacktestFilters
from ..models.signals import AlgorithmSettings
from ..models.results import BacktestResult
from ..utils.validation import StockSymbolValidator, AlgorithmSettingsValidator, DateRangeValidator, GeneralValidator
from ..utils.error_handling import (
    ErrorHandler, ValidationError, handle_errors, ErrorContext,
    StockScannerError
)

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """Request model for backtesting."""
    symbols: List[str] = Field(..., description="List of stock symbols to backtest")
    start_date: date = Field(..., description="Start date for backtest period")
    end_date: date = Field(..., description="End date for backtest period")
    settings: Optional[dict] = Field(None, description="Algorithm settings override")


class BacktestResponse(BaseModel):
    """Response model for backtest results."""
    id: str
    timestamp: datetime
    start_date: date
    end_date: date
    symbols: List[str]
    trades: List[dict]
    performance: dict
    settings_used: dict


@router.post("/", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, http_request: Request):
    """
    Run a historical backtest using the EMA-ATR algorithm.
    
    - **symbols**: List of stock symbols to backtest (1-50 symbols)
    - **start_date**: Start date for backtest period
    - **end_date**: End date for backtest period
    - **settings**: Optional algorithm settings override
    
    Returns backtest results with trades and performance metrics.
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("run_backtest", request_id=request_id, symbols_count=len(request.symbols)):
            # Validate symbols
            symbol_validation = StockSymbolValidator.validate_symbols(request.symbols, max_symbols=50)
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
            
            # Validate date range
            date_validation = DateRangeValidator.validate_date_range(
                request.start_date, 
                request.end_date,
                min_days=1,
                max_days=365 * 5  # 5 years max
            )
            if not date_validation.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in date_validation.errors]
                raise ValidationError(
                    message=f"Date range validation failed: {'; '.join(error_messages)}",
                    recovery_suggestions=[
                        "Ensure start date is before end date",
                        "Use dates in YYYY-MM-DD format",
                        "Keep date range within 5 years",
                        "Ensure dates are not in the future"
                    ]
                )
            
            validated_start_date = date_validation.cleaned_data["start_date"]
            validated_end_date = date_validation.cleaned_data["end_date"]
            
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
            
            # Initialize backtest service
            backtest_service = BacktestService()
            
            # Run backtest
            result = await backtest_service.run_backtest(
                symbols=validated_symbols,
                start_date=validated_start_date,
                end_date=validated_end_date,
                settings=settings
            )
            
            # Convert to response format
            return BacktestResponse(
                id=result.id,
                timestamp=result.timestamp,
                start_date=result.start_date,
                end_date=result.end_date,
                symbols=result.symbols,
                trades=[trade.to_dict() for trade in result.trades],
                performance=result.performance.to_dict(),
                settings_used=result.settings_used.to_dict()
            )
            
    except ValidationError as exc:
        # Handle validation errors with 422 status
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )
    except StockScannerError:
        # Re-raise our custom errors
        raise
    except Exception as exc:
        # Handle unexpected errors
        error = ErrorHandler.handle_exception(exc, {
            "operation": "run_backtest",
            "request_id": request_id,
            "symbols_count": len(request.symbols),
            "date_range_days": (request.end_date - request.start_date).days
        })
        ErrorHandler.log_error(error, request_id)
        
        # Convert to HTTP exception
        error_response = ErrorHandler.create_error_response(error)
        raise HTTPException(
            status_code=500 if error.error_details.category.value == "system" else 400,
            detail=error_response["error"]["message"]
        )


@router.get("/history", response_model=List[BacktestResponse])
async def get_backtest_history(
    start_date: Optional[date] = Query(None, description="Filter backtests from this date"),
    end_date: Optional[date] = Query(None, description="Filter backtests until this date"),
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols to filter by"),
    min_trades: Optional[int] = Query(None, description="Minimum number of trades", ge=0),
    min_win_rate: Optional[float] = Query(None, description="Minimum win rate", ge=0.0, le=1.0),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
    offset: int = Query(0, description="Number of results to skip", ge=0)
):
    """
    Retrieve backtest history with optional filtering.
    
    - **start_date**: Filter backtests from this date
    - **end_date**: Filter backtests until this date
    - **symbols**: Comma-separated symbols to filter by
    - **min_trades**: Minimum number of trades
    - **min_win_rate**: Minimum win rate (0.0-1.0)
    - **limit**: Maximum results (1-1000)
    - **offset**: Results to skip for pagination
    """
    try:
        # Parse filters
        filters = BacktestFilters(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols.split(',') if symbols else None,
            min_trades=min_trades,
            min_win_rate=min_win_rate,
            limit=limit,
            offset=offset
        )
        
        # Initialize backtest service
        backtest_service = BacktestService()
        
        # Get backtest history
        results = await backtest_service.get_backtest_history(filters)
        
        # Convert to response format
        return [
            BacktestResponse(
                id=result.id,
                timestamp=result.timestamp,
                start_date=result.start_date,
                end_date=result.end_date,
                symbols=result.symbols,
                trades=[trade.to_dict() for trade in result.trades],
                performance=result.performance.to_dict(),
                settings_used=result.settings_used.to_dict()
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve backtest history: {str(e)}")