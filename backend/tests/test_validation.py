"""
Tests for comprehensive validation utilities.
"""

import pytest
from datetime import date, datetime, timedelta
from app.utils.validation import (
    ValidationError, ValidationResult, StockSymbolValidator,
    DateRangeValidator, AlgorithmSettingsValidator, GeneralValidator
)


class TestStockSymbolValidator:
    """Test stock symbol validation."""
    
    def test_valid_symbols(self):
        """Test validation with valid symbols."""
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        result = StockSymbolValidator.validate_symbols(valid_symbols)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.cleaned_data["symbols"] == valid_symbols
    
    def test_single_symbol_validation(self):
        """Test single symbol validation."""
        # Valid symbols
        assert StockSymbolValidator.validate_symbol("AAPL")[0] is True
        assert StockSymbolValidator.validate_symbol("BRK.A")[0] is True
        assert StockSymbolValidator.validate_symbol("BRK-B")[0] is True
        
        # Invalid symbols
        assert StockSymbolValidator.validate_symbol("123")[0] is False
        assert StockSymbolValidator.validate_symbol("A@PL")[0] is False
        assert StockSymbolValidator.validate_symbol("")[0] is False
    
    def test_symbol_cleaning(self):
        """Test symbol cleaning and normalization."""
        symbols = [" aapl ", "msft", "GOOGL "]
        result = StockSymbolValidator.validate_symbols(symbols)
        
        assert result.is_valid
        assert result.cleaned_data["symbols"] == ["AAPL", "MSFT", "GOOGL"]
    
    def test_duplicate_removal(self):
        """Test duplicate symbol removal."""
        symbols = ["AAPL", "MSFT", "AAPL", "GOOGL"]
        result = StockSymbolValidator.validate_symbols(symbols)
        
        assert result.is_valid
        assert len(result.cleaned_data["symbols"]) == 3
        assert len(result.warnings) > 0
    
    def test_max_symbols_limit(self):
        """Test maximum symbols limit."""
        symbols = [f"SYM{i:03d}" for i in range(101)]
        result = StockSymbolValidator.validate_symbols(symbols, max_symbols=100)
        
        assert not result.is_valid
        assert any(error.code == "TOO_MANY_SYMBOLS" for error in result.errors)


class TestDateRangeValidator:
    """Test date range validation."""
    
    def test_valid_date_range(self):
        """Test valid date range."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = DateRangeValidator.validate_date_range(start_date, end_date)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.cleaned_data["start_date"] == start_date
        assert result.cleaned_data["end_date"] == end_date
    
    def test_invalid_date_range(self):
        """Test invalid date range (end before start)."""
        start_date = date(2023, 12, 31)
        end_date = date(2023, 1, 1)
        
        result = DateRangeValidator.validate_date_range(start_date, end_date)
        
        assert not result.is_valid
        assert any(error.code == "INVALID_DATE_RANGE" for error in result.errors)
    
    def test_date_string_parsing(self):
        """Test date string parsing."""
        is_valid, error, parsed = DateRangeValidator.validate_date("2023-01-01", "test_date")
        
        assert is_valid
        assert error is None
        assert parsed == date(2023, 1, 1)
    
    def test_invalid_date_string(self):
        """Test invalid date string."""
        is_valid, error, parsed = DateRangeValidator.validate_date("invalid-date", "test_date")
        
        assert not is_valid
        assert error is not None
        assert parsed is None
    
    def test_future_date_validation(self):
        """Test future date validation."""
        future_date = date(2030, 1, 1)
        is_valid, error, parsed = DateRangeValidator.validate_date(future_date, "test_date")
        
        assert not is_valid
        assert "future" in error.lower()
    
    def test_date_range_too_long(self):
        """Test date range that's too long."""
        start_date = date(2018, 1, 1)
        end_date = date(2024, 1, 1)  # 6 years
        
        result = DateRangeValidator.validate_date_range(start_date, end_date, max_days=365*5)
        
        assert not result.is_valid
        assert any(error.code == "DATE_RANGE_TOO_LONG" for error in result.errors)


