import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Grid,
} from '@mui/material';
import { PlayArrow, History, Settings } from '@mui/icons-material';
import { useAppContext, useAppActions } from '../contexts/AppContext';
import { Signal } from '../types';
import { 
  formatPrice, 
  formatPercentage, 
  getSignalColor, 
  validateAndFormatSymbols,
  formatExecutionTime 
} from '../utils/formatters';
import ProgressIndicator from './ProgressIndicator';

interface ScannerDashboardProps {
  onViewHistory: () => void;
  onConfigureSettings: () => void;
}

const ScannerDashboard: React.FC<ScannerDashboardProps> = ({
  onViewHistory,
  onConfigureSettings,
}) => {
  const { state } = useAppContext();
  const { initiateScan, clearScanError } = useAppActions();
  const [symbols, setSymbols] = useState<string>('AAPL,GOOGL,MSFT,TSLA,AMZN');
  const [progress, setProgress] = useState<number>(0);
  const [progressMessage, setProgressMessage] = useState<string>('');

  const handleScan = async () => {
    if (!symbols.trim()) {
      return;
    }

    if (!state.settings) {
      return;
    }

    // Validate symbols
    const { valid, invalid } = validateAndFormatSymbols(symbols);
    
    if (invalid.length > 0) {
      // Show warning about invalid symbols but continue with valid ones
      console.warn('Invalid symbols detected:', invalid);
    }

    if (valid.length === 0) {
      return;
    }

    try {
      await initiateScan(valid, state.settings, (prog, msg) => {
        setProgress(prog);
        setProgressMessage(msg || '');
      });
    } catch (error) {
      // Error is handled by the context
      console.error('Scan failed:', error);
    } finally {
      setProgress(0);
      setProgressMessage('');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Stock Scanner Dashboard
      </Typography>

      {/* Progress Indicator */}
      <ProgressIndicator
        isVisible={state.scanLoading}
        progress={progress}
        message={progressMessage}
        variant="linear"
        size="medium"
      />

      {/* Scan Input Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Initiate Stock Scan
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stock Symbols (comma-separated)"
                value={symbols}
                onChange={(e) => setSymbols(e.target.value)}
                placeholder="AAPL,GOOGL,MSFT,TSLA"
                disabled={state.scanLoading}
                helperText="Enter stock symbols separated by commas"
                error={!state.settings}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={handleScan}
                  disabled={state.scanLoading || !state.settings || state.apiStatus !== 'online'}
                  sx={{ minWidth: 120 }}
                >
                  {state.scanLoading ? 'Scanning...' : 'Start Scan'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<History />}
                  onClick={onViewHistory}
                  disabled={state.scanLoading}
                >
                  History
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  onClick={onConfigureSettings}
                  disabled={state.scanLoading}
                >
                  Settings
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Display */}
      {state.scanError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={clearScanError}>
          {state.scanError}
        </Alert>
      )}

      {/* Settings Loading Warning */}
      {!state.settings && state.settingsLoading && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Loading algorithm settings...
        </Alert>
      )}

      {/* Settings Error Warning */}
      {!state.settings && state.settingsError && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Unable to load settings. Please check the Settings tab.
        </Alert>
      )}

      {/* API Status Warning */}
      {state.apiStatus !== 'online' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          API server is {state.apiStatus}. Scanning may not be available.
        </Alert>
      )}

      {/* Scan Results */}
      {state.currentScanResult && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Scan Results
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Scanned {state.currentScanResult.symbols_scanned.length} symbols in {formatExecutionTime(state.currentScanResult.execution_time)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Found {state.currentScanResult.signals_found.length} signals
              </Typography>
            </Box>

            {state.currentScanResult.signals_found.length === 0 ? (
              <Alert severity="info">
                No trading signals found matching the current algorithm criteria.
              </Alert>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Signal</TableCell>
                      <TableCell>Price</TableCell>
                      <TableCell>EMA5</TableCell>
                      <TableCell>EMA8</TableCell>
                      <TableCell>EMA21</TableCell>
                      <TableCell>ATR</TableCell>
                      <TableCell>Confidence</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {state.currentScanResult.signals_found.map((signal: Signal, index: number) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {signal.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={signal.signal_type.toUpperCase()}
                            color={getSignalColor(signal.signal_type)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{formatPrice(signal.price)}</TableCell>
                        <TableCell>{signal.indicators.ema5.toFixed(2)}</TableCell>
                        <TableCell>{signal.indicators.ema8.toFixed(2)}</TableCell>
                        <TableCell>{signal.indicators.ema21.toFixed(2)}</TableCell>
                        <TableCell>{signal.indicators.atr.toFixed(2)}</TableCell>
                        <TableCell>{formatPercentage(signal.confidence)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ScannerDashboard;