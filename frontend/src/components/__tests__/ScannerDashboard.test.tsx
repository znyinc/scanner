import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ScannerDashboard from '../ScannerDashboard';
import { ApiService } from '../../services/api';
import { AlgorithmSettings, ScanResult } from '../../types';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

const mockSettings: AlgorithmSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

const mockScanResult: ScanResult = {
  id: 'test-scan-1',
  timestamp: '2023-12-01T10:00:00Z',
  symbols_scanned: ['AAPL', 'GOOGL'],
  signals_found: [
    {
      symbol: 'AAPL',
      signal_type: 'long',
      timestamp: '2023-12-01T10:00:00Z',
      price: 150.25,
      indicators: {
        ema5: 149.50,
        ema8: 148.75,
        ema13: 147.25,
        ema21: 145.50,
        ema50: 140.25,
        atr: 2.15,
        atr_long_line: 147.35,
        atr_short_line: 151.90,
      },
      confidence: 0.85,
    },
  ],
  settings_used: mockSettings,
  execution_time: 2.5,
};

describe('ScannerDashboard', () => {
  const mockOnViewHistory = jest.fn();
  const mockOnConfigureSettings = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getSettings.mockResolvedValue(mockSettings);
  });

  it('renders scanner dashboard with initial elements', async () => {
    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    expect(screen.getByText('Stock Scanner Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Initiate Stock Scan')).toBeInTheDocument();
    expect(screen.getByLabelText('Stock Symbols (comma-separated)')).toBeInTheDocument();
    expect(screen.getByText('Start Scan')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });
  });

  it('allows user to input stock symbols', async () => {
    const user = userEvent.setup();
    
    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    const symbolInput = screen.getByLabelText('Stock Symbols (comma-separated)');
    await user.clear(symbolInput);
    await user.type(symbolInput, 'TSLA,NVDA');

    expect(symbolInput).toHaveValue('TSLA,NVDA');
  });

  it('initiates scan when Start Scan button is clicked', async () => {
    const user = userEvent.setup();
    mockApiService.initiateScan.mockResolvedValue(mockScanResult);

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const startScanButton = screen.getByText('Start Scan');
    await user.click(startScanButton);

    await waitFor(() => {
      expect(mockApiService.initiateScan).toHaveBeenCalledWith(
        ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        mockSettings
      );
    });
  });

  it('displays scan results after successful scan', async () => {
    const user = userEvent.setup();
    mockApiService.initiateScan.mockResolvedValue(mockScanResult);

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const startScanButton = screen.getByText('Start Scan');
    await user.click(startScanButton);

    await waitFor(() => {
      expect(screen.getByText('Scan Results')).toBeInTheDocument();
      expect(screen.getByText('Scanned 2 symbols in 2.50s')).toBeInTheDocument();
      expect(screen.getByText('Found 1 signals')).toBeInTheDocument();
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('LONG')).toBeInTheDocument();
      expect(screen.getByText('$150.25')).toBeInTheDocument();
    });
  });

  it('displays error message when scan fails', async () => {
    const user = userEvent.setup();
    mockApiService.initiateScan.mockRejectedValue(new Error('Network error'));

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const startScanButton = screen.getByText('Start Scan');
    await user.click(startScanButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows loading state during scan', async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: ScanResult) => void;
    const scanPromise = new Promise<ScanResult>((resolve) => {
      resolvePromise = resolve;
    });
    mockApiService.initiateScan.mockReturnValue(scanPromise);

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const startScanButton = screen.getByText('Start Scan');
    await user.click(startScanButton);

    expect(screen.getByText('Scanning...')).toBeInTheDocument();
    expect(startScanButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!(mockScanResult);

    await waitFor(() => {
      expect(screen.getByText('Start Scan')).toBeInTheDocument();
      expect(startScanButton).not.toBeDisabled();
    });
  });

  it('calls onViewHistory when History button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    const historyButton = screen.getByText('History');
    await user.click(historyButton);

    expect(mockOnViewHistory).toHaveBeenCalled();
  });

  it('calls onConfigureSettings when Settings button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    const settingsButton = screen.getByText('Settings');
    await user.click(settingsButton);

    expect(mockOnConfigureSettings).toHaveBeenCalled();
  });

  it('validates empty symbols input', async () => {
    const user = userEvent.setup();

    render(
      <ScannerDashboard 
        onViewHistory={mockOnViewHistory}
        onConfigureSettings={mockOnConfigureSettings}
      />
    );

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const symbolInput = screen.getByLabelText('Stock Symbols (comma-separated)');
    await user.clear(symbolInput);

    const startScanButton = screen.getByText('Start Scan');
    await user.click(startScanButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter at least one stock symbol')).toBeInTheDocument();
    });

    expect(mockApiService.initiateScan).not.toHaveBeenCalled();
  });
});