class TestAlgorithmSettingsValidator:
    """Test algorithm settings validation."""
    
    def test_valid_settings(self):
        """Test valid algorithm settings."""
        settings = {
            "atr_multiplier": 2.0,
            "ema5_rising_threshold": 0.02,
            "ema8_rising_threshold": 0.01,
            "ema21_rising_threshold": 0.005,
            "volatility_filter": 1.5,
            "fomo_filter": 1.0,
            "higher_timeframe": "15m"
        }
        
        result = AlgorithmSettingsValidator.validate_settings(settings)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.cleaned_data == settings
    
    def test_default_values(self):
        """Test default values for missing parameters."""
        settings = {}
        result = AlgorithmSettingsValidator.validate_settings(settings)
        
        assert result.is_valid
        assert result.cleaned_data["atr_multiplier"] == 2.0
        assert result.cleaned_data["higher_timeframe"] == "15m"
    
    def test_invalid_numeric_parameters(self):
        """Test invalid numeric parameters."""
        settings = {
            "atr_multiplier": -1.0,  # Below minimum
            "ema5_rising_threshold": 1.5,  # Above maximum
            "volatility_filter": "invalid"  # Wrong type
        }
        
        result = AlgorithmSettingsValidator.validate_settings(settings)
        
        assert not result.is_valid
        assert len(result.errors) >= 3
    
    def test_invalid_timeframe(self):
        """Test invalid timeframe."""
        settings = {"higher_timeframe": "invalid"}
        result = AlgorithmSettingsValidator.validate_settings(settings)
        
        assert not result.is_valid
        assert any(error.field == "higher_timeframe" for error in result.errors)
    
    def test_boundary_values(self):
        """Test boundary values."""
        # Test minimum values
        settings = {
            "atr_multiplier": 0.5,
            "ema5_rising_threshold": 0.001,
            "volatility_filter": 0.1
        }
        result = AlgorithmSettingsValidator.validate_settings(settings)
        assert result.is_valid
        
        # Test maximum values
        settings = {
            "atr_multiplier": 10.0,
            "ema5_rising_threshold": 0.1,
            "volatility_filter": 5.0
        }
        result = AlgorithmSettingsValidator.validate_settings(settings)
        assert result.is_valid


class TestGeneralValidator:
    """Test general validation utilities."""
    
    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        result = GeneralValidator.validate_pagination(limit=50, offset=10)
        
        assert result.is_valid
        assert result.cleaned_data["limit"] == 50
        assert result.cleaned_data["offset"] == 10
    
    def test_default_pagination(self):
        """Test default pagination values."""
        result = GeneralValidator.validate_pagination()
        
        assert result.is_valid
        assert result.cleaned_data["limit"] == 100
        assert result.cleaned_data["offset"] == 0
    
    def test_invalid_pagination(self):
        """Test invalid pagination parameters."""
        # Negative limit
        result = GeneralValidator.validate_pagination(limit=-1)
        assert not result.is_valid
        
        # Limit too high
        result = GeneralValidator.validate_pagination(limit=2000)
        assert not result.is_valid
        
        # Negative offset
        result = GeneralValidator.validate_pagination(offset=-5)
        assert not result.is_valid
    
    def test_valid_confidence_range(self):
        """Test valid confidence range."""
        result = GeneralValidator.validate_confidence_range(0.5)
        
        assert result.is_valid
        assert result.cleaned_data["min_confidence"] == 0.5
    
    def test_invalid_confidence_range(self):
        """Test invalid confidence range."""
        # Below 0
        result = GeneralValidator.validate_confidence_range(-0.1)
        assert not result.is_valid
        
        # Above 1
        result = GeneralValidator.validate_confidence_range(1.5)
        assert not result.is_valid
        
        # Wrong type
        result = GeneralValidator.validate_confidence_range("invalid")
        assert not result.is_valid


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        errors = [ValidationError("test", "Test error", "TEST_ERROR")]
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            cleaned_data={"test": "value"},
            warnings=["Test warning"]
        )
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.cleaned_data["test"] == "value"
        assert len(result.warnings) == 1
    
    def test_validation_result_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            cleaned_data={}
        )
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0


class TestValidationError:
    """Test ValidationError dataclass."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError(
            "test_field",
            "Test error message",
            "TEST_ERROR",
            "invalid_value"
        )
        
        assert error.field == "test_field"
        assert error.message == "Test error message"
        assert error.code == "TEST_ERROR"
        assert error.value == "invalid_value"