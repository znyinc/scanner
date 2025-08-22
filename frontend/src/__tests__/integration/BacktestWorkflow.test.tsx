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

const mockBacktestResult = {
  id: 'backtest-123',
  timestamp: '2023-12-01T10:00:00Z',
  start_date: '2023-01-01',
  end_date: '2023-12-01',
  symbols: ['AAPL', 'GOOGL'],
  trades: [
    {
      symbol: 'AAPL',
      entry_date: '2023-06-01T09:30:00Z',
      entry_price: 145.50,
      exit_date: '2023-06-02T16:00:00Z',
      exit_price: 148.75,
      trade_type: 'long' as const,
      pnl: 3.25,
      pnl_percent: 0.0223,
    },
    {
      symbol: 'GOOGL',
      entry_date: '2023-07-15T09:30:00Z',
      entry_price: 120.00,
      exit_date: '2023-07-16T16:00:00Z',
      exit_price: 118.50,
      trade_type: 'short' as const,
      pnl: 1.50,
      pnl_percent: 0.0125,
    },
  ],
  performance: {
    total_trades: 2,
    winning_trades: 2,
    losing_trades: 0,
    win_rate: 1.0,
    total_return: 0.0348,
    average_return: 0.0174,
    max_drawdown: 0.0,
    sharpe_ratio: 2.5,
  },
  settings_used: mockSettings,
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

describe('Backtest Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    mockApiService.getSettings.mockResolvedValue(mockSettings);
    mockApiService.healthCheck.mockResolvedValue(true);
    mockApiService.runBacktest.mockResolvedValue(mockBacktestResult);
  });

  test('complete backtest workflow - successful backtest with results', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for initial settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    // Verify we're on the backtest interface
    expect(screen.getByText('Backtest Interface')).toBeInTheDocument();

    // Fill in backtest parameters
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.clear(symbolsInput);
    await user.type(symbolsInput, 'AAPL,GOOGL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');

    // Click the run backtest button
    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    expect(backtestButton).not.toBeDisabled();
    
    await user.click(backtestButton);

    // Verify API call was made with correct parameters
    await waitFor(() => {
      expect(mockApiService.runBacktest).toHaveBeenCalledWith(
        ['AAPL', 'GOOGL'],
        '2023-01-01',
        '2023-12-01',
        mockSettings,
        expect.any(Function)
      );
    });

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });

    // Verify performance metrics are displayed
    expect(screen.getByText('2')).toBeInTheDocument(); // total trades
    expect(screen.getByText('100.00%')).toBeInTheDocument(); // win rate
    expect(screen.getByText('3.48%')).toBeInTheDocument(); // total return
    expect(screen.getByText('2.50')).toBeInTheDocument(); // sharpe ratio

    // Verify individual trades table
    expect(screen.getByText('Individual Trades (2)')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('LONG')).toBeInTheDocument();
    expect(screen.getByText('SHORT')).toBeInTheDocument();
  });

  test('backtest workflow - validation errors', async () => {
    const user = userEvent.setup();
    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    // Try to run backtest without symbols
    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    await user.click(backtestButton);

    // Should not call API
    expect(mockApiService.runBacktest).not.toHaveBeenCalled();

    // Fill symbols but set invalid date range (start after end)
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.type(symbolsInput, 'AAPL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-12-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-01-01');

    await user.click(backtestButton);

    // Should not call API with invalid date range
    expect(mockApiService.runBacktest).not.toHaveBeenCalled();
  });

  test('backtest workflow - API error handling', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    mockApiService.runBacktest.mockRejectedValue(new Error('Insufficient data'));

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    // Fill valid parameters
    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.type(symbolsInput, 'AAPL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');

    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    await user.click(backtestButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
    });

    // Verify error alert is displayed
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  test('backtest workflow - export results functionality', async () => {
    const user = userEvent.setup();
    
    // Mock successful backtest
    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab and run backtest
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.type(symbolsInput, 'AAPL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');

    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    await user.click(backtestButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });

    // Mock URL.createObjectURL and click export
    const mockCreateObjectURL = jest.fn(() => 'mock-url');
    const mockRevokeObjectURL = jest.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock document.createElement and click
    const mockLink = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);

    const exportButton = screen.getByRole('button', { name: /export results/i });
    await user.click(exportButton);

    // Verify export functionality was called
    expect(mockCreateObjectURL).toHaveBeenCalled();
    expect(mockLink.click).toHaveBeenCalled();
    expect(mockRevokeObjectURL).toHaveBeenCalled();
  });

  test('backtest workflow - no trades scenario', async () => {
    const user = userEvent.setup();
    
    // Mock backtest with no trades
    const emptyResult = {
      ...mockBacktestResult,
      trades: [],
      performance: {
        ...mockBacktestResult.performance,
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: 0,
        total_return: 0,
        average_return: 0,
      },
    };
    mockApiService.runBacktest.mockResolvedValue(emptyResult);

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab and run backtest
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.type(symbolsInput, 'AAPL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');

    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    await user.click(backtestButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });

    // Verify no trades message
    expect(screen.getByText(/no trades were generated/i)).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument(); // total trades
  });

  test('progress indicator during backtest', async () => {
    const user = userEvent.setup();
    
    // Mock backtest with progress callback
    mockApiService.runBacktest.mockImplementation(async (symbols, startDate, endDate, settings, onProgress) => {
      if (onProgress) {
        onProgress(10, 'Fetching historical data...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onProgress(50, 'Running algorithm...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onProgress(90, 'Calculating metrics...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onProgress(100, 'Complete');
      }
      return mockBacktestResult;
    });

    renderApp();

    // Wait for settings to load
    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Navigate to backtest tab and start backtest
    const backtestTab = screen.getByRole('tab', { name: /backtest/i });
    await user.click(backtestTab);

    const symbolsInput = screen.getByLabelText(/stock symbols/i);
    await user.type(symbolsInput, 'AAPL');

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');

    const backtestButton = screen.getByRole('button', { name: /run backtest/i });
    await user.click(backtestButton);

    // Verify progress indicator appears
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });
  });
});