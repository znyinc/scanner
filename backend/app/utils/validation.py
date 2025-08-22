"""
Comprehensive input validation utilities for the stock scanner application.
Provides validation for stock symbols, date ranges, algorithm parameters, and other user inputs.
"""

import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error with field and message."""
    field: str
    message: str
    code: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of validation with errors and cleaned data."""
    is_valid: bool
    errors: List[ValidationError]
    cleaned_data: Dict[str, Any]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class StockSymbolValidator:
    """Validator for stock symbols with comprehensive rules."""
    
    # Common stock symbol patterns
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?(-[A-Z])?$')
    CRYPTO_PATTERN = re.compile(r'^[A-Z]{2,10}-(USD|EUR|BTC|ETH)$')
    
    # Known invalid patterns
    INVALID_PATTERNS = [
        re.compile(r'^\d+$'),  # Only numbers
        re.compile(r'^[^A-Z]'),  # Doesn't start with letter
        re.compile(r'[^A-Z0-9.\-]'),  # Invalid characters
    ]
    
    # Reserved words that shouldn't be symbols
    RESERVED_WORDS = {
        'NULL', 'NONE', 'UNDEFINED', 'TEST', 'DEMO', 'SAMPLE'
    }
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single stock symbol.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not symbol or not isinstance(symbol, str):
            return False, "Symbol must be a non-empty string"
        
        # Clean and normalize
        symbol = symbol.strip().upper()
        
        if not symbol:
            return False, "Symbol cannot be empty"
        
        if len(symbol) > 12:
            return False, "Symbol too long (max 12 characters)"
        
        if len(symbol) < 1:
            return False, "Symbol too short (min 1 character)"
        
        # Check reserved words
        if symbol in cls.RESERVED_WORDS:
            return False, f"'{symbol}' is a reserved word"
        
        # Check invalid patterns
        for pattern in cls.INVALID_PATTERNS:
            if pattern.search(symbol):
                return False, f"Symbol '{symbol}' contains invalid characters"
        
        # Check valid patterns
        if cls.SYMBOL_PATTERN.match(symbol) or cls.CRYPTO_PATTERN.match(symbol):
            return True, None
        
        # Additional flexibility for international symbols
        if re.match(r'^[A-Z]{1,8}$', symbol):
            return True, None
        
        return False, f"Symbol '{symbol}' does not match valid format"
    
    @classmethod
    def validate_symbols(cls, symbols: List[str], max_symbols: int = 100) -> ValidationResult:
        """
        Validate a list of stock symbols.
        
        Args:
            symbols: List of symbols to validate
            max_symbols: Maximum number of symbols allowed
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        warnings = []
        valid_symbols = []
        
        if not symbols:
            errors.append(ValidationError(
                field="symbols",
                message="At least one symbol is required",
                code="SYMBOLS_REQUIRED"
            ))
            return ValidationResult(False, errors, {}, warnings)
        
        if len(symbols) > max_symbols:
            errors.append(ValidationError(
                field="symbols",
                message=f"Too many symbols (max {max_symbols})",
                code="TOO_MANY_SYMBOLS",
                value=len(symbols)
            ))
        
        seen_symbols = set()
        
        for i, symbol in enumerate(symbols):
            if not symbol or not isinstance(symbol, str):
                errors.append(ValidationError(
                    field=f"symbols[{i}]",
                    message="Symbol must be a non-empty string",
                    code="INVALID_SYMBOL_TYPE",
                    value=symbol
                ))
                continue
            
            # Clean symbol
            clean_symbol = symbol.strip().upper()
            
            # Check for duplicates
            if clean_symbol in seen_symbols:
                warnings.append(f"Duplicate symbol '{clean_symbol}' removed")
                continue
            
            # Validate symbol
            is_valid, error_msg = cls.validate_symbol(clean_symbol)
            
            if is_valid:
                valid_symbols.append(clean_symbol)
                seen_symbols.add(clean_symbol)
            else:
                errors.append(ValidationError(
                    field=f"symbols[{i}]",
                    message=error_msg,
                    code="INVALID_SYMBOL",
                    value=symbol
                ))
        
        # Check if we have any valid symbols
        if not valid_symbols and not errors:
            errors.append(ValidationError(
                field="symbols",
                message="No valid symbols provided",
                code="NO_VALID_SYMBOLS"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            cleaned_data={"symbols": valid_symbols},
            warnings=warnings
        )


class DateRangeValidator:
    """Validator for date ranges with business logic."""
    
    MIN_DATE = date(2000, 1, 1)
    MAX_FUTURE_DAYS = 1  # Allow 1 day in future for timezone differences
    
    @classmethod
    def validate_date(cls, date_value: Union[str, date, datetime], field_name: str) -> Tuple[bool, Optional[str], Optional[date]]:
        """
        Validate a single date.
        
        Args:
            date_value: Date to validate
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid, error_message, parsed_date)
        """
        if date_value is None:
            return False, f"{field_name} is required", None
        
        # Parse date
        parsed_date = None
        
        if isinstance(date_value, str):
            try:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if parsed_date is None:
                    return False, f"Invalid date format for {field_name}. Use YYYY-MM-DD", None
                    
            except Exception as e:
                return False, f"Error parsing {field_name}: {str(e)}", None
                
        elif isinstance(date_value, datetime):
            parsed_date = date_value.date()
        elif isinstance(date_value, date):
            parsed_date = date_value
        else:
            return False, f"{field_name} must be a date string or date object", None
        
        # Validate date range
        today = date.today()
        max_future_date = today + timedelta(days=cls.MAX_FUTURE_DAYS)
        
        if parsed_date < cls.MIN_DATE:
            return False, f"{field_name} cannot be before {cls.MIN_DATE}", None
        
        if parsed_date > max_future_date:
            return False, f"{field_name} cannot be more than {cls.MAX_FUTURE_DAYS} day(s) in the future", None
        
        return True, None, parsed_date
    
    @classmethod
    def validate_date_range(cls, start_date: Union[str, date, datetime], 
                          end_date: Union[str, date, datetime],
                          min_days: int = 1, max_days: int = 365 * 5) -> ValidationResult:
        """
        Validate a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            min_days: Minimum number of days in range
            max_days: Maximum number of days in range
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        warnings = []
        
        # Validate start date
        start_valid, start_error, parsed_start = cls.validate_date(start_date, "start_date")
        if not start_valid:
            errors.append(ValidationError(
                field="start_date",
                message=start_error,
                code="INVALID_START_DATE",
                value=start_date
            ))
        
        # Validate end date
        end_valid, end_error, parsed_end = cls.validate_date(end_date, "end_date")
        if not end_valid:
            errors.append(ValidationError(
                field="end_date",
                message=end_error,
                code="INVALID_END_DATE",
                value=end_date
            ))
        
        # If both dates are valid, check range
        if start_valid and end_valid and parsed_start and parsed_end:
            if parsed_start >= parsed_end:
                errors.append(ValidationError(
                    field="date_range",
                    message="Start date must be before end date",
                    code="INVALID_DATE_RANGE"
                ))
            else:
                # Check range length
                range_days = (parsed_end - parsed_start).days
                
                if range_days < min_days:
                    errors.append(ValidationError(
                        field="date_range",
                        message=f"Date range too short (minimum {min_days} days)",
                        code="DATE_RANGE_TOO_SHORT",
                        value=range_days
                    ))
                
                if range_days > max_days:
                    errors.append(ValidationError(
                        field="date_range",
                        message=f"Date range too long (maximum {max_days} days)",
                        code="DATE_RANGE_TOO_LONG",
                        value=range_days
                    ))
                
                # Warn about weekends/holidays
                if range_days > 7:
                    weekend_days = 0
                    current_date = parsed_start
                    while current_date < parsed_end:
                        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                            weekend_days += 1
                        current_date += timedelta(days=1)
                    
                    if weekend_days > 0:
                        warnings.append(f"Date range includes {weekend_days} weekend days (markets closed)")
        
        cleaned_data = {}
        if parsed_start:
            cleaned_data["start_date"] = parsed_start
        if parsed_end:
            cleaned_data["end_date"] = parsed_end
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            cleaned_data=cleaned_data,
            warnings=warnings
        )


