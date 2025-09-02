"""
Tests for error handling utilities.
"""

import pytest
from unittest.mock import Mock, patch

from app.utils.error_handling import (
    StockScannerError, ValidationError, ErrorHandler, ErrorContext, handle_errors
)


class TestBasicErrorHandling:
    """Test basic error handling functionality."""
    
    def test_stock_scanner_error_creation(self):
        """Test creating StockScannerError."""
        error = StockScannerError("Test error message")
        
        assert str(error) == "Test error message"
        assert hasattr(error, 'error_details')
    
    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid input")
        
        assert str(error) == "Invalid input"


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_handle_exception(self):
        """Test handling generic exception."""
        exc = ValueError("Test error")
        result = ErrorHandler.handle_exception(exc)
        
        assert isinstance(result, StockScannerError)
        assert str(result) == "Test error"
    
    def test_handle_exception_with_context(self):
        """Test handling exception with context."""
        exc = ValueError("Test error")
        context = {"operation": "test_op"}
        result = ErrorHandler.handle_exception(exc, context)
        
        assert isinstance(result, StockScannerError)
        assert str(result) == "Test error"
    
    def test_log_error(self):
        """Test error logging."""
        error = StockScannerError("Test error")
        # Should not raise an exception
        ErrorHandler.log_error(error)
        ErrorHandler.log_error(error, "request-123")
    
    def test_create_error_response(self):
        """Test creating error response."""
        error = StockScannerError("Test error")
        response = ErrorHandler.create_error_response(error)
        
        assert "error" in response
        assert response["error"]["message"] == "Test error"


class TestErrorContext:
    """Test ErrorContext context manager."""
    
    def test_error_context_creation(self):
        """Test creating ErrorContext."""
        context = ErrorContext("test_operation", request_id="123")
        
        assert context.operation == "test_operation"
        assert context.request_id == "123"
    
    def test_error_context_manager(self):
        """Test context manager functionality."""
        with ErrorContext("test_operation") as ctx:
            assert ctx.operation == "test_operation"
        
        # Should not raise any exceptions


class TestErrorDecorator:
    """Test error handling decorator."""
    
    def test_handle_errors_decorator(self):
        """Test decorator functionality."""
        @handle_errors()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_handle_errors_decorator_with_exception(self):
        """Test decorator with exception."""
        @handle_errors()
        def test_function():
            raise ValueError("Test error")
        
        # The current implementation just returns the function as-is
        # so it will still raise the exception
        with pytest.raises(ValueError, match="Test error"):
            test_function()


