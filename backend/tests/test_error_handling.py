"""
Tests for comprehensive error handling utilities.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from app.utils.error_handling import (
    ErrorCategory, ErrorSeverity, ErrorDetails, StockScannerError,
    ValidationError, APIError, NetworkError, DatabaseError, AlgorithmError,
    RateLimitError, TimeoutError, ErrorHandler, ErrorContext, handle_errors
)


class TestErrorDetails:
    """Test ErrorDetails dataclass."""
    
    def test_error_details_creation(self):
        """Test creating ErrorDetails with all fields."""
        details = ErrorDetails(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            code="TEST_ERROR",
            message="Test message",
            user_message="User message",
            recovery_suggestions=["Try again"],
            technical_details={"field": "test"}
        )
        
        assert details.category == ErrorCategory.VALIDATION
        assert details.severity == ErrorSeverity.MEDIUM
        assert details.code == "TEST_ERROR"
        assert details.message == "Test message"
        assert details.user_message == "User message"
        assert details.recovery_suggestions == ["Try again"]
        assert details.technical_details == {"field": "test"}
        assert isinstance(details.timestamp, datetime)
    
    def test_error_details_auto_timestamp(self):
        """Test that timestamp is automatically set."""
        details = ErrorDetails(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            code="TEST",
            message="Test",
            user_message="Test",
            recovery_suggestions=[]
        )
        
        assert details.timestamp is not None
        assert isinstance(details.timestamp, datetime)


class TestStockScannerError:
    """Test base StockScannerError class."""
    
    def test_stock_scanner_error_creation(self):
        """Test creating StockScannerError."""
        details = ErrorDetails(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            code="TEST_ERROR",
            message="Test message",
            user_message="User message",
            recovery_suggestions=["Try again"]
        )
        
        error = StockScannerError(details)
        
        assert error.error_details == details
        assert str(error) == "Test message"
        assert error.original_exception is None
    
    def test_stock_scanner_error_with_original(self):
        """Test creating StockScannerError with original exception."""
        original = ValueError("Original error")
        details = ErrorDetails(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            code="SYSTEM_ERROR",
            message="System error",
            user_message="System error occurred",
            recovery_suggestions=["Try again"]
        )
        
        error = StockScannerError(details, original)
        
        assert error.original_exception == original
    
    def test_to_dict(self):
        """Test converting error to dictionary."""
        details = ErrorDetails(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            code="TEST_ERROR",
            message="Test message",
            user_message="User message",
            recovery_suggestions=["Try again"],
            technical_details={"field": "test"}
        )
        
        error = StockScannerError(details)
        result = error.to_dict()
        
        assert result["category"] == "validation"
        assert result["severity"] == "medium"
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Test message"
        assert result["user_message"] == "User message"
        assert result["recovery_suggestions"] == ["Try again"]
        assert result["technical_details"] == {"field": "test"}
        assert "timestamp" in result


class TestSpecificErrors:
    """Test specific error types."""
    
    def test_validation_error(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid input", field="test_field", value="invalid")
        
        assert error.error_details.category == ErrorCategory.VALIDATION
        assert error.error_details.severity == ErrorSeverity.MEDIUM
        assert error.error_details.code == "VALIDATION_ERROR"
        assert "Invalid input" in error.error_details.message
        assert error.error_details.technical_details["field"] == "test_field"
        assert error.error_details.technical_details["value"] == "invalid"
    
    def test_api_error(self):
        """Test APIError creation."""
        error = APIError("API failed", api_name="yfinance", status_code=500)
        
        assert error.error_details.category == ErrorCategory.API_ERROR
        assert error.error_details.severity == ErrorSeverity.HIGH
        assert error.error_details.code == "API_ERROR_500"
        assert error.error_details.technical_details["api_name"] == "yfinance"
        assert error.error_details.technical_details["status_code"] == 500
    
    def test_api_error_rate_limit(self):
        """Test APIError with rate limit status."""
        error = APIError("Rate limited", status_code=429)
        
        assert "Rate limit exceeded" in error.error_details.recovery_suggestions[0]
    
    def test_network_error(self):
        """Test NetworkError creation."""
        error = NetworkError("Connection failed", operation="fetch_data")
        
        assert error.error_details.category == ErrorCategory.NETWORK
        assert error.error_details.severity == ErrorSeverity.HIGH
        assert error.error_details.code == "NETWORK_ERROR"
        assert error.error_details.technical_details["operation"] == "fetch_data"
    
    def test_database_error(self):
        """Test DatabaseError creation."""
        error = DatabaseError("Query failed", operation="insert", table="scan_results")
        
        assert error.error_details.category == ErrorCategory.DATABASE
        assert error.error_details.severity == ErrorSeverity.CRITICAL
        assert error.error_details.code == "DATABASE_ERROR"
        assert error.error_details.technical_details["operation"] == "insert"
        assert error.error_details.technical_details["table"] == "scan_results"
    
    def test_algorithm_error(self):
        """Test AlgorithmError creation."""
        error = AlgorithmError("EMA calculation failed", symbol="AAPL", indicator="EMA5")
        
        assert error.error_details.category == ErrorCategory.ALGORITHM
        assert error.error_details.severity == ErrorSeverity.MEDIUM
        assert error.error_details.code == "ALGORITHM_ERROR"
        assert error.error_details.technical_details["symbol"] == "AAPL"
        assert error.error_details.technical_details["indicator"] == "EMA5"
    
    def test_rate_limit_error(self):
        """Test RateLimitError creation."""
        error = RateLimitError("Rate limited", retry_after=60, api_name="yfinance")
        
        assert error.error_details.category == ErrorCategory.RATE_LIMIT
        assert error.error_details.severity == ErrorSeverity.MEDIUM
        assert error.error_details.code == "RATE_LIMIT_ERROR"
        assert error.error_details.technical_details["retry_after"] == 60
        assert "Wait 60 seconds" in error.error_details.recovery_suggestions[0]
    
    def test_timeout_error(self):
        """Test TimeoutError creation."""
        error = TimeoutError("Operation timed out", operation="scan", timeout_seconds=30)
        
        assert error.error_details.category == ErrorCategory.TIMEOUT
        assert error.error_details.severity == ErrorSeverity.MEDIUM
        assert error.error_details.code == "TIMEOUT_ERROR"
        assert error.error_details.technical_details["operation"] == "scan"
        assert error.error_details.technical_details["timeout_seconds"] == 30


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_handle_stock_scanner_error(self):
        """Test handling existing StockScannerError."""
        original_error = ValidationError("Test error")
        result = ErrorHandler.handle_exception(original_error)
        
        assert result == original_error
    
    def test_handle_rate_limit_exception(self):
        """Test handling rate limit exception."""
        exc = Exception("Rate limit exceeded")
        result = ErrorHandler.handle_exception(exc)
        
        assert isinstance(result, RateLimitError)
        assert result.error_details.category == ErrorCategory.RATE_LIMIT
    
    def test_handle_timeout_exception(self):
        """Test handling timeout exception."""
        exc = Exception("Operation timed out")
        result = ErrorHandler.handle_exception(exc)
        
        assert isinstance(result, TimeoutError)
        assert result.error_details.category == ErrorCategory.TIMEOUT
    
    def test_handle_network_exception(self):
        """Test handling network exception."""
        exc = Exception("Connection error")
        result = ErrorHandler.handle_exception(exc)
        
        assert isinstance(result, NetworkError)
        assert result.error_details.category == ErrorCategory.NETWORK
    
    def test_handle_database_exception(self):
        """Test handling database exception."""
        exc = Exception("Database connection failed")
        result = ErrorHandler.handle_exception(exc)
        
        assert isinstance(result, DatabaseError)
        assert result.error_details.category == ErrorCategory.DATABASE
    
    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        exc = ValueError("Generic error")
        result = ErrorHandler.handle_exception(exc, {"operation": "test"})
        
        assert isinstance(result, StockScannerError)
        assert result.error_details.category == ErrorCategory.SYSTEM
        assert result.error_details.technical_details["exception_type"] == "ValueError"
        assert result.error_details.technical_details["context"]["operation"] == "test"
    
    @patch('app.utils.error_handling.logger')
    def test_log_error(self, mock_logger):
        """Test error logging."""
        error = ValidationError("Test error")
        ErrorHandler.log_error(error, "request-123")
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "request-123" in call_args or "request_id" in call_args
    
    @patch('app.utils.error_handling.logger')
    def test_log_critical_error(self, mock_logger):
        """Test logging critical error."""
        error = DatabaseError("Critical database error")
        ErrorHandler.log_error(error)
        
        mock_logger.critical.assert_called_once()
    
    def test_create_error_response(self):
        """Test creating error response."""
        error = ValidationError("Test error", field="test")
        response = ErrorHandler.create_error_response(error)
        
        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["category"] == "validation"
        assert response["error"]["severity"] == "medium"
        assert "recovery_suggestions" in response["error"]
        assert "technical_details" not in response["error"]
    
    def test_create_error_response_with_technical_details(self):
        """Test creating error response with technical details."""
        error = ValidationError("Test error", field="test")
        response = ErrorHandler.create_error_response(error, include_technical_details=True)
        
        assert "technical_details" in response["error"]
        assert response["error"]["technical_details"]["field"] == "test"


class TestErrorDecorator:
    """Test error handling decorator."""
    
    def test_handle_errors_decorator_success(self):
        """Test decorator with successful function."""
        @handle_errors()
        def test_function():
            return {"success": True, "data": "test"}
        
        result = test_function()
        assert result["success"] is True
        assert result["data"] == "test"
    
    @patch('app.utils.error_handling.ErrorHandler.log_error')
    def test_handle_errors_decorator_exception(self, mock_log):
        """Test decorator with exception."""
        @handle_errors()
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        
        assert result["success"] is False
        assert result["error"]["code"] == "SYSTEM_ERROR"
        mock_log.assert_called_once()
    
    @patch('app.utils.error_handling.ErrorHandler.log_error')
    def test_handle_errors_decorator_with_technical_details(self, mock_log):
        """Test decorator with technical details enabled."""
        @handle_errors(include_technical_details=True)
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        
        assert "technical_details" in result["error"]
        assert result["error"]["technical_details"]["exception_type"] == "ValueError"


class TestErrorContext:
    """Test ErrorContext context manager."""
    
    def test_error_context_success(self):
        """Test context manager with successful operation."""
        with ErrorContext("test_operation", param="value"):
            result = "success"
        
        assert result == "success"
    
    def test_error_context_exception(self):
        """Test context manager with exception."""
        with pytest.raises(StockScannerError) as exc_info:
            with ErrorContext("test_operation", param="value"):
                raise ValueError("Test error")
        
        error = exc_info.value
        assert error.error_details.technical_details["operation"] == "test_operation"
        assert error.error_details.technical_details["param"] == "value"


class TestErrorIntegration:
    """Integration tests for error handling."""
    
    def test_validation_to_api_response(self):
        """Test complete flow from validation error to API response."""
        try:
            raise ValidationError("Invalid symbol", field="symbol", value="123")
        except Exception as exc:
            error = ErrorHandler.handle_exception(exc)
            response = ErrorHandler.create_error_response(error)
        
        assert response["success"] is False
        assert response["error"]["category"] == "validation"
        assert "Invalid symbol" in response["error"]["message"]
        assert len(response["error"]["recovery_suggestions"]) > 0
    
    @patch('app.utils.error_handling.logger')
    def test_error_logging_integration(self, mock_logger):
        """Test error logging integration."""
        error = APIError("API failed", api_name="yfinance", status_code=500)
        ErrorHandler.log_error(error, "req-123")
        
        # Verify logging was called
        assert mock_logger.error.called
        
        # Verify log content
        log_call = mock_logger.error.call_args[0][0]
        log_data = json.loads(log_call.split("High severity error: ")[1])
        
        assert log_data["error_category"] == "api_error"
        assert log_data["error_code"] == "API_ERROR_500"
        assert log_data["request_id"] == "req-123"