import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { ApiService } from './services/api';

// Mock the API service
jest.mock('./services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Mock recharts to avoid issues in tests
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
}));

const mockSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getSettings.mockResolvedValue(mockSettings);
    mockApiService.getScanHistory.mockResolvedValue([]);
    mockApiService.getBacktestHistory.mockResolvedValue([]);
  });

  it('renders app with navigation and initial scanner tab', () => {
    render(<App />);

    expect(screen.getByText('Stock Scanner - EMA-ATR Algorithm')).toBeInTheDocument();
    expect(screen.getByText('Scanner')).toBeInTheDocument();
    expect(screen.getByText('Backtest')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    
    // Should show scanner dashboard by default
    expect(screen.getByText('Stock Scanner Dashboard')).toBeInTheDocument();
  });

  it('navigates to backtest tab when clicked', async () => {
    const user = userEvent.setup();
    render(<App />);

    const backtestTab = screen.getByText('Backtest');
    await user.click(backtestTab);

    expect(screen.getByText('Backtest Interface')).toBeInTheDocument();
  });

  it('navigates to history tab when clicked', async () => {
    const user = userEvent.setup();
    render(<App />);

    const historyTab = screen.getByText('History');
    await user.click(historyTab);

    expect(screen.getByText('History Viewer')).toBeInTheDocument();
  });

  it('navigates to settings tab when clicked', async () => {
    const user = userEvent.setup();
    render(<App />);

    const settingsTab = screen.getByText('Settings');
    await user.click(settingsTab);

    expect(screen.getByText('Algorithm Settings')).toBeInTheDocument();
  });

  it('navigates to history tab when History button is clicked from scanner', async () => {
    const user = userEvent.setup();
    render(<App />);

    // Should start on scanner tab
    expect(screen.getByText('Stock Scanner Dashboard')).toBeInTheDocument();

    const historyButton = screen.getByText('History');
    await user.click(historyButton);

    expect(screen.getByText('History Viewer')).toBeInTheDocument();
  });

  it('navigates to settings tab when Settings button is clicked from scanner', async () => {
    const user = userEvent.setup();
    render(<App />);

    // Should start on scanner tab
    expect(screen.getByText('Stock Scanner Dashboard')).toBeInTheDocument();

    const settingsButton = screen.getByText('Settings');
    await user.click(settingsButton);

    expect(screen.getByText('Algorithm Settings')).toBeInTheDocument();
  });

  it('displays app bar with correct title and icon', () => {
    render(<App />);

    expect(screen.getByText('Stock Scanner - EMA-ATR Algorithm')).toBeInTheDocument();
    expect(screen.getByTestId('TrendingUpIcon')).toBeInTheDocument();
  });

  it('applies Material-UI theme correctly', () => {
    render(<App />);

    // Check that Material-UI components are rendered
    const appBar = screen.getByRole('banner');
    expect(appBar).toBeInTheDocument();

    const tabs = screen.getByRole('tablist');
    expect(tabs).toBeInTheDocument();
  });
});