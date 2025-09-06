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
  Grid,
  useMediaQuery,
  useTheme,
  Stack,
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
import ResponsiveTable from './ResponsiveTable';
import MarketDataTable from './MarketDataTable';

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleScan = async () => {
    if (!symbols.trim()) {
      return;
    }

    if (!state.settings) {
      return;
    }

    // Prevent multiple concurrent scans
    if (state.scanLoading) {
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

  // Define table columns for scan results
  const scanResultColumns = [
    { 
      id: 'symbol', 
      label: 'Symbol', 
      priority: 1,
      format: (value: string) => value
    },
    { 
      id: 'signal_type', 
      label: 'Signal', 
      priority: 1,
      format: (value: string) => value.toUpperCase()
    },
    { 
      id: 'price', 
      label: 'Price', 
      priority: 2,
      align: 'right' as const,
      format: formatPrice
    },
    { 
      id: 'ema5', 
      label: 'EMA5', 
      priority: 3,
      align: 'right' as const,
      hideOnMobile: true,
      format: (value: number) => value.toFixed(2)
    },
    { 
      id: 'ema8', 
      label: 'EMA8', 
      priority: 4,
      align: 'right' as const,
      hideOnMobile: true,
      format: (value: number) => value.toFixed(2)
    },
    { 
      id: 'ema21', 
      label: 'EMA21', 
      priority: 4,
      align: 'right' as const,
      hideOnMobile: true,
      format: (value: number) => value.toFixed(2)
    },
    { 
      id: 'atr', 
      label: 'ATR', 
      priority: 4,
      align: 'right' as const,
      hideOnMobile: true,
      format: (value: number) => value.toFixed(2)
    },
    { 
      id: 'confidence', 
      label: 'Confidence', 
      priority: 3,
      align: 'right' as const,
      format: formatPercentage
    },
  ];

  // Transform signals for table display
  const getTableRows = () => {
    if (!state.currentScanResult) return [];
    
    return state.currentScanResult.signals_found.map((signal: Signal) => ({
      symbol: signal.symbol,
      signal_type: signal.signal_type,
      price: signal.price,
      ema5: signal.indicators.ema5,
      ema8: signal.indicators.ema8,
      ema21: signal.indicators.ema21,
      atr: signal.indicators.atr,
      confidence: signal.confidence,
    }));
  };

  // Mobile card renderer for scan results
  const renderMobileCard = (row: any, index: number) => (
    <Box key={index} role="group" aria-labelledby={`signal-${index}-symbol`}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography 
          variant="h6" 
          component="h3" 
          id={`signal-${index}-symbol`}
          sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
        >
          {row.symbol}
        </Typography>
        <Chip
          label={row.signal_type.toUpperCase()}
          color={getSignalColor(row.signal_type)}
          size="small"
          aria-label={`${row.signal_type} signal for ${row.symbol}`}
          sx={{
            fontWeight: 600,
            minHeight: 32,
            '& .MuiChip-label': {
              px: 1.5
            }
          }}
        />
      </Box>
      <Grid container spacing={1}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            Price
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold" 
            component="dd"
            sx={{ 
              margin: 0,
              fontSize: { xs: '1rem', sm: '1.125rem' }
            }}
            aria-label={`Current price: ${formatPrice(row.price)}`}
          >
            {formatPrice(row.price)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary" component="dt">
            Confidence
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold" 
            component="dd"
            sx={{ 
              margin: 0,
              fontSize: { xs: '1rem', sm: '1.125rem' },
              color: row.confidence >= 0.7 ? 'success.main' : row.confidence >= 0.5 ? 'warning.main' : 'text.primary'
            }}
            aria-label={`Signal confidence: ${formatPercentage(row.confidence)}`}
          >
            {formatPercentage(row.confidence)}
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
        id="scanner-title"
      >
        Stock Scanner Dashboard
      </Typography>
      
      {/* Screen reader announcement for page content */}
      <div className="sr-only" aria-live="polite" id="page-status">
        Stock scanner dashboard loaded. Use the form below to scan stocks or navigate to other sections.
      </div>

      {/* Progress Indicator */}
      <ProgressIndicator
        isVisible={state.scanLoading}
        progress={progress}
        message={progressMessage}
        variant="linear"
        size="medium"
      />

      {/* Scan Input Section */}
      <Card sx={{ mb: 3 }} role="region" aria-labelledby="scan-input-title">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom id="scan-input-title">
            Initiate Stock Scan
          </Typography>
          
          <Box 
            component="form" 
            role="form" 
            aria-labelledby="scan-input-title"
            onSubmit={(e) => {
              e.preventDefault();
              handleScan();
            }}
          >
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Stock Symbols (comma-separated)"
                  value={symbols}
                  onChange={(e) => setSymbols(e.target.value)}
                  placeholder="AAPL,GOOGL,MSFT,TSLA"
                  disabled={state.scanLoading}
                  helperText="Enter stock symbols separated by commas. Example: AAPL,GOOGL,MSFT"
                  error={!state.settings}
                  inputProps={{
                    'aria-describedby': 'symbols-helper-text',
                    'aria-required': 'true',
                    'aria-invalid': !state.settings,
                  }}
                  id="stock-symbols-input"
                  FormHelperTextProps={{
                    id: 'symbols-helper-text'
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                {isMobile ? (
                  <Stack spacing={1}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<PlayArrow />}
                      onClick={handleScan}
                      disabled={state.scanLoading || !state.settings || state.apiStatus !== 'online'}
                      aria-describedby={state.scanLoading ? 'scan-loading-status' : undefined}
                      sx={{ 
                        minHeight: 48,
                        fontSize: '1rem',
                        fontWeight: 600
                      }}
                      type="button"
                    >
                      {state.scanLoading ? 'Scanning...' : 'Start Scan'}
                    </Button>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="outlined"
                        startIcon={<History />}
                        onClick={onViewHistory}
                        disabled={state.scanLoading}
                        sx={{ 
                          flex: 1,
                          minHeight: 48
                        }}
                        aria-label="View previous scan results and history"
                      >
                        History
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<Settings />}
                        onClick={onConfigureSettings}
                        disabled={state.scanLoading}
                        sx={{ 
                          flex: 1,
                          minHeight: 48
                        }}
                        aria-label="Configure algorithm parameters and settings"
                      >
                        Settings
                      </Button>
                    </Box>
                  </Stack>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      startIcon={<PlayArrow />}
                      onClick={handleScan}
                      disabled={state.scanLoading || !state.settings || state.apiStatus !== 'online'}
                      sx={{ minWidth: 120 }}
                      aria-describedby={state.scanLoading ? 'scan-loading-status' : undefined}
                      type="button"
                    >
                      {state.scanLoading ? 'Scanning...' : 'Start Scan'}
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<History />}
                      onClick={onViewHistory}
                      disabled={state.scanLoading}
                      aria-label="View previous scan results and history"
                    >
                      History
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Settings />}
                      onClick={onConfigureSettings}
                      disabled={state.scanLoading}
                      aria-label="Configure algorithm parameters and settings"
                    >
                      Settings
                    </Button>
                  </Box>
                )}
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Market Data Verification Table */}
      <Box sx={{ mb: 3 }}>
        <MarketDataTable 
          symbols={symbols.split(',').map(s => s.trim()).filter(s => s.length > 0)}
        />
      </Box>

      {/* Error Display */}
      {state.scanError && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={clearScanError}
          role="alert"
          aria-live="polite"
        >
          {state.scanError}
        </Alert>
      )}

      {/* Settings Loading Warning */}
      {!state.settings && state.settingsLoading && (
        <Alert severity="info" sx={{ mb: 3 }} role="status" aria-live="polite">
          Loading algorithm settings...
        </Alert>
      )}

      {/* Settings Error Warning */}
      {!state.settings && state.settingsError && (
        <Alert severity="warning" sx={{ mb: 3 }} role="alert" aria-live="polite">
          Unable to load settings. Please check the Settings tab.
        </Alert>
      )}

      {/* API Status Warning */}
      {state.apiStatus !== 'online' && (
        <Alert severity="warning" sx={{ mb: 3 }} role="alert" aria-live="polite">
          API server is {state.apiStatus}. Scanning may not be available.
        </Alert>
      )}

      {/* Loading Status for Screen Readers */}
      {state.scanLoading && (
        <div id="scan-loading-status" className="sr-only" aria-live="polite">
          Scanning in progress: {progressMessage}
        </div>
      )}

      {/* Scan Results */}
      {state.currentScanResult && (
        <Card role="region" aria-labelledby="scan-results-title">
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom id="scan-results-title">
              Scan Results
            </Typography>
            
            <Box sx={{ mb: 2 }} role="status" aria-live="polite">
              <Typography variant="body2" color="text.secondary">
                Scanned {state.currentScanResult.symbols_scanned.length} symbols in {formatExecutionTime(state.currentScanResult.execution_time)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Found {state.currentScanResult.signals_found.length} trading signals
              </Typography>
            </Box>

            {state.currentScanResult.signals_found.length === 0 ? (
              <Alert 
                severity="info" 
                role="status"
                aria-live="polite"
                sx={{
                  '& .MuiAlert-message': {
                    fontSize: { xs: '0.875rem', sm: '1rem' }
                  }
                }}
              >
                No trading signals found matching the current algorithm criteria. Try adjusting the settings or scanning different symbols.
              </Alert>
            ) : (
              <>
                <div className="sr-only" aria-live="polite">
                  {state.currentScanResult.signals_found.length} trading signals found. Results displayed in {isMobile ? 'card' : 'table'} format below.
                </div>
                <ResponsiveTable
                  columns={scanResultColumns}
                  rows={getTableRows()}
                  ariaLabel={`Scan results showing ${state.currentScanResult.signals_found.length} trading signals`}
                  mobileCardView={true}
                  renderMobileCard={renderMobileCard}
                  stickyHeader={true}
                />
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ScannerDashboard;