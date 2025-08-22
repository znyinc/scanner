import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material';
import { AppProvider } from '../../contexts/AppContext';
import App from '../../App';
import { ApiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Mock data
const mockSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

const mockScanResult = {
  id: 'scan-123',
  timestamp: '2023-12-01T10:00:00Z',
  symbols_scanned: ['AAPL', 'GOOGL'],
  signals_found: [
    {
      symbol: 'AAPL',
      signal_type: 'long' as const,
      timestamp: '2023-12-01T10:00:00Z',
      price: 150.25,
      indicators: {
        ema5: 149.50,
        ema8: 148.75,
        ema13: 148.00,
        ema21: 147.25,
        ema50: 145.00,
        atr: 2.50,
        atr_long_line: 147.00,
        atr_short_line: 152.00,
      },
      confidence: 0.85,
    },
  ],
  settings_used: mockSettings,
  execution_time: 2.5,
};

const theme = createTheme();

const renderApp = () => {
  return render(
    <ThemeProvider theme={theme}>
      <AppProvider>
        <App />
      </AppProvider>
    </ThemeProvider>
  );
};

describe('Scan Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    mockApiService.getSettings.mockResolvedValue(mockSettings);
    mockApiService.healthCheck.mockResolvedValue(true);
    mockApiService.initiateScan.mockResolvedValue(mockScanResult);
  });

  test('complete scan workflow - successful scan with results', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for initial settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Verify we're on the scanner tab
    expect(screen.getByText('Stock Scanner Dashboard')).toBeInTheDocument();

    // Find and fill the symbols input
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'AAPL,GOOGL');

    // Click the scan button
    const scanButton = screen.getByRole('button', { name: /start scan/i });
    expect(scanButton).not.toBeDisabled();
    
    await user.click(scanButton);

    // Verify API call was made with correct parameters
    await waitFor(() => {
      expect(mockApiService.initiateScan).toHaveBeenCalledWith(
        ['AAPL', 'GOOGL'],
        mockSettings,
        expect.any(Function)
      );
    });

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Scan Results')).toBeInTheDocument();
    });

    // Verify scan results are displayed
    expect(screen.getByText('Found 1 signals')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('LONG')).toBeInTheDocument();
    expect(screen.getByText('150.25')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // confidence
  });

  test('scan workflow - no results found', async () => {
    const user = userEvent.setup();
    
    // Mock scan with no results
    const emptyResult = {
      ...mockScanResult,
      signals_found: [],
    };
    mockApiService.initiateScan.mockResolvedValue(emptyResult);

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Fill symbols and scan
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'AAPL');

    const scanButton = screen.getByRole('button', { name: /start scan/i });
    await user.click(scanButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Scan Results')).toBeInTheDocument();
    });

    // Verify no signals message
    expect(screen.getByText(/no trading signals found/i)).toBeInTheDocument();
  });

  test('scan workflow - API error handling', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    mockApiService.initiateScan.mockRejectedValue(new Error('Network error'));

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Fill symbols and scan
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'AAPL');

    const scanButton = screen.getByRole('button', { name: /start scan/i });
    await user.click(scanButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });

    // Verify error alert is displayed
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  test('scan workflow - disabled when API offline', async () => {
    // Mock API as offline
    mockApiService.healthCheck.mockResolvedValue(false);

    renderApp();

    // Wait for settings and health check
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
      expect(mockApiService.healthCheck).toHaveBeenCalled();
    });

    // Verify scan button is disabled
    const scanButton = screen.getByRole('button', { name: /start scan/i });
    expect(scanButton).toBeDisabled();

    // Verify warning message
    expect(screen.getByText(/api server is error/i)).toBeInTheDocument();
  });

  test('scan workflow - invalid symbols validation', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Fill with invalid symbols
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'INVALID123,TOOLONG');

    const scanButton = screen.getByRole('button', { name: /start scan/i });
    await user.click(scanButton);

    // Should not call API with invalid symbols
    expect(mockApiService.initiateScan).not.toHaveBeenCalled();
  });

  test('navigation to history from scan results', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Click history button
    const historyButton = screen.getByRole('button', { name: /history/i });
    await user.click(historyButton);

    // Verify we navigated to history tab
    expect(screen.getByText('History Viewer')).toBeInTheDocument();
  });

  test('navigation to settings from scanner', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Click settings button
    const settingsButton = screen.getByRole('button', { name: /settings/i });
    await user.click(settingsButton);

    // Verify we navigated to settings tab
    expect(screen.getByText('Algorithm Settings')).toBeInTheDocument();
  });

  test('progress indicator during scan', async () => {
    const user = userEvent.setup();
    
    // Mock scan with progress callback
    mockApiService.initiateScan.mockImplementation(async (symbols, settings, onProgress) => {
      if (onProgress) {
        onProgress(25, 'Fetching data...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onProgress(75, 'Analyzing signals...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onProgress(100, 'Complete');
      }
      return mockScanResult;
    });

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Start scan
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'AAPL');

    const scanButton = screen.getByRole('button', { name: /start scan/i });
    await user.click(scanButton);

    // Verify progress indicator appears
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Scan Results')).toBeInTheDocument();
    });
  });
});