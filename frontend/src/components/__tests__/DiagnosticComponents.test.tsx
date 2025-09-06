import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ExpandableCard from '../ExpandableCard';
import SymbolBadge from '../SymbolBadge';
import DiagnosticDetails from '../DiagnosticDetails';
import { EnhancedScanResult, SymbolDiagnostic } from '../../types';

// Mock useMediaQuery to avoid JSDOM issues
jest.mock('@mui/material/useMediaQuery', () => ({
  __esModule: true,
  default: jest.fn(() => false), // Always return false (desktop view)
}));

const theme = createTheme();

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe('ExpandableCard', () => {
  it('renders with title and can be toggled', () => {
    const mockToggle = jest.fn();
    
    render(
      <TestWrapper>
        <ExpandableCard
          title="Test Card"
          expanded={false}
          onToggle={mockToggle}
        >
          <div>Test content</div>
        </ExpandableCard>
      </TestWrapper>
    );

    expect(screen.getByText('Test Card')).toBeInTheDocument();
    
    const expandButton = screen.getByLabelText(/expand test card section/i);
    fireEvent.click(expandButton);
    
    expect(mockToggle).toHaveBeenCalled();
  });

  it('shows content when expanded', () => {
    render(
      <TestWrapper>
        <ExpandableCard
          title="Test Card"
          expanded={true}
          onToggle={() => {}}
        >
          <div>Test content</div>
        </ExpandableCard>
      </TestWrapper>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('applies severity styling', () => {
    render(
      <TestWrapper>
        <ExpandableCard
          title="Error Card"
          expanded={false}
          onToggle={() => {}}
          severity="error"
        >
          <div>Content</div>
        </ExpandableCard>
      </TestWrapper>
    );

    expect(screen.getByText('Error Card')).toBeInTheDocument();
  });
});

describe('SymbolBadge', () => {
  const mockDiagnostic: SymbolDiagnostic = {
    symbol: 'AAPL',
    status: 'success',
    data_points_1m: 100,
    data_points_15m: 50,
    timeframe_coverage: { '1m': true, '15m': true },
    fetch_time: 0.5,
    processing_time: 0.1,
  };

  it('renders symbol badge with correct status', () => {
    render(
      <TestWrapper>
        <SymbolBadge
          symbol="AAPL"
          status="success"
          diagnostic={mockDiagnostic}
        />
      </TestWrapper>
    );

    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const mockClick = jest.fn();
    
    render(
      <TestWrapper>
        <SymbolBadge
          symbol="AAPL"
          status="success"
          onClick={mockClick}
        />
      </TestWrapper>
    );

    const badge = screen.getByText('AAPL');
    fireEvent.click(badge);
    
    expect(mockClick).toHaveBeenCalledTimes(1);
  });

  it('shows error status correctly', () => {
    const errorDiagnostic: SymbolDiagnostic = {
      ...mockDiagnostic,
      status: 'error',
      error_message: 'API timeout',
    };

    render(
      <TestWrapper>
        <SymbolBadge
          symbol="AAPL"
          status="error"
          diagnostic={errorDiagnostic}
        />
      </TestWrapper>
    );

    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });
});

describe('DiagnosticDetails', () => {
  const mockScanResult: EnhancedScanResult = {
    id: 'test-scan-1',
    timestamp: '2024-01-01T10:00:00Z',
    symbols_scanned: ['AAPL', 'GOOGL', 'MSFT'],
    signals_found: [],
    settings_used: {
      atr_multiplier: 2.0,
      ema5_rising_threshold: 0.1,
      ema8_rising_threshold: 0.1,
      ema21_rising_threshold: 0.1,
      volatility_filter: 0.5,
      fomo_filter: 0.3,
      higher_timeframe: '15m',
    },
    execution_time: 2.5,
    diagnostics: {
      symbols_with_data: ['AAPL', 'GOOGL'],
      symbols_without_data: ['MSFT'],
      symbols_with_errors: {},
      data_fetch_time: 2.0,
      algorithm_time: 0.5,
      total_data_points: { 'AAPL': 100, 'GOOGL': 95 },
      error_summary: {},
      symbol_details: {},
      performance_metrics: {
        memory_usage_mb: 150,
        api_requests_made: 10,
        api_rate_limit_remaining: 990,
        cache_hit_rate: 0.8,
        concurrent_requests: 3,
      },
      signal_analysis: {
        signals_found: 0,
        symbols_meeting_partial_criteria: {},
        rejection_reasons: {},
        confidence_distribution: {},
      },
      data_quality_metrics: {
        total_data_points: 195,
        success_rate: 0.67,
        average_fetch_time: 1.0,
        data_completeness: 0.85,
        quality_score: 0.75,
      },
      settings_snapshot: {
        atr_multiplier: 2.0,
        ema5_rising_threshold: 0.1,
        ema8_rising_threshold: 0.1,
        ema21_rising_threshold: 0.1,
        volatility_filter: 0.5,
        fomo_filter: 0.3,
        higher_timeframe: '15m',
      },
    },
  };

  it('renders diagnostic details with scan result', () => {
    const mockToggle = jest.fn();
    
    render(
      <TestWrapper>
        <DiagnosticDetails
          scanResult={mockScanResult}
          expanded={true}
          onToggle={mockToggle}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Diagnostic Details')).toBeInTheDocument();
    expect(screen.getByText('Scan Settings')).toBeInTheDocument();
    expect(screen.getByText('Symbols Scanned')).toBeInTheDocument();
  });

  it('handles export action', () => {
    const mockExport = jest.fn();
    const mockToggle = jest.fn();
    
    render(
      <TestWrapper>
        <DiagnosticDetails
          scanResult={mockScanResult}
          expanded={true}
          onToggle={mockToggle}
          onExport={mockExport}
        />
      </TestWrapper>
    );

    const exportButton = screen.getByLabelText(/export diagnostic data/i);
    fireEvent.click(exportButton);
    
    expect(mockExport).toHaveBeenCalledWith('test-scan-1');
  });

  it('shows loading state', () => {
    const mockToggle = jest.fn();
    
    render(
      <TestWrapper>
        <DiagnosticDetails
          scanResult={mockScanResult}
          expanded={true}
          onToggle={mockToggle}
          isLoading={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Loading diagnostic information...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const mockToggle = jest.fn();
    
    render(
      <TestWrapper>
        <DiagnosticDetails
          scanResult={mockScanResult}
          expanded={true}
          onToggle={mockToggle}
          error="Failed to load diagnostics"
        />
      </TestWrapper>
    );

    expect(screen.getByText('Failed to load diagnostics')).toBeInTheDocument();
  });

  it('handles scan result without diagnostics', () => {
    const mockToggle = jest.fn();
    const scanResultWithoutDiagnostics = {
      ...mockScanResult,
      diagnostics: undefined,
    };
    
    render(
      <TestWrapper>
        <DiagnosticDetails
          scanResult={scanResultWithoutDiagnostics}
          expanded={true}
          onToggle={mockToggle}
        />
      </TestWrapper>
    );

    expect(screen.getByText('No diagnostic information available')).toBeInTheDocument();
  });
});