import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HistoryViewer from '../HistoryViewer';
import { ApiService } from '../../services/api';
import { ScanResult } from '../../types';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Mock scan result with diagnostics
const mockScanWithDiagnostics: ScanResult = {
  id: 'test-scan-1',
  timestamp: '2025-09-03T13:19:24.000Z',
  symbols_scanned: ['AAPL', 'MSFT', 'INVALID123'],
  signals_found: [],
  settings_used: {
    atr_multiplier: 2.0,
    ema5_rising_threshold: 0.001,
    ema8_rising_threshold: 0.001,
    ema21_rising_threshold: 0.001,
    volatility_filter: 0.02,
    fomo_filter: 0.05,
    higher_timeframe: '15m'
  },
  execution_time: 3.04,
  scan_status: 'partial',
  error_message: 'Some symbols failed to process',
  diagnostics: {
    symbols_with_data: ['AAPL'],
    symbols_without_data: ['MSFT', 'INVALID123'],
    symbols_with_errors: {
      'INVALID123': 'Invalid symbol format'
    },
    data_fetch_time: 2.85,
    algorithm_time: 0.19,
    total_data_points: {
      'AAPL': 150,
      'MSFT': 0,
      'INVALID123': 0
    },
    error_summary: {
      'data_fetch_error': 2,
      'insufficient_data': 1
    }
  }
};

describe('HistoryViewer Diagnostics', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock API responses
    mockApiService.getScanHistory.mockResolvedValue([mockScanWithDiagnostics]);
    mockApiService.getBacktestHistory.mockResolvedValue([]);
  });

  test('displays scan status in table', async () => {
    render(<HistoryViewer />);
    
    await waitFor(() => {
      expect(screen.getByText('partial')).toBeInTheDocument();
    });
  });

  test('shows diagnostic summary in mobile card view', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 400,
    });
    
    render(<HistoryViewer />);
    
    await waitFor(() => {
      expect(screen.getByText(/Data: 1 success, 2 no data, 1 errors/)).toBeInTheDocument();
    });
  });

  test('displays comprehensive diagnostics in detail dialog', async () => {
    render(<HistoryViewer />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('partial')).toBeInTheDocument();
    });
    
    // Click view button to open detail dialog
    const viewButton = screen.getByLabelText(/View scan details/);
    fireEvent.click(viewButton);
    
    // Check for diagnostic information
    await waitFor(() => {
      expect(screen.getByText('Diagnostic Information')).toBeInTheDocument();
      expect(screen.getByText('Data Availability')).toBeInTheDocument();
      expect(screen.getByText('✅ Symbols with data (1):')).toBeInTheDocument();
      expect(screen.getByText('⚠️ Symbols without data (2):')).toBeInTheDocument();
      expect(screen.getByText('❌ Symbols with errors (1):')).toBeInTheDocument();
      expect(screen.getByText('Performance Breakdown')).toBeInTheDocument();
      expect(screen.getByText('2.85s')).toBeInTheDocument(); // Data fetch time
      expect(screen.getByText('0.19s')).toBeInTheDocument(); // Algorithm time
    });
  });

  test('shows error message when scan failed', async () => {
    const failedScan = {
      ...mockScanWithDiagnostics,
      scan_status: 'failed',
      error_message: 'All symbols failed to process'
    };
    
    mockApiService.getScanHistory.mockResolvedValue([failedScan]);
    
    render(<HistoryViewer />);
    
    // Wait for data to load and open detail dialog
    await waitFor(() => {
      expect(screen.getByText('failed')).toBeInTheDocument();
    });
    
    const viewButton = screen.getByLabelText(/View scan details/);
    fireEvent.click(viewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Error Details')).toBeInTheDocument();
      expect(screen.getByText('All symbols failed to process')).toBeInTheDocument();
    });
  });

  test('displays data points for each symbol', async () => {
    render(<HistoryViewer />);
    
    await waitFor(() => {
      expect(screen.getByText('partial')).toBeInTheDocument();
    });
    
    const viewButton = screen.getByLabelText(/View scan details/);
    fireEvent.click(viewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Data Points Retrieved')).toBeInTheDocument();
      expect(screen.getByText('AAPL: 150 points')).toBeInTheDocument();
      expect(screen.getByText('MSFT: 0 points')).toBeInTheDocument();
      expect(screen.getByText('INVALID123: 0 points')).toBeInTheDocument();
    });
  });

  test('shows error summary when errors occurred', async () => {
    render(<HistoryViewer />);
    
    await waitFor(() => {
      expect(screen.getByText('partial')).toBeInTheDocument();
    });
    
    const viewButton = screen.getByLabelText(/View scan details/);
    fireEvent.click(viewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Error Summary')).toBeInTheDocument();
      expect(screen.getByText('data fetch error: 2')).toBeInTheDocument();
      expect(screen.getByText('insufficient data: 1')).toBeInTheDocument();
    });
  });

  test('handles scans without diagnostics gracefully', async () => {
    const scanWithoutDiagnostics = {
      ...mockScanWithDiagnostics,
      diagnostics: undefined,
      scan_status: undefined,
      error_message: undefined
    };
    
    mockApiService.getScanHistory.mkResolvedValue([scanWithoutDiagnostics]);
    
    render(<HistoryViewer />);
    
    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument(); // Default status
    });
    
    // Should not crash when opening details
    const viewButton = screen.getByLabelText(/View scan details/);
    fireEvent.click(viewButton);
    
    await waitFor(() => {
      expect(screen.getByText('Scan Overview')).toBeInTheDocument();
    });
  });
});