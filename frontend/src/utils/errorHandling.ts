/**
 * Frontend error handling utilities for the stock scanner application.
 * Provides error classification, user-friendly error messages, and recovery suggestions.
 */

import { ApiError, ErrorCategory, ErrorSeverity } from '../types';

/**
 * Handle API errors and convert them to standardized ApiError format
 */
export function handleApiError(error: any): ApiError {
  // If it's already a structured backend error, use it
  if (error?.response?.data?.error) {
    const backendError = error.response.data.error;
    return {
      code: backendError.code,
      message: backendError.message || backendError.user_message,
      category: backendError.category as ErrorCategory,
      severity: backendError.severity as ErrorSeverity,
      recovery_suggestions: backendError.recovery_suggestions || [],
      timestamp: backendError.timestamp || new Date().toISOString(),
      request_id: backendError.request_id,
      technical_details: backendError.technical_details
    };
  }

  // Handle HTTP response errors
  if (error?.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return {
          code: 'BAD_REQUEST',
          message: data?.detail || data?.message || 'Bad request',
          category: 'validation',
          severity: 'medium',
          recovery_suggestions: [
            'Check your input format and try again',
            'Ensure all required fields are provided'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 401:
        return {
          code: 'UNAUTHORIZED',
          message: data?.detail || 'Authentication required',
          category: 'authentication',
          severity: 'high',
          recovery_suggestions: [
            'Please log in to continue',
            'Check your credentials and try again'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 403:
        return {
          code: 'FORBIDDEN',
          message: data?.detail || 'Access denied',
          category: 'permission',
          severity: 'high',
          recovery_suggestions: [
            'You do not have permission to perform this action',
            'Contact support if you believe this is an error'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 404:
        return {
          code: 'NOT_FOUND',
          message: data?.detail || 'Resource not found',
          category: 'api_error',
          severity: 'medium',
          recovery_suggestions: [
            'Check the URL and try again',
            'The requested resource may no longer exist'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 422:
        return {
          code: 'VALIDATION_ERROR',
          message: data?.detail || 'Validation failed',
          category: 'validation',
          severity: 'medium',
          recovery_suggestions: [
            'Check your input format',
            'Ensure all fields meet the required criteria'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 429:
        return {
          code: 'RATE_LIMITED',
          message: data?.detail || 'Too many requests',
          category: 'rate_limit',
          severity: 'medium',
          recovery_suggestions: [
            'Please wait a moment before trying again',
            'Reduce the number of requests you are making',
            'Consider upgrading your plan for higher limits'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 500:
        return {
          code: 'INTERNAL_SERVER_ERROR',
          message: data?.detail || 'Internal server error',
          category: 'system',
          severity: 'high',
          recovery_suggestions: [
            'Please try again in a few moments',
            'Contact support if the problem persists'
          ],
          timestamp: new Date().toISOString()
        };
        
      case 503:
        return {
          code: 'SERVICE_UNAVAILABLE',
          message: data?.detail || 'Service temporarily unavailable',
          category: 'system',
          severity: 'high',
          recovery_suggestions: [
            'The service is temporarily down for maintenance',
            'Please try again later',
            'Check our status page for updates'
          ],
          timestamp: new Date().toISOString()
        };
        
      default:
        return {
          code: `HTTP_${status}`,
          message: data?.detail || data?.message || `HTTP ${status} error`,
          category: 'api_error',
          severity: 'medium',
          recovery_suggestions: [
            'Please try again',
            'Contact support if the problem persists'
          ],
          timestamp: new Date().toISOString()
        };
    }
  }

  // Handle network errors (no response received)
  if (error?.request) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server',
      category: 'network',
      severity: 'high',
      recovery_suggestions: [
        'Check your internet connection',
        'Try again in a few moments',
        'Contact support if the problem persists'
      ],
      timestamp: new Date().toISOString()
    };
  }

  // Handle timeout errors
  if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
    return {
      code: 'TIMEOUT_ERROR',
      message: 'Request timed out',
      category: 'timeout',
      severity: 'medium',
      recovery_suggestions: [
        'The request took too long to complete',
        'Try again with fewer items',
        'Check your internet connection'
      ],
      timestamp: new Date().toISOString()
    };
  }

  // Handle unknown errors
  return {
    code: 'UNKNOWN_ERROR',
    message: error?.message || 'An unexpected error occurred',
    category: 'system',
    severity: 'medium',
    recovery_suggestions: [
      'Please try again',
      'Refresh the page if the problem persists',
      'Contact support for assistance'
    ],
    timestamp: new Date().toISOString()
  };
}

/**
 * Check if the user is online
 */
export function checkNetworkStatus(): boolean {
  return navigator.onLine;
}

/**
 * Get API service status
 */
export async function getApiStatus(): Promise<'online' | 'offline' | 'error'> {
  try {
    // Simple health check - this would be implemented based on your API
    const response = await fetch('/api/health', {
      method: 'GET',
      timeout: 5000
    } as any);
    
    if (response.ok) {
      return 'online';
    } else {
      return 'error';
    }
  } catch (error) {
    return 'offline';
  }
}

/**
 * Format error message for display to users
 */
export function formatErrorMessage(error: ApiError): string {
  let message = error.message;
  
  // Add context based on category
  switch (error.category) {
    case 'validation':
      message = `Input Error: ${message}`;
      break;
    case 'network':
      message = `Connection Error: ${message}`;
      break;
    case 'rate_limit':
      message = `Rate Limit: ${message}`;
      break;
    case 'authentication':
      message = `Authentication: ${message}`;
      break;
    case 'permission':
      message = `Permission: ${message}`;
      break;
    case 'system':
      message = `System Error: ${message}`;
      break;
  }
  
  return message;
}

/**
 * Get appropriate CSS class for error severity
 */
export function getErrorSeverityClass(severity: ErrorSeverity): string {
  switch (severity) {
    case 'low':
      return 'error-low';
    case 'medium':
      return 'error-medium';
    case 'high':
      return 'error-high';
    case 'critical':
      return 'error-critical';
    default:
      return 'error-medium';
  }
}

/**
 * Determine if an error should trigger a retry
 */
export function shouldRetry(error: ApiError): boolean {
  // Don't retry validation errors or authentication errors
  if (error.category === 'validation' || error.category === 'authentication') {
    return false;
  }
  
  // Don't retry rate limit errors immediately
  if (error.category === 'rate_limit') {
    return false;
  }
  
  // Retry network, timeout, and some system errors
  return ['network', 'timeout', 'system'].includes(error.category);
}

/**
 * Get retry delay in milliseconds based on error type
 */
export function getRetryDelay(error: ApiError, attempt: number): number {
  const baseDelay = 1000; // 1 second
  const maxDelay = 30000; // 30 seconds
  
  let delay = baseDelay;
  
  // Exponential backoff for most errors
  if (error.category === 'network' || error.category === 'timeout') {
    delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  }
  
  // Longer delay for rate limit errors
  if (error.category === 'rate_limit') {
    delay = Math.min(baseDelay * 10 * attempt, maxDelay * 2);
  }
  
  return delay;
}

/**
 * Log error for debugging (in development) or monitoring (in production)
 */
export function logError(error: ApiError, context?: Record<string, any>): void {
  const logData = {
    ...error,
    context,
    userAgent: navigator.userAgent,
    url: window.location.href,
    timestamp: new Date().toISOString()
  };
  
  if (process.env.NODE_ENV === 'development') {
    console.error('API Error:', logData);
  } else {
    // In production, you might send this to a logging service
    // Example: sendToLoggingService(logData);
  }
}

/**
 * Create a user-friendly error notification
 */
export function createErrorNotification(error: ApiError): {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  actions?: Array<{ label: string; action: () => void }>;
} {
  let type: 'error' | 'warning' | 'info' = 'error';
  
  if (error.severity === 'low') {
    type = 'info';
  } else if (error.severity === 'medium') {
    type = 'warning';
  }
  
  const notification = {
    title: getErrorTitle(error),
    message: error.message,
    type,
    actions: [] as Array<{ label: string; action: () => void }>
  };
  
  // Add retry action if appropriate
  if (shouldRetry(error)) {
    notification.actions.push({
      label: 'Retry',
      action: () => {
        // This would be implemented by the calling component
        console.log('Retry action triggered');
      }
    });
  }
  
  return notification;
}

/**
 * Get appropriate title for error notification
 */
function getErrorTitle(error: ApiError): string {
  switch (error.category) {
    case 'validation':
      return 'Invalid Input';
    case 'network':
      return 'Connection Problem';
    case 'rate_limit':
      return 'Rate Limit Exceeded';
    case 'authentication':
      return 'Authentication Required';
    case 'permission':
      return 'Access Denied';
    case 'timeout':
      return 'Request Timeout';
    case 'system':
      return 'System Error';
    default:
      return 'Error';
  }
}