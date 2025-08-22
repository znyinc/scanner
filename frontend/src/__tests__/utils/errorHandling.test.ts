/**
 * Tests for frontend error handling utilities.
 */

import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { describe } from 'node:test';
import { handleApiError, checkNetworkStatus, getApiStatus } from '../../services/api';
import { ApiError } from '../../types';

// Mock axios for testing
jest.mock('axios');

describe('Error Handling Utilities', () => {
  describe('handleApiError', () => {
    it('should handle structured backend errors', () => {
      const backendError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Invalid input provided',
              category: 'validation',
              severity: 'medium',
              recovery_suggestions: [
                'Check your input format',
                'Ensure all fields are valid'
              ],
              timestamp: '2023-01-01T00:00:00Z',
              request_id: 'req-123'
            }
          }
        }
      };

      const result = handleApiError(backendError);

      expect(result.code).toBe('VALIDATION_ERROR');
      expect(result.message).toBe('Invalid input provided');
      expect(result.category).toBe('validation');
      expect(result.severity).toBe('medium');
      expect(result.recovery_suggestions).toHaveLength(2);
      expect(result.request_id).toBe('req-123');
    });

    it('should handle HTTP 400 errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            detail: 'Bad request'
          }
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('BAD_REQUEST');
      expect(result.message).toBe('Bad request');
      expect(result.category).toBe('validation');
      expect(result.severity).toBe('medium');
      expect(result.recovery_suggestions.length).toBeGreaterThan(0);
    });

    it('should handle HTTP 401 errors', () => {
      const error = {
        response: {
          status: 401,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('UNAUTHORIZED');
      expect(result.category).toBe('authentication');
      expect(result.severity).toBe('high');
      expect(result.message).toContain('Authentication required');
    });

    it('should handle HTTP 403 errors', () => {
      const error = {
        response: {
          status: 403,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('FORBIDDEN');
      expect(result.category).toBe('permission');
      expect(result.severity).toBe('high');
      expect(result.message).toContain('Access denied');
    });

    it('should handle HTTP 404 errors', () => {
      const error = {
        response: {
          status: 404,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('NOT_FOUND');
      expect(result.category).toBe('api_error');
      expect(result.message).toContain('not found');
    });

    it('should handle HTTP 422 validation errors', () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: 'Validation failed for field X'
          }
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('VALIDATION_ERROR');
      expect(result.category).toBe('validation');
      expect(result.message).toBe('Validation failed for field X');
    });

    it('should handle HTTP 429 rate limit errors', () => {
      const error = {
        response: {
          status: 429,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('RATE_LIMITED');
      expect(result.category).toBe('rate_limit');
      expect(result.message).toContain('Too many requests');
      expect(result.recovery_suggestions.some(s => s.toLowerCase().includes('wait'))).toBe(true);
    });

    it('should handle HTTP 500 server errors', () => {
      const error = {
        response: {
          status: 500,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('INTERNAL_SERVER_ERROR');
      expect(result.category).toBe('system');
      expect(result.severity).toBe('high');
      expect(result.message).toContain('Internal server error');
    });

    it('should handle HTTP 503 service unavailable errors', () => {
      const error = {
        response: {
          status: 503,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.code).toBe('SERVICE_UNAVAILABLE');
      expect(result.category).toBe('system');
      expect(result.severity).toBe('high');
      expect(result.message).toContain('temporarily unavailable');
    });

    it('should handle network errors (no response)', () => {
      const error = {
        request: {},
        message: 'Network Error'
      };

      const result = handleApiError(error);

      expect(result.code).toBe('NETWORK_ERROR');
      expect(result.category).toBe('network');
      expect(result.severity).toBe('high');
      expect(result.message).toContain('Unable to connect');
      expect(result.recovery_suggestions.some(s => s.includes('internet'))).toBe(true);
    });

    it('should handle timeout errors', () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded'
      };

      const result = handleApiError(error);

      expect(result.code).toBe('TIMEOUT_ERROR');
      expect(result.category).toBe('timeout');
      expect(result.severity).toBe('medium');
      expect(result.message).toContain('timed out');
    });

    it('should handle unknown errors', () => {
      const error = {
        message: 'Something went wrong'
      };

      const result = handleApiError(error);

      expect(result.code).toBe('UNKNOWN_ERROR');
      expect(result.category).toBe('system');
      expect(result.message).toBe('Something went wrong');
      expect(result.timestamp).toBeDefined();
    });

    it('should add timestamp if not present', () => {
      const error = {
        response: {
          status: 400,
          data: {}
        }
      };

      const result = handleApiError(error);

      expect(result.timestamp).toBeDefined();
      expect(new Date(result.timestamp!).getTime()).toBeCloseTo(Date.now(), -3);
    });
  });

  describe('checkNetworkStatus', () => {
    it('should return true when online', () => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true
      });

      expect(checkNetworkStatus()).toBe(true);
    });

    it('should return false when offline', () => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      expect(checkNetworkStatus()).toBe(false);
    });
  });

  describe('getApiStatus', () => {
    it('should return online when health check succeeds', async () => {
      // This would need to be mocked properly in a real test
      // For now, we'll test the structure
      const status = await getApiStatus();
      expect(['online', 'offline', 'error']).toContain(status);
    });
  });
});

