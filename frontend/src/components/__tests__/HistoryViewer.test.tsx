import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HistoryViewer from '../HistoryViewer';
import { ApiService } from '../../services/api';
import { ScanResult, BacktestResult, AlgorithmSettings } from '../../types';

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

const mockScanResults: ScanResult[] = [
  {
    id: 'scan-1',
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
  },
];

const mockBacktestResults: BacktestResult[] = [
  {
    id: 'backtest-1',
    timestamp: '2023-12-01T11:00:00Z',
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
  },
];

describe('HistoryViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getScanHistory.mockResolvedValue(mockScanResults);
    mockApiService.getBacktestHistory.mockResolvedValue(mockBacktestResults);
  });

  it('renders history viewer with initial elements', async () => {
    render(<HistoryViewer />);

    expect(screen.getByText('History Viewer')).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
    expect(screen.getByLabelText('Symbol')).toBeInTheDocument();
    expect(screen.getByLabelText('Signal Type')).toBeInTheDocument();
    expect(screen.getByText('Apply Filters')).toBeInTheDocument();
    expect(screen.getByText('Clear')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalled();
      expect(mockApiService.getBacktestHistory).toHaveBeenCalled();
    });
  });

  it('displays scan history in the first tab', async () => {
    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Scan History (1)')).toBeInTheDocument();
      expect(screen.getByText('2 symbols')).toBeInTheDocument();
      expect(screen.getByText('1 signals')).toBeInTheDocument();
      expect(screen.getByText('2.50s')).toBeInTheDocument();
    });
  });

  it('displays backtest history in the second tab', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Backtest History (1)')).toBeInTheDocument();
    });

    const backtestTab = screen.getByText('Backtest History (1)');
    await user.click(backtestTab);

    await waitFor(() => {
      expect(screen.getByText('2023-01-01 to 2023-12-31')).toBeInTheDocument();
      expect(screen.getByText('2 symbols')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // total trades
      expect(screen.getByText('100.00%')).toBeInTheDocument(); // win rate
      expect(screen.getByText('3.33%')).toBeInTheDocument(); // total return
    });
  });

  it('allows filtering by symbol', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    const symbolInput = screen.getByLabelText('Symbol');
    await user.type(symbolInput, 'AAPL');

    const applyFiltersButton = screen.getByText('Apply Filters');
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledWith({
        symbol: 'AAPL',
      });
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledWith({
        symbol: 'AAPL',
      });
    });
  });

  it('allows filtering by signal type', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    const signalTypeSelect = screen.getByLabelText('Signal Type');
    await user.click(signalTypeSelect);
    
    const longOption = screen.getByText('Long');
    await user.click(longOption);

    const applyFiltersButton = screen.getByText('Apply Filters');
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledWith({
        signal_type: 'long',
      });
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledWith({
        signal_type: 'long',
      });
    });
  });

  it('allows filtering by date range', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    const startDateInput = screen.getByLabelText('Start Date');
    await user.type(startDateInput, '2023-01-01');

    const endDateInput = screen.getByLabelText('End Date');
    await user.type(endDateInput, '2023-12-31');

    const applyFiltersButton = screen.getByText('Apply Filters');
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledWith({
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      });
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledWith({
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      });
    });
  });

  it('clears filters when Clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    // Set some filters
    const symbolInput = screen.getByLabelText('Symbol');
    await user.type(symbolInput, 'AAPL');

    const clearButton = screen.getByText('Clear');
    await user.click(clearButton);

    expect(symbolInput).toHaveValue('');

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledWith({});
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledWith({});
    });
  });

  it('refreshes data when Refresh button is clicked', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledTimes(1);
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByText('Refresh');
    await user.click(refreshButton);

    await waitFor(() => {
      expect(mockApiService.getScanHistory).toHaveBeenCalledTimes(2);
      expect(mockApiService.getBacktestHistory).toHaveBeenCalledTimes(2);
    });
  });

  it('opens detail dialog when View button is clicked', async () => {
    const user = userEvent.setup();
    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Scan History (1)')).toBeInTheDocument();
    });

    const viewButtons = screen.getAllByText('View');
    await user.click(viewButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Scan Details')).toBeInTheDocument();
      expect(screen.getByText('ID: scan-1')).toBeInTheDocument();
      expect(screen.getByText('Symbols Scanned: AAPL, GOOGL')).toBeInTheDocument();
    });
  });

  it('displays empty state when no history exists', async () => {
    mockApiService.getScanHistory.mockResolvedValue([]);
    mockApiService.getBacktestHistory.mockResolvedValue([]);

    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Scan History (0)')).toBeInTheDocument();
      expect(screen.getByText('No scan history found.')).toBeInTheDocument();
    });
  });

  it('displays error message when loading fails', async () => {
    mockApiService.getScanHistory.mockRejectedValue(new Error('Network error'));
    mockApiService.getBacktestHistory.mockRejectedValue(new Error('Network error'));

    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows loading indicator while fetching data', async () => {
    let resolveScanPromise: (value: ScanResult[]) => void;
    let resolveBacktestPromise: (value: BacktestResult[]) => void;
    
    const scanPromise = new Promise<ScanResult[]>((resolve) => {
      resolveScanPromise = resolve;
    });
    const backtestPromise = new Promise<BacktestResult[]>((resolve) => {
      resolveBacktestPromise = resolve;
    });

    mockApiService.getScanHistory.mockReturnValue(scanPromise);
    mockApiService.getBacktestHistory.mockReturnValue(backtestPromise);

    render(<HistoryViewer />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Resolve the promises
    resolveScanPromise!(mockScanResults);
    resolveBacktestPromise!(mockBacktestResults);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  it('handles pagination correctly', async () => {
    // Create more than 10 items to test pagination
    const manyScans = Array.from({ length: 15 }, (_, i) => ({
      ...mockScanResults[0],
      id: `scan-${i + 1}`,
    }));

    mockApiService.getScanHistory.mockResolvedValue(manyScans);

    render(<HistoryViewer />);

    await waitFor(() => {
      expect(screen.getByText('Scan History (15)')).toBeInTheDocument();
    });

    // Should show pagination controls
    const pagination = screen.getByRole('navigation');
    expect(pagination).toBeInTheDocument();
  });
});