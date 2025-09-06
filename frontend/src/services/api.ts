import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { AlgorithmSettings, ScanResult, BacktestResult, HistoryFilters, ApiError, EnhancedScanResult } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Progress callback type for long-running operations
export type ProgressCallback = (progress: number, message?: string) => void;

// Retry configuration
interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition?: (error: any) => boolean;
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 1, // Reduced from 3 to 1 to prevent multiple scans
  retryDelay: 1000,
  retryCondition: (error) => {
    // Only retry on network errors, not server errors for scans
    return !error.response;
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds timeout for long-running operations
});

// Request interceptor for adding common headers
if (api.interceptors?.request) {
  api.interceptors.request.use((config) => {
    config.headers['Content-Type'] = 'application/json';
    return config;
  });
}

// Response interceptor for handling common errors
if (api.interceptors?.response) {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('API Error:', error);
      return Promise.reject(error);
    }
  );
}

export class ApiService {
  // Generic retry wrapper
  private static async withRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig = defaultRetryConfig
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        if (attempt === config.maxRetries || !config.retryCondition?.(error)) {
          throw error;
        }
        
        // Wait before retrying with exponential backoff
        const delay = config.retryDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }

  // Enhanced scan endpoint with progress tracking
  static async initiateScan(
    symbols: string[], 
    settings: AlgorithmSettings,
    onProgress?: ProgressCallback
  ): Promise<ScanResult> {
    
    return this.withRetry(async () => {
      onProgress?.(0, 'Starting scan...');
      
      const response = await api.post('/scan/', {
        symbols,
        settings
      });
      onProgress?.(100, 'Scan completed');
      return response.data;
    });
  }

  static async getScanHistory(filters?: HistoryFilters): Promise<EnhancedScanResult[]> {
    return this.withRetry(async () => {
      const response = await api.get('/scan/history', { params: filters });
      return response.data;
    });
  }

  // Get basic market data for a single symbol
  static async getMarketData(symbol: string): Promise<{
    symbol: string;
    lastPrice: number;
    priceChange: number;
    priceChangePercent: number;
    volume: number;
    exchange: string;
  }> {
    return this.withRetry(async () => {
      const response = await api.get(`/market-data/${symbol}`);
      return response.data;
    });
  }

  // Enhanced backtest endpoint with progress tracking
  static async runBacktest(
    symbols: string[], 
    startDate: string, 
    endDate: string, 
    settings: AlgorithmSettings,
    onProgress?: ProgressCallback
  ): Promise<BacktestResult> {
    return this.withRetry(async () => {
      onProgress?.(0, 'Starting backtest...');
      
      const response = await api.post('/backtest', {
        symbols,
        start_date: startDate,
        end_date: endDate,
        settings
      });
      
      onProgress?.(100, 'Backtest completed');
      return response.data;
    }, { ...defaultRetryConfig, maxRetries: 1 }); // Fewer retries for long operations
  }

  static async getBacktestHistory(filters?: HistoryFilters): Promise<BacktestResult[]> {
    return this.withRetry(async () => {
      const response = await api.get('/backtest/history', { params: filters });
      return response.data;
    });
  }

  // Settings endpoints with caching
  private static settingsCache: { data: AlgorithmSettings; timestamp: number } | null = null;
  private static readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static async getSettings(useCache: boolean = true): Promise<AlgorithmSettings> {
    if (useCache && this.settingsCache) {
      const now = Date.now();
      if (now - this.settingsCache.timestamp < this.CACHE_DURATION) {
        return this.settingsCache.data;
      }
    }

    return this.withRetry(async () => {
      const response = await api.get('/settings');
      
      // Update cache
      this.settingsCache = {
        data: response.data,
        timestamp: Date.now()
      };
      
      return response.data;
    });
  }

  static async updateSettings(settings: AlgorithmSettings): Promise<AlgorithmSettings> {
    return this.withRetry(async () => {
      const response = await api.put('/settings', settings);
      
      // Update cache
      this.settingsCache = {
        data: response.data,
        timestamp: Date.now()
      };
      
      return response.data;
    });
  }

  // Health check endpoint
  static async healthCheck(): Promise<boolean> {
    try {
      await api.get('/health', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  // Clear settings cache
  static clearSettingsCache(): void {
    this.settingsCache = null;
  }
}

// Enhanced error handling utility
export const handleApiError = (error: any): ApiError => {
  let apiError: ApiError;
  
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    // Check if response contains structured error from backend
    if (data?.error && typeof data.error === 'object') {
      apiError = {
        code: data.error.code || `HTTP_${status}`,
        message: data.error.message || 'An error occurred',
        category: data.error.category || 'api_error',
        severity: data.error.severity || 'medium',
        recovery_suggestions: data.error.recovery_suggestions || [],
        timestamp: data.error.timestamp,
        request_id: data.error.request_id,
        technical_details: data.error.technical_details
      };
    } else {
      // Handle specific HTTP status codes
      switch (status) {
        case 400:
          apiError = {
            code: 'BAD_REQUEST',
            message: data?.detail || 'Invalid request. Please check your input.',
            category: 'validation',
            severity: 'medium',
            recovery_suggestions: [
              'Check your input format',
              'Ensure all required fields are provided',
              'Refer to the API documentation'
            ]
          };
          break;
        case 401:
          apiError = {
            code: 'UNAUTHORIZED',
            message: 'Authentication required. Please log in.',
            category: 'authentication',
            severity: 'high',
            recovery_suggestions: [
              'Log in to your account',
              'Check your credentials',
              'Contact support if the problem persists'
            ]
          };
          break;
        case 403:
          apiError = {
            code: 'FORBIDDEN',
            message: 'Access denied. You do not have permission to perform this action.',
            category: 'permission',
            severity: 'high',
            recovery_suggestions: [
              'Contact your administrator for access',
              'Check your account permissions',
              'Try logging out and back in'
            ]
          };
          break;
        case 404:
          apiError = {
            code: 'NOT_FOUND',
            message: 'The requested resource was not found.',
            category: 'api_error',
            severity: 'medium',
            recovery_suggestions: [
              'Check the URL or resource identifier',
              'Try refreshing the page',
              'Contact support if the resource should exist'
            ]
          };
          break;
        case 422:
          apiError = {
            code: 'VALIDATION_ERROR',
            message: data?.detail || 'Validation error. Please check your input.',
            category: 'validation',
            severity: 'medium',
            recovery_suggestions: [
              'Check input format and values',
              'Ensure all required fields are valid',
              'Refer to field-specific error messages'
            ]
          };
          break;
        case 429:
          apiError = {
            code: 'RATE_LIMITED',
            message: 'Too many requests. Please wait a moment and try again.',
            category: 'rate_limit',
            severity: 'medium',
            recovery_suggestions: [
              'Wait a few moments before trying again',
              'Reduce the frequency of requests',
              'Contact support for rate limit increases'
            ]
          };
          break;
        case 500:
          apiError = {
            code: 'INTERNAL_SERVER_ERROR',
            message: 'Internal server error. Please try again later.',
            category: 'system',
            severity: 'high',
            recovery_suggestions: [
              'Try again in a few moments',
              'Check if the issue persists',
              'Contact support if the problem continues'
            ]
          };
          break;
        case 502:
        case 503:
        case 504:
          apiError = {
            code: 'SERVICE_UNAVAILABLE',
            message: 'Server is temporarily unavailable. Please try again later.',
            category: 'system',
            severity: 'high',
            recovery_suggestions: [
              'Wait a few minutes and try again',
              'Check your internet connection',
              'Contact support if the service remains unavailable'
            ]
          };
          break;
        default:
          apiError = {
            code: `HTTP_${status}`,
            message: data?.detail || data?.message || `Server error (${status})`,
            category: 'api_error',
            severity: 'medium',
            recovery_suggestions: [
              'Try the request again',
              'Check your input',
              'Contact support if the problem persists'
            ]
          };
      }
    }
  } else if (error.request) {
    // Request was made but no response received
    apiError = {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to server. Please check your internet connection.',
      category: 'network',
      severity: 'high',
      recovery_suggestions: [
        'Check your internet connection',
        'Try again in a few moments',
        'Contact your network administrator if the problem persists'
      ]
    };
  } else if (error.code === 'ECONNABORTED') {
    // Request timeout
    apiError = {
      code: 'TIMEOUT_ERROR',
      message: 'Request timed out. The operation is taking longer than expected.',
      category: 'timeout',
      severity: 'medium',
      recovery_suggestions: [
        'Try again with fewer items',
        'Check your internet connection',
        'Contact support if timeouts persist'
      ]
    };
  } else {
    // Something else happened
    apiError = {
      code: 'UNKNOWN_ERROR',
      message: error.message || 'An unexpected error occurred',
      category: 'system',
      severity: 'medium',
      recovery_suggestions: [
        'Try refreshing the page',
        'Try the operation again',
        'Contact support if the problem persists'
      ]
    };
  }
  
  // Add timestamp if not present
  if (!apiError.timestamp) {
    apiError.timestamp = new Date().toISOString();
  }
  
  return apiError;
};

// Network status utility
export const checkNetworkStatus = (): boolean => {
  return navigator.onLine;
};

// API status utility
export const getApiStatus = async (): Promise<'online' | 'offline' | 'error'> => {
  try {
    const isHealthy = await ApiService.healthCheck();
    return isHealthy ? 'online' : 'error';
  } catch {
    return 'offline';
  }
};