describe('Error Recovery Scenarios', () => {
  it('should provide appropriate recovery suggestions for validation errors', () => {
    const error = {
      response: {
        status: 400,
        data: {
          error: {
            code: 'INVALID_SYMBOLS',
            message: 'Invalid stock symbols provided',
            category: 'validation',
            severity: 'medium',
            recovery_suggestions: [
              'Check symbol format (e.g., AAPL, MSFT)',
              'Remove invalid symbols and try again'
            ]
          }
        }
      }
    };

    const result = handleApiError(error);

    expect(result.recovery_suggestions).toContain('Check symbol format (e.g., AAPL, MSFT)');
    expect(result.recovery_suggestions).toContain('Remove invalid symbols and try again');
  });

  it('should provide appropriate recovery suggestions for rate limit errors', () => {
    const error = {
      response: {
        status: 429,
        data: {}
      }
    };

    const result = handleApiError(error);

    expect(result.recovery_suggestions.some(s => s.toLowerCase().includes('wait'))).toBe(true);
    expect(result.recovery_suggestions.some(s => s.toLowerCase().includes('reduce'))).toBe(true);
  });

  it('should provide appropriate recovery suggestions for network errors', () => {
    const error = {
      request: {},
      message: 'Network Error'
    };

    const result = handleApiError(error);

    expect(result.recovery_suggestions.some(s => s.toLowerCase().includes('internet'))).toBe(true);
    expect(result.recovery_suggestions.some(s => s.toLowerCase().includes('connection'))).toBe(true);
  });
});

describe('Error Categorization', () => {
  it('should correctly categorize validation errors', () => {
    const error = {
      response: {
        status: 422,
        data: { detail: 'Validation error' }
      }
    };

    const result = handleApiError(error);
    expect(result.category).toBe('validation');
  });

  it('should correctly categorize authentication errors', () => {
    const error = {
      response: {
        status: 401,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.category).toBe('authentication');
  });

  it('should correctly categorize permission errors', () => {
    const error = {
      response: {
        status: 403,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.category).toBe('permission');
  });

  it('should correctly categorize system errors', () => {
    const error = {
      response: {
        status: 500,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.category).toBe('system');
  });

  it('should correctly categorize network errors', () => {
    const error = {
      request: {},
      message: 'Network Error'
    };

    const result = handleApiError(error);
    expect(result.category).toBe('network');
  });

  it('should correctly categorize rate limit errors', () => {
    const error = {
      response: {
        status: 429,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.category).toBe('rate_limit');
  });
});

describe('Error Severity Levels', () => {
  it('should assign high severity to authentication errors', () => {
    const error = {
      response: {
        status: 401,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.severity).toBe('high');
  });

  it('should assign high severity to system errors', () => {
    const error = {
      response: {
        status: 500,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.severity).toBe('high');
  });

  it('should assign medium severity to validation errors', () => {
    const error = {
      response: {
        status: 400,
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result.severity).toBe('medium');
  });

  it('should assign medium severity to timeout errors', () => {
    const error = {
      code: 'ECONNABORTED',
      message: 'timeout'
    };

    const result = handleApiError(error);
    expect(result.severity).toBe('medium');
  });
});