class AlgorithmSettingsValidator:
    """Validator for algorithm settings with acceptable ranges."""
    
    # Define acceptable ranges for each parameter
    PARAMETER_RANGES = {
        'atr_multiplier': {'min': 0.5, 'max': 10.0, 'default': 2.0},
        'ema5_rising_threshold': {'min': 0.001, 'max': 0.1, 'default': 0.02},
        'ema8_rising_threshold': {'min': 0.001, 'max': 0.1, 'default': 0.01},
        'ema21_rising_threshold': {'min': 0.001, 'max': 0.1, 'default': 0.005},
        'volatility_filter': {'min': 0.1, 'max': 5.0, 'default': 1.5},
        'fomo_filter': {'min': 0.1, 'max': 3.0, 'default': 1.0},
    }
    
    VALID_TIMEFRAMES = {
        '1m', '2m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'
    }
    
    @classmethod
    def validate_numeric_parameter(cls, value: Any, param_name: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Validate a numeric algorithm parameter.
        
        Args:
            value: Parameter value to validate
            param_name: Name of the parameter
            
        Returns:
            Tuple of (is_valid, error_message, cleaned_value)
        """
        if value is None:
            # Use default value
            default_val = cls.PARAMETER_RANGES[param_name]['default']
            return True, None, default_val
        
        # Convert to float
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return False, f"{param_name} must be a number", None
        
        # Check if it's a valid number
        if not isinstance(float_value, (int, float)) or float_value != float_value:  # NaN check
            return False, f"{param_name} must be a valid number", None
        
        # Check range
        param_range = cls.PARAMETER_RANGES[param_name]
        if float_value < param_range['min']:
            return False, f"{param_name} must be at least {param_range['min']}", None
        
        if float_value > param_range['max']:
            return False, f"{param_name} must be at most {param_range['max']}", None
        
        return True, None, float_value
    
    @classmethod
    def validate_timeframe(cls, timeframe: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate higher timeframe parameter.
        
        Args:
            timeframe: Timeframe string to validate
            
        Returns:
            Tuple of (is_valid, error_message, cleaned_value)
        """
        if not timeframe:
            return True, None, "15m"  # Default
        
        if not isinstance(timeframe, str):
            return False, "Timeframe must be a string", None
        
        clean_timeframe = timeframe.strip().lower()
        
        if clean_timeframe not in cls.VALID_TIMEFRAMES:
            valid_options = ', '.join(sorted(cls.VALID_TIMEFRAMES))
            return False, f"Invalid timeframe. Valid options: {valid_options}", None
        
        return True, None, clean_timeframe
    
    @classmethod
    def validate_settings(cls, settings: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete algorithm settings.
        
        Args:
            settings: Dictionary of algorithm settings
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        warnings = []
        cleaned_data = {}
        
        if not isinstance(settings, dict):
            errors.append(ValidationError(
                field="settings",
                message="Settings must be a dictionary",
                code="INVALID_SETTINGS_TYPE",
                value=type(settings).__name__
            ))
            return ValidationResult(False, errors, {}, warnings)
        
        # Validate numeric parameters
        for param_name in cls.PARAMETER_RANGES.keys():
            value = settings.get(param_name)
            is_valid, error_msg, cleaned_value = cls.validate_numeric_parameter(value, param_name)
            
            if is_valid:
                cleaned_data[param_name] = cleaned_value
                # Warn if using default
                if value is None:
                    warnings.append(f"Using default value for {param_name}: {cleaned_value}")
            else:
                errors.append(ValidationError(
                    field=param_name,
                    message=error_msg,
                    code="INVALID_PARAMETER_VALUE",
                    value=value
                ))
        
        # Validate timeframe
        timeframe = settings.get('higher_timeframe')
        is_valid, error_msg, cleaned_timeframe = cls.validate_timeframe(timeframe)
        
        if is_valid:
            cleaned_data['higher_timeframe'] = cleaned_timeframe
            if timeframe is None:
                warnings.append(f"Using default timeframe: {cleaned_timeframe}")
        else:
            errors.append(ValidationError(
                field="higher_timeframe",
                message=error_msg,
                code="INVALID_TIMEFRAME",
                value=timeframe
            ))
        
        # Check for unknown parameters
        known_params = set(cls.PARAMETER_RANGES.keys()) | {'higher_timeframe'}
        unknown_params = set(settings.keys()) - known_params
        
        if unknown_params:
            warnings.append(f"Unknown parameters ignored: {', '.join(unknown_params)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            cleaned_data=cleaned_data,
            warnings=warnings
        )


class GeneralValidator:
    """General validation utilities."""
    
    @staticmethod
    def validate_pagination(limit: Optional[int] = None, offset: Optional[int] = None) -> ValidationResult:
        """
        Validate pagination parameters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        cleaned_data = {}
        
        # Validate limit
        if limit is not None:
            try:
                limit_int = int(limit)
                if limit_int < 1:
                    errors.append(ValidationError(
                        field="limit",
                        message="Limit must be at least 1",
                        code="INVALID_LIMIT",
                        value=limit
                    ))
                elif limit_int > 1000:
                    errors.append(ValidationError(
                        field="limit",
                        message="Limit cannot exceed 1000",
                        code="LIMIT_TOO_HIGH",
                        value=limit
                    ))
                else:
                    cleaned_data["limit"] = limit_int
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    field="limit",
                    message="Limit must be an integer",
                    code="INVALID_LIMIT_TYPE",
                    value=limit
                ))
        else:
            cleaned_data["limit"] = 100  # Default
        
        # Validate offset
        if offset is not None:
            try:
                offset_int = int(offset)
                if offset_int < 0:
                    errors.append(ValidationError(
                        field="offset",
                        message="Offset cannot be negative",
                        code="INVALID_OFFSET",
                        value=offset
                    ))
                else:
                    cleaned_data["offset"] = offset_int
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    field="offset",
                    message="Offset must be an integer",
                    code="INVALID_OFFSET_TYPE",
                    value=offset
                ))
        else:
            cleaned_data["offset"] = 0  # Default
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            cleaned_data=cleaned_data
        )
    
    @staticmethod
    def validate_confidence_range(min_confidence: Optional[float] = None) -> ValidationResult:
        """
        Validate confidence range parameter.
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        cleaned_data = {}
        
        if min_confidence is not None:
            try:
                conf_float = float(min_confidence)
                if conf_float < 0.0 or conf_float > 1.0:
                    errors.append(ValidationError(
                        field="min_confidence",
                        message="Confidence must be between 0.0 and 1.0",
                        code="INVALID_CONFIDENCE_RANGE",
                        value=min_confidence
                    ))
                else:
                    cleaned_data["min_confidence"] = conf_float
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    field="min_confidence",
                    message="Confidence must be a number",
                    code="INVALID_CONFIDENCE_TYPE",
                    value=min_confidence
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            cleaned_data=cleaned_data
        )