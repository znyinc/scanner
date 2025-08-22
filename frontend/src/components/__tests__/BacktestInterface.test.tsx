import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BacktestInterface from '../BacktestInterface';
import { ApiService } from '../../services/api';
import { AlgorithmSettings, BacktestResult } from '../../types';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Mock recharts
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
}));

const mockSettings: AlgorithmSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

const mockBacktestResult: BacktestResult = {
  id: 'test-backtest-1',
  timestamp: '2023-12-01T10:00:00Z',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  symbols: ['AAPL', 'GOOGL'],
  trades: [
    {
      symbol: 'AAPL',
      entry_date: '2023-06-01T09:30:00Z',
      entry_price: 150.00,
      exit_date: '2023-06-02T16:00:00Z',
      exit_price: 155.00,
      trade_type: 'long',
      pnl: 5.00,
      pnl_percent: 0.0333,
    },
  ],
  performance: {
    total_trades: 1,
    winning_trades: 1,
    losing_trades: 0,
    win_rate: 1.0,
    total_return: 0.0333,
    average_return: 0.0333,
    max_drawdown: 0.0,
    sharpe_ratio: 1.5,
  },
  settings_used: mockSettings,
};

describe('BacktestInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getSettings.mockResolvedValue(mockSettings);
  });

  it('renders backtest interface with initial elements', async () => {
    render(<BacktestInterface />);

    expect(screen.getByText('Backtest Interface')).toBeInTheDocument();
    expect(screen.getByText('Backtest Configuration')).toBeInTheDocument();
    expect(screen.getByLabelText('Stock Symbols')).toBeInTheDocument();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    expect(screen.getByText('Run Backtest')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });
  });

  it('allows user to configure backtest parameters', async () => {
    const user = userEvent.setup();
    
    render(<BacktestInterface />);

    const symbolInput = screen.getByLabelText('Stock Symbols');
    await user.clear(symbolInput);
    await user.type(symbolInput, 'TSLA,NVDA');

    const startDateInput = screen.getByLabelText('Start Date');
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-06-01');

    const endDateInput = screen.getByLabelText('End Date');
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-06-30');

    expect(symbolInput).toHaveValue('TSLA,NVDA');
    expect(startDateInput).toHaveValue('2023-06-01');
    expect(endDateInput).toHaveValue('2023-06-30');
  });

  it('runs backtest when Run Backtest button is clicked', async () => {
    const user = userEvent.setup();
    mockApiService.runBacktest.mockResolvedValue(mockBacktestResult);

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(mockApiService.runBacktest).toHaveBeenCalledWith(
        ['AAPL', 'GOOGL', 'MSFT'],
        '2023-01-01',
        expect.any(String), // end date is set to today
        mockSettings
      );
    });
  });

  it('displays backtest results after successful run', async () => {
    const user = userEvent.setup();
    mockApiService.runBacktest.mockResolvedValue(mockBacktestResult);

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
      expect(screen.getByText('Total Trades')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // total trades
      expect(screen.getByText('Win Rate')).toBeInTheDocument();
      expect(screen.getByText('100.00%')).toBeInTheDocument(); // win rate
      expect(screen.getByText('Individual Trades (1)')).toBeInTheDocument();
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('LONG')).toBeInTheDocument();
    });
  });

  it('displays performance chart when trades exist', async () => {
    const user = userEvent.setup();
    mockApiService.runBacktest.mockResolvedValue(mockBacktestResult);

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Cumulative P&L')).toBeInTheDocument();
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('displays error message when backtest fails', async () => {
    const user = userEvent.setup();
    mockApiService.runBacktest.mockRejectedValue(new Error('Server error'));

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });

  it('validates date range', async () => {
    const user = userEvent.setup();

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const startDateInput = screen.getByLabelText('Start Date');
    const endDateInput = screen.getByLabelText('End Date');

    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-12-31');
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-01-01');

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Start date must be before end date')).toBeInTheDocument();
    });

    expect(mockApiService.runBacktest).not.toHaveBeenCalled();
  });

  it('validates empty symbols input', async () => {
    const user = userEvent.setup();

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const symbolInput = screen.getByLabelText('Stock Symbols');
    await user.clear(symbolInput);

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter at least one stock symbol')).toBeInTheDocument();
    });

    expect(mockApiService.runBacktest).not.toHaveBeenCalled();
  });

  it('shows loading state during backtest', async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: BacktestResult) => void;
    const backtestPromise = new Promise<BacktestResult>((resolve) => {
      resolvePromise = resolve;
    });
    mockApiService.runBacktest.mockReturnValue(backtestPromise);

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    expect(screen.getByText('Running...')).toBeInTheDocument();
    expect(runBacktestButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!(mockBacktestResult);

    await waitFor(() => {
      expect(screen.getByText('Run Backtest')).toBeInTheDocument();
      expect(runBacktestButton).not.toBeDisabled();
    });
  });

  it('allows exporting results', async () => {
    const user = userEvent.setup();
    mockApiService.runBacktest.mockResolvedValue(mockBacktestResult);

    // Mock URL.createObjectURL and related functions
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();
    
    const mockClick = jest.fn();
    const mockLink = {
      href: '',
      download: '',
      click: mockClick,
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);

    render(<BacktestInterface />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const runBacktestButton = screen.getByText('Run Backtest');
    await user.click(runBacktestButton);

    await waitFor(() => {
      expect(screen.getByText('Export Results')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export Results');
    await user.click(exportButton);

    expect(mockClick).toHaveBeenCalled();
    expect(mockLink.download).toBe('backtest_test-backtest-1.json');
  });
});