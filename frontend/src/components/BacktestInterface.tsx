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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Divider,
} from '@mui/material';
import { PlayArrow, GetApp } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ApiService, handleApiError } from '../services/api';
import { BacktestResult, Trade, AlgorithmSettings } from '../types';

const BacktestInterface: React.FC = () => {
  const [symbols, setSymbols] = useState<string>('AAPL,GOOGL,MSFT');
  const [startDate, setStartDate] = useState<string>('2023-01-01');
  const [endDate, setEndDate] = useState<string>('2023-12-31');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string>('');
  const [settings, setSettings] = useState<AlgorithmSettings | null>(null);

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
      setError(handleApiError(err));
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

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Backtest Interface
      </Typography>

      {/* Backtest Configuration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Backtest Configuration
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Stock Symbols"
                value={symbols}
                onChange={(e) => setSymbols(e.target.value)}
                placeholder="AAPL,GOOGL,MSFT"
                disabled={isRunning}
                helperText="Comma-separated symbols"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isRunning}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isRunning}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                startIcon={isRunning ? <CircularProgress size={20} /> : <PlayArrow />}
                onClick={runBacktest}
                disabled={isRunning}
                sx={{ height: '56px' }}
              >
                {isRunning ? 'Running...' : 'Run Backtest'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Backtest Results */}
      {result && (
        <>
          {/* Performance Metrics */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Performance Metrics
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<GetApp />}
                  onClick={exportResults}
                  size="small"
                >
                  Export Results
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Total Trades
                  </Typography>
                  <Typography variant="h6">
                    {result.performance.total_trades}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Win Rate
                  </Typography>
                  <Typography variant="h6" color={result.performance.win_rate >= 0.5 ? 'success.main' : 'error.main'}>
                    {formatPercentage(result.performance.win_rate)}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Total Return
                  </Typography>
                  <Typography variant="h6" color={result.performance.total_return >= 0 ? 'success.main' : 'error.main'}>
                    {formatPercentage(result.performance.total_return)}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
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
                <Typography variant="h6" gutterBottom>
                  Cumulative P&L
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
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
              </CardContent>
            </Card>
          )}

          {/* Individual Trades */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Individual Trades ({result.trades.length})
              </Typography>
              
              {result.trades.length === 0 ? (
                <Alert severity="info">
                  No trades were generated during the backtest period.
                </Alert>
              ) : (
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Entry Date</TableCell>
                        <TableCell>Entry Price</TableCell>
                        <TableCell>Exit Date</TableCell>
                        <TableCell>Exit Price</TableCell>
                        <TableCell>P&L</TableCell>
                        <TableCell>P&L %</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.trades.map((trade: Trade, index: number) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {trade.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={trade.trade_type.toUpperCase()}
                              color={getTradeColor(trade.trade_type)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {new Date(trade.entry_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell>{formatPrice(trade.entry_price)}</TableCell>
                          <TableCell>
                            {new Date(trade.exit_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell>{formatPrice(trade.exit_price)}</TableCell>
                          <TableCell>
                            <Typography 
                              color={trade.pnl >= 0 ? 'success.main' : 'error.main'}
                              fontWeight="bold"
                            >
                              {formatPrice(trade.pnl)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              color={trade.pnl_percent >= 0 ? 'success.main' : 'error.main'}
                              fontWeight="bold"
                            >
                              {formatPercentage(trade.pnl_percent)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default BacktestInterface;