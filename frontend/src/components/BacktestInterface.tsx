import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Chip,
  Divider,
  useMediaQuery,
  useTheme,
  Stack,
} from '@mui/material';
import { PlayArrow, GetApp } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ApiService, handleApiError } from '../services/api';
import { BacktestResult, Trade, AlgorithmSettings } from '../types';
import ResponsiveTable from './ResponsiveTable';

const BacktestInterface: React.FC = () => {
  const [symbols, setSymbols] = useState<string>('AAPL,GOOGL,MSFT');
  const [startDate, setStartDate] = useState<string>('2023-01-01');
  const [endDate, setEndDate] = useState<string>('2023-12-31');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string>('');
  const [settings, setSettings] = useState<AlgorithmSettings | null>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  useEffect(() => {
    loadSettings();
    // Set default end date to today
    const today = new Date().toISOString().split('T')[0];
    setEndDate(today);
  }, []);

  const loadSettings = async () => {
    try {
      const currentSettings = await ApiService.getSettings();
      setSettings(currentSettings);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const runBacktest = async () => {
    if (!symbols.trim()) {
      setError('Please enter at least one stock symbol');
      return;
    }

    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) >= new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }

    if (!settings) {
      setError('Settings not loaded. Please try again.');
      return;
    }

    setIsRunning(true);
    setError('');
    setResult(null);

    try {
      const symbolList = symbols
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);

      const backtestResult = await ApiService.runBacktest(
        symbolList,
        startDate,
        endDate,
        settings
      );
      setResult(backtestResult);
    } catch (err) {
      setError(handleApiError(err).message);
    } finally {
      setIsRunning(false);
    }
  };

  const exportResults = () => {
    if (!result) return;

    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest_${result.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const formatPrice = (price: number): string => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getTradeColor = (tradeType: string) => {
    return tradeType === 'long' ? 'success' : 'error';
  };

  // Prepare chart data from trades
  const getChartData = () => {
    if (!result || result.trades.length === 0) return [];

    let cumulativePnL = 0;
    return result.trades.map((trade: Trade) => {
      cumulativePnL += trade.pnl;
      return {
        date: trade.exit_date.split('T')[0],
        cumulativePnL: cumulativePnL,
        tradePnL: trade.pnl,
      };
    });
  };

  // Define table columns for trades
  const tradeColumns = [
    { 
      id: 'symbol', 
      label: 'Symbol', 
      priority: 1,
      format: (value: string) => value
    },
    { 
      id: 'trade_type', 
      label: 'Type', 
      priority: 1,
      format: (value: string) => value.toUpperCase()
    },
    { 
      id: 'entry_date', 
      label: 'Entry Date', 
      priority: 3,
      hideOnMobile: true,
      format: (value: string) => new Date(value).toLocaleDateString()
    },
    { 
      id: 'entry_price', 
      label: 'Entry Price', 
      priority: 4,
      align: 'right' as const,
      hideOnMobile: true,
      format: formatPrice
    },
    { 
      id: 'exit_date', 
      label: 'Exit Date', 
      priority: 4,
      hideOnMobile: true,
      format: (value: string) => new Date(value).toLocaleDateString()
    },
    { 
      id: 'exit_price', 
      label: 'Exit Price', 
      priority: 4,
      align: 'right' as const,
      hideOnMobile: true,
      format: formatPrice
    },
    { 
      id: 'pnl', 
      label: 'P&L', 
      priority: 2,
      align: 'right' as const,
      format: formatPrice
    },
    { 
      id: 'pnl_percent', 
      label: 'P&L %', 
      priority: 2,
      align: 'right' as const,
      format: formatPercentage
    },
  ];

  // Transform trades for table display
  const getTradeRows = () => {
    if (!result) return [];
    
    return result.trades.map((trade: Trade) => ({
      symbol: trade.symbol,
      trade_type: trade.trade_type,
      entry_date: trade.entry_date,
      entry_price: trade.entry_price,
      exit_date: trade.exit_date,
      exit_price: trade.exit_price,
      pnl: trade.pnl,
      pnl_percent: trade.pnl_percent,
    }));
  };

  // Mobile card renderer for trades
  const renderTradeCard = (row: any, index: number) => (
    <Box key={index} role="group" aria-labelledby={`trade-${index}-symbol`}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography 
          variant="h6" 
          component="h3" 
          id={`trade-${index}-symbol`}
          sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
        >
          {row.symbol}
        </Typography>
        <Chip
          label={row.trade_type.toUpperCase()}
          color={getTradeColor(row.trade_type)}
          size="small"
          aria-label={`${row.trade_type} trade for ${row.symbol}`}
          sx={{
            fontWeight: 600,
            minHeight: 32,
            '& .MuiChip-label': {
              px: 1.5
            }
          }}
        />
      </Box>
      <Grid container spacing={1} component="dl" sx={{ margin: 0 }}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            P&L
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold"
            component="dd"
            sx={{ 
              margin: 0,
              fontSize: { xs: '1rem', sm: '1.125rem' }
            }}
            color={row.pnl >= 0 ? 'success.main' : 'error.main'}
            aria-label={`Profit and loss: ${row.pnl >= 0 ? 'profit' : 'loss'} of ${formatPrice(row.pnl)}`}
          >
            {formatPrice(row.pnl)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            P&L %
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold"
            component="dd"
            sx={{ 
              margin: 0,
              fontSize: { xs: '1rem', sm: '1.125rem' }
            }}
            color={row.pnl_percent >= 0 ? 'success.main' : 'error.main'}
            aria-label={`Percentage return: ${formatPercentage(row.pnl_percent)}`}
          >
            {formatPercentage(row.pnl_percent)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            Entry Date
          </Typography>
          <Typography 
            variant="body2" 
            component="dd" 
            sx={{ margin: 0 }}
            aria-label={`Entry date: ${new Date(row.entry_date).toLocaleDateString()}`}
          >
            {new Date(row.entry_date).toLocaleDateString()}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            Exit Date
          </Typography>
          <Typography 
            variant="body2" 
            component="dd" 
            sx={{ margin: 0 }}
            aria-label={`Exit date: ${new Date(row.exit_date).toLocaleDateString()}`}
          >
            {new Date(row.exit_date).toLocaleDateString()}
          </Typography>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }}>
      <Typography 
        variant="h4" 
        component="h1"
        gutterBottom
        sx={{ 
          fontSize: { xs: '1.5rem', sm: '2.125rem' },
          textAlign: { xs: 'center', sm: 'left' }
        }}
        id="backtest-title"
      >
        Backtest Interface
      </Typography>
      
      {/* Screen reader announcement */}
      <div className="sr-only" aria-live="polite">
        Backtest interface loaded. Configure your backtest parameters and run historical analysis.
      </div>

      {/* Backtest Configuration */}
      <Card sx={{ mb: 3 }} role="region" aria-labelledby="backtest-config-title">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom id="backtest-config-title">
            Backtest Configuration
          </Typography>
          
          <Box component="form" role="form" aria-labelledby="backtest-config-title">
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Stock Symbols"
                  value={symbols}
                  onChange={(e) => setSymbols(e.target.value)}
                  placeholder="AAPL,GOOGL,MSFT"
                  disabled={isRunning}
                  helperText="Enter stock symbols separated by commas for historical analysis"
                  inputProps={{
                    'aria-describedby': 'backtest-symbols-helper-text',
                    'aria-required': 'true',
                  }}
                  id="backtest-symbols-input"
                  FormHelperTextProps={{
                    id: 'backtest-symbols-helper-text'
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  disabled={isRunning}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{
                    'aria-label': 'Backtest start date',
                    'aria-required': 'true',
                    max: endDate || undefined,
                  }}
                  helperText="Select the beginning date for historical analysis"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="End Date"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  disabled={isRunning}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{
                    'aria-label': 'Backtest end date',
                    'aria-required': 'true',
                    min: startDate || undefined,
                  }}
                  helperText="Select the ending date for historical analysis"
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  fullWidth={isMobile}
                  variant="contained"
                  startIcon={isRunning ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={runBacktest}
                  disabled={isRunning}
                  sx={{ 
                    height: { xs: 48, sm: 56 },
                    maxWidth: isMobile ? 'none' : '200px',
                    fontSize: { xs: '1rem', sm: '0.875rem' },
                    fontWeight: 600
                  }}
                  aria-describedby={isRunning ? 'backtest-loading-status' : undefined}
                  type="submit"
                >
                  {isRunning ? 'Running Backtest...' : 'Run Backtest'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError('')}
          role="alert"
          aria-live="polite"
        >
          {error}
        </Alert>
      )}

      {/* Loading Status for Screen Readers */}
      {isRunning && (
        <div id="backtest-loading-status" className="sr-only" aria-live="polite">
          Backtest is running, please wait...
        </div>
      )}

      {/* Backtest Results */}
      {result && (
        <>
          {/* Performance Metrics */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                mb: 2,
                flexDirection: { xs: 'column', sm: 'row' },
                gap: { xs: 2, sm: 0 }
              }}>
                <Typography variant="h6" component="h2">
                  Performance Metrics
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<GetApp />}
                  onClick={exportResults}
                  size="small"
                  aria-label="Export backtest results"
                >
                  Export Results
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Total Trades
                  </Typography>
                  <Typography variant="h6">
                    {result.performance.total_trades}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Win Rate
                  </Typography>
                  <Typography variant="h6" color={result.performance.win_rate >= 0.5 ? 'success.main' : 'error.main'}>
                    {formatPercentage(result.performance.win_rate)}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Total Return
                  </Typography>
                  <Typography variant="h6" color={result.performance.total_return >= 0 ? 'success.main' : 'error.main'}>
                    {formatPercentage(result.performance.total_return)}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Sharpe Ratio
                  </Typography>
                  <Typography variant="h6">
                    {result.performance.sharpe_ratio.toFixed(2)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Performance Chart */}
          {result.trades.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" component="h2" gutterBottom>
                  Cumulative P&L Chart
                </Typography>
                <Box sx={{ width: '100%', height: { xs: 250, sm: 300 } }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart 
                      data={getChartData()}
                      aria-label="Cumulative profit and loss over time"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: isMobile ? 10 : 12 }}
                      />
                      <YAxis 
                        tick={{ fontSize: isMobile ? 10 : 12 }}
                      />
                      <Tooltip 
                        formatter={(value: number) => [formatPrice(value), 'Cumulative P&L']}
                        labelFormatter={(label) => `Date: ${label}`}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="cumulativePnL" 
                        stroke="#2196f3" 
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Individual Trades */}
          <Card>
            <CardContent>
              <Typography variant="h6" component="h2" gutterBottom>
                Individual Trades ({result.trades.length})
              </Typography>
              
              {result.trades.length === 0 ? (
                <Alert severity="info" role="status">
                  No trades were generated during the backtest period.
                </Alert>
              ) : (
                <ResponsiveTable
                  columns={tradeColumns}
                  rows={getTradeRows()}
                  ariaLabel="Individual trades table"
                  mobileCardView={true}
                  renderMobileCard={renderTradeCard}
                  stickyHeader={true}
                  maxHeight={400}
                />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default BacktestInterface;