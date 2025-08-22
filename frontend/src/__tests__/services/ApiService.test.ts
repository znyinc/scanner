import { ApiService, handleApiError, getApiStatus } from '../../services/api';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios instance
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
};

mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

describe('ApiService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    ApiService.clearSettingsCache();
  });

  describe('retry logic', () => {
    test('should retry on network errors', async () => {
      const networkError = new Error('Network Error');
      networkError.name = 'NetworkError';

      // First two calls fail, third succeeds
      mockAxiosInstance.get
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce({ data: { test: 'data' } });

      const result = await ApiService.getSettings();

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ test: 'data' });
    });

    test('should retry on 5xx server errors', async () => {
      const serverError = {
        response: { status: 500, data: { detail: 'Internal Server Error' } },
      };

      // First call fails, second succeeds
      mockAxiosInstance.get
        .mockRejectedValueOnce(serverError)
        .mockResolvedValueOnce({ data: { test: 'data' } });

      const result = await ApiService.getSettings();

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ test: 'data' });
    });

    test('should not retry on 4xx client errors', async () => {
      const clientError = {
        response: { status: 400, data: { detail: 'Bad Request' } },
      };

      mockAxiosInstance.get.mockRejectedValueOnce(clientError);

      await expect(ApiService.getSettings()).rejects.toEqual(clientError);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
    });

    test('should stop retrying after max attempts', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.get.mockRejectedValue(networkError);

      await expect(ApiService.getSettings()).rejects.toEqual(networkError);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(4); // 1 initial + 3 retries
    });
  });

  describe('settings caching', () => {
    test('should cache settings and return from cache', async () => {
      const mockSettings = { atr_multiplier: 2.0 };
      mockAxiosInstance.get.mockResolvedValue({ data: mockSettings });

      // First call
      const result1 = await ApiService.getSettings();
      expect(result1).toEqual(mockSettings);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);

      // Second call should use cache
      const result2 = await ApiService.getSettings();
      expect(result2).toEqual(mockSettings);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1); // No additional call
    });

    test('should bypass cache when requested', async () => {
      const mockSettings = { atr_multiplier: 2.0 };
      mockAxiosInstance.get.mockResolvedValue({ data: mockSettings });

      // First call
      await ApiService.getSettings();
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);

      // Second call with useCache=false
      await ApiService.getSettings(false);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
    });

    test('should update cache when settings are updated', async () => {
      const originalSettings = { atr_multiplier: 2.0 };
      const updatedSettings = { atr_multiplier: 3.0 };

      mockAxiosInstance.get.mockResolvedValue({ data: originalSettings });
      mockAxiosInstance.put.mockResolvedValue({ data: updatedSettings });

      // Load initial settings
      await ApiService.getSettings();

      // Update settings
      await ApiService.updateSettings(updatedSettings);

      // Get settings again - should return updated from cache
      mockAxiosInstance.get.mockClear();
      const result = await ApiService.getSettings();
      
      expect(result).toEqual(updatedSettings);
      expect(mockAxiosInstance.get).not.toHaveBeenCalled(); // Used cache
    });
  });

  describe('progress callbacks', () => {
    test('should call progress callback during scan', async () => {
      const mockResult = { id: 'scan-123', signals_found: [] };
      const progressCallback = jest.fn();

      mockAxiosInstance.post.mockResolvedValue({ data: mockResult });

      await ApiService.initiateScan(['AAPL'], {} as any, progressCallback);

      expect(progressCallback).toHaveBeenCalledWith(0, 'Starting scan...');
      expect(progressCallback).toHaveBeenCalledWith(100, 'Scan completed');
    });

    test('should call progress callback during backtest', async () => {
      const mockResult = { id: 'backtest-123', trades: [] };
      const progressCallback = jest.fn();

      mockAxiosInstance.post.mockResolvedValue({ data: mockResult });

      await ApiService.runBacktest(['AAPL'], '2023-01-01', '2023-12-01', {} as any, progressCallback);

      expect(progressCallback).toHaveBeenCalledWith(0, 'Starting backtest...');
      expect(progressCallback).toHaveBeenCalledWith(100, 'Backtest completed');
    });
  });

  describe('health check', () => {
    test('should return true for successful health check', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { status: 'ok' } });

      const result = await ApiService.healthCheck();

      expect(result).toBe(true);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health', { timeout: 5000 });
    });

    test('should return false for failed health check', async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error('Connection failed'));

      const result = await ApiService.healthCheck();

      expect(result).toBe(false);
    });
  });
});

describe('handleApiError', () => {
  test('should handle response errors with detail', () => {
    const error = {
      response: {
        status: 400,
        data: { detail: 'Invalid input' },
      },
    };

    const result = handleApiError(error);
    expect(result).toBe('Invalid input');
  });

  test('should handle response errors with message', () => {
    const error = {
      response: {
        status: 500,
        data: { message: 'Server error' },
      },
    };

    const result = handleApiError(error);
    expect(result).toBe('Server error');
  });

  test('should handle specific HTTP status codes', () => {
    const testCases = [
      { status: 401, expected: 'Authentication required. Please log in.' },
      { status: 403, expected: 'Access denied. You do not have permission to perform this action.' },
      { status: 404, expected: 'The requested resource was not found.' },
      { status: 429, expected: 'Too many requests. Please wait a moment and try again.' },
      { status: 502, expected: 'Server is temporarily unavailable. Please try again later.' },
    ];

    testCases.forEach(({ status, expected }) => {
      const error = { response: { status, data: {} } };
      const result = handleApiError(error);
      expect(result).toBe(expected);
    });
  });

  test('should handle request errors (no response)', () => {
    const error = { request: {} };
    const result = handleApiError(error);
    expect(result).toBe('Unable to connect to server. Please check your internet connection.');
  });

  test('should handle timeout errors', () => {
    const error = { code: 'ECONNABORTED', message: 'timeout' };
    const result = handleApiError(error);
    expect(result).toBe('Request timed out. The operation is taking longer than expected.');
  });

  test('should handle generic errors', () => {
    const error = { message: 'Something went wrong' };
    const result = handleApiError(error);
    expect(result).toBe('Something went wrong');
  });

  test('should handle errors without message', () => {
    const error = {};
    const result = handleApiError(error);
    expect(result).toBe('An unexpected error occurred');
  });
});

describe('getApiStatus', () => {
  test('should return online for healthy API', async () => {
    mockAxiosInstance.get.mockResolvedValue({ data: { status: 'ok' } });

    const result = await getApiStatus();
    expect(result).toBe('online');
  });

  test('should return error for unhealthy API', async () => {
    mockAxiosInstance.get.mockResolvedValue({ data: { status: 'error' } });
    // Mock healthCheck to return false
    jest.spyOn(ApiService, 'healthCheck').mockResolvedValue(false);

    const result = await getApiStatus();
    expect(result).toBe('error');
  });

  test('should return offline for connection errors', async () => {
    jest.spyOn(ApiService, 'healthCheck').mockRejectedValue(new Error('Connection failed'));

    const result = await getApiStatus();
    expect(result).toBe('offline');
  });
});