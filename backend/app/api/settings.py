"""
Settings API endpoints for algorithm parameter configuration.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import json
import os
import uuid

from ..models.signals import AlgorithmSettings
from ..utils.validation import AlgorithmSettingsValidator
from ..utils.error_handling import (
    ErrorHandler, ValidationError, handle_errors, ErrorContext,
    StockScannerError
)

router = APIRouter(prefix="/settings", tags=["settings"])

# Settings file path
SETTINGS_FILE = "algorithm_settings.json"


class SettingsRequest(BaseModel):
    """Request model for updating algorithm settings."""
    atr_multiplier: Optional[float] = Field(None, description="ATR multiplier")
    ema5_rising_threshold: Optional[float] = Field(None, description="EMA5 rising threshold")
    ema8_rising_threshold: Optional[float] = Field(None, description="EMA8 rising threshold")
    ema21_rising_threshold: Optional[float] = Field(None, description="EMA21 rising threshold")
    volatility_filter: Optional[float] = Field(None, description="Volatility filter multiplier")
    fomo_filter: Optional[float] = Field(None, description="FOMO filter multiplier")
    higher_timeframe: Optional[str] = Field(None, description="Higher timeframe period")


class SettingsResponse(BaseModel):
    """Response model for algorithm settings."""
    atr_multiplier: float
    ema5_rising_threshold: float
    ema8_rising_threshold: float
    ema21_rising_threshold: float
    volatility_filter: float
    fomo_filter: float
    higher_timeframe: str


def _load_settings() -> AlgorithmSettings:
    """Load settings from file or return defaults."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return AlgorithmSettings.from_dict(data)
    except Exception:
        pass  # Fall back to defaults
    
    return AlgorithmSettings()


def _save_settings(settings: AlgorithmSettings) -> None:
    """Save settings to file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings.to_dict(), f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")


@router.get("/", response_model=SettingsResponse)
@router.get("", response_model=SettingsResponse)  # Handle both with and without trailing slash
async def get_settings():
    """
    Get current algorithm settings.
    
    Returns the current algorithm configuration parameters.
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("get_settings", request_id=request_id):
            settings = _load_settings()
            
            return SettingsResponse(
                atr_multiplier=settings.atr_multiplier,
                ema5_rising_threshold=settings.ema5_rising_threshold,
                ema8_rising_threshold=settings.ema8_rising_threshold,
                ema21_rising_threshold=settings.ema21_rising_threshold,
                volatility_filter=settings.volatility_filter,
                fomo_filter=settings.fomo_filter,
                higher_timeframe=settings.higher_timeframe
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
            "operation": "get_settings",
            "request_id": request_id
        })
        ErrorHandler.log_error(error, request_id)
        
        # Convert to HTTP exception
        error_response = ErrorHandler.create_error_response(error)
        raise HTTPException(
            status_code=500,
            detail=error_response["error"]["message"]
        )


@router.put("/", response_model=SettingsResponse)
@router.put("", response_model=SettingsResponse)  # Handle both with and without trailing slash
async def update_settings(request: SettingsRequest, http_request: Request):
    """
    Update algorithm settings.
    
    - **atr_multiplier**: ATR multiplier (0.5-10.0, default: 2.0)
    - **ema5_rising_threshold**: EMA5 rising threshold (0.001-0.1, default: 0.02)
    - **ema8_rising_threshold**: EMA8 rising threshold (0.001-0.1, default: 0.01)
    - **ema21_rising_threshold**: EMA21 rising threshold (0.001-0.1, default: 0.005)
    - **volatility_filter**: Volatility filter multiplier (0.1-5.0, default: 1.5)
    - **fomo_filter**: FOMO filter multiplier (0.1-3.0, default: 1.0)
    - **higher_timeframe**: Higher timeframe period (1m, 2m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, default: 15m)
    
    Only provided parameters will be updated. Others will retain their current values.
    """
    request_id = str(uuid.uuid4())
    
    try:
        with ErrorContext("update_settings", request_id=request_id):
            # Convert request to dict for validation
            update_data = request.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationError(
                    message="No settings provided for update",
                    recovery_suggestions=[
                        "Provide at least one setting parameter to update",
                        "Check the request body format",
                        "Refer to API documentation for valid parameters"
                    ]
                )
            
            # Validate settings
            settings_validation = AlgorithmSettingsValidator.validate_settings(update_data)
            if not settings_validation.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in settings_validation.errors]
                raise ValidationError(
                    message=f"Settings validation failed: {'; '.join(error_messages)}",
                    recovery_suggestions=[
                        "Check parameter ranges in documentation",
                        "Ensure all numeric values are within valid ranges",
                        "Use valid timeframe values (1m, 5m, 15m, etc.)"
                    ]
                )
            
            # Load current settings
            current_settings = _load_settings()
            
            # Update only validated parameters
            validated_data = settings_validation.cleaned_data
            for key, value in validated_data.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            # Save updated settings
            _save_settings(current_settings)
            
            return SettingsResponse(
                atr_multiplier=current_settings.atr_multiplier,
                ema5_rising_threshold=current_settings.ema5_rising_threshold,
                ema8_rising_threshold=current_settings.ema8_rising_threshold,
                ema21_rising_threshold=current_settings.ema21_rising_threshold,
                volatility_filter=current_settings.volatility_filter,
                fomo_filter=current_settings.fomo_filter,
                higher_timeframe=current_settings.higher_timeframe
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
            "operation": "update_settings",
            "request_id": request_id,
            "update_fields": list(request.model_dump(exclude_unset=True).keys())
        })
        ErrorHandler.log_error(error, request_id)
        
        # Convert to HTTP exception
        error_response = ErrorHandler.create_error_response(error)
        raise HTTPException(
            status_code=500 if error.error_details.category.value == "system" else 400,
            detail=error_response["error"]["message"]
        )


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings():
    """
    Reset algorithm settings to defaults.
    
    Restores all algorithm parameters to their default values.
    """
    try:
        # Create default settings
        default_settings = AlgorithmSettings()
        
        # Save default settings
        _save_settings(default_settings)
        
        return SettingsResponse(
            atr_multiplier=default_settings.atr_multiplier,
            ema5_rising_threshold=default_settings.ema5_rising_threshold,
            ema8_rising_threshold=default_settings.ema8_rising_threshold,
            ema21_rising_threshold=default_settings.ema21_rising_threshold,
            volatility_filter=default_settings.volatility_filter,
            fomo_filter=default_settings.fomo_filter,
            higher_timeframe=default_settings.higher_timeframe
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")