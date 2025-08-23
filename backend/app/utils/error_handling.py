"""Simple error handling for stock scanner."""

class ErrorHandler:
    """Simple error handler."""
    
    @staticmethod
    def handle_exception(exc, context=None):
        """Handle exceptions."""
        return StockScannerError(str(exc))
    
    @staticmethod
    def log_error(error, request_id=None):
        """Log error."""
        print(f"Error: {error}")
    
    @staticmethod
    def create_error_response(error):
        """Create error response."""
        return {"error": {"message": str(error)}}

class ValidationError(Exception):
    """Validation error."""
    pass

class StockScannerError(Exception):
    """Base error."""
    def __init__(self, message):
        super().__init__(message)
        self.error_details = type('ErrorDetails', (), {
            'category': type('Category', (), {'value': 'system'})()
        })()

def handle_errors():
    """Error decorator."""
    def decorator(func):
        return func
    return decorator

class ErrorContext:
    """Error context."""
    def __init__(self, operation, request_id=None, symbols_count=None, **kwargs):
        self.operation = operation
        self.request_id = request_id
        self.symbols_count = symbols_count
        self.extra_context = kwargs
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the error with context
            context_info = f"Operation: {self.operation}"
            if self.request_id:
                context_info += f", Request ID: {self.request_id}"
            if self.symbols_count:
                context_info += f", Symbols Count: {self.symbols_count}"
            print(f"Error in {context_info}: {exc_val}")
        return False