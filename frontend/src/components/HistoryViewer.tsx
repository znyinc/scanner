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
  Tabs,
  Tab,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useMediaQuery,
  useTheme,
  Stack,
} from '@mui/material';
import { Search, Visibility, Refresh } from '@mui/icons-material';
import { ApiService, handleApiError } from '../services/api';
import { BacktestResult, HistoryFilters, EnhancedScanResult } from '../types';
import ResponsiveTable from './ResponsiveTable';
import DiagnosticDetails from './DiagnosticDetails';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div 
      role="tabpanel"
      hidden={value !== index}
      id={`history-tabpanel-${index}`}
      aria-labelledby={`history-tab-${index}`}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

const HistoryViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [scanHistory, setScanHistory] = useState<EnhancedScanResult[]>([]);
  const [backtestHistory, setBacktestHistory] = useState<BacktestResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Diagnostic state
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false);
  const [expandedDiagnostics, setExpandedDiagnostics] = useState<Set<string>>(new Set());
  
  // Filters
  const [filters, setFilters] = useState<HistoryFilters>({});
  const [symbolFilter, setSymbolFilter] = useState<string>('');
  const [signalTypeFilter, setSignalTypeFilter] = useState<string>('all');
  const [startDateFilter, setStartDateFilter] = useState<string>('');
  const [endDateFilter, setEndDateFilter] = useState<string>('');
  
  // Pagination
  const [scanPage, setScanPage] = useState<number>(1);
  const [backtestPage, setBacktestPage] = useState<number>(1);
  const itemsPerPage = isMobile ? 5 : 10;
  
  // Detail dialog
  const [selectedItem, setSelectedItem] = useState<EnhancedScanResult | BacktestResult | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState<boolean>(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const [scans, backtests] = await Promise.all([
        ApiService.getScanHistory(filters),
        ApiService.getBacktestHistory(filters)
      ]);
      
      setScanHistory(scans);
      setBacktestHistory(backtests);
    } catch (err) {
      setError(handleApiError(err).message);
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilters = () => {
    const newFilters: HistoryFilters = {};
    
    if (symbolFilter.trim()) {
      newFilters.symbol = symbolFilter.trim().toUpperCase();
    }
    
    if (signalTypeFilter !== 'all') {
      newFilters.signal_type = signalTypeFilter as 'long' | 'short';
    }
    
    if (startDateFilter) {
      newFilters.start_date = startDateFilter;
    }
    
    if (endDateFilter) {
      newFilters.end_date = endDateFilter;
    }
    
    setFilters(newFilters);
    setScanPage(1);
    setBacktestPage(1);
    loadHistoryWithFilters(newFilters);
  };

  const loadHistoryWithFilters = async (appliedFilters: HistoryFilters) => {
    setIsLoading(true);
    setError('');
    
    try {
      const [scans, backtests] = await Promise.all([
        ApiService.getScanHistory(appliedFilters),
        ApiService.getBacktestHistory(appliedFilters)
      ]);
      
      setScanHistory(scans);
      setBacktestHistory(backtests);
    } catch (err) {
      setError(handleApiError(err).message);
    } finally {
      setIsLoading(false);
    }
  };

  const clearFilters = () => {
    setSymbolFilter('');
    setSignalTypeFilter('all');
    setStartDateFilter('');
    setEndDateFilter('');
    setFilters({});
    setScanPage(1);
    setBacktestPage(1);
    loadHistory();
  };

  const viewDetails = (item: EnhancedScanResult | BacktestResult) => {
    setSelectedItem(item);
    setDetailDialogOpen(true);
  };

  // Toggle diagnostic details for a specific scan
  const toggleDiagnostics = (scanId: string) => {
    setExpandedDiagnostics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(scanId)) {
        newSet.delete(scanId);
      } else {
        newSet.add(scanId);
      }
      return newSet;
    });
  };

  // Handle diagnostic export
  const handleDiagnosticExport = (scanId: string) => {
    // TODO: Implement export functionality
    console.log('Export diagnostics for scan:', scanId);
  };

  // Handle diagnostic refresh
  const handleDiagnosticRefresh = (scanId: string) => {
    // TODO: Implement refresh functionality
    console.log('Refresh diagnostics for scan:', scanId);
  };

  const formatDateTime = (dateTime: string): string => {
    return new Date(dateTime).toLocaleString();
  };

  const formatPrice = (price: number): string => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  // Pagination helpers
  const getPaginatedScans = () => {
    const startIndex = (scanPage - 1) * itemsPerPage;
    return scanHistory.slice(startIndex, startIndex + itemsPerPage);
  };

  const getPaginatedBacktests = () => {
    const startIndex = (backtestPage - 1) * itemsPerPage;
    return backtestHistory.slice(startIndex, startIndex + itemsPerPage);
  };

  const isScanResult = (item: EnhancedScanResult | BacktestResult): item is EnhancedScanResult => {
    return 'signals_found' in item;
  };

  // Define table columns for scan history
  const scanHistoryColumns = [
    { 
      id: 'timestamp', 
      label: 'Date/Time', 
      priority: 1,
      format: formatDateTime
    },
    { 
      id: 'symbols_scanned_count', 
      label: 'Symbols', 
      priority: 2,
      format: (value: number) => `${value} symbols`
    },
    { 
      id: 'signals_found_count', 
      label: 'Signals', 
      priority: 1,
      format: (value: number) => `${value} signals`
    },
    { 
      id: 'scan_status', 
      label: 'Status', 
      priority: 2,
      format: (value: string) => value || 'completed'
    },
    { 
      id: 'execution_time', 
      label: 'Time', 
      priority: 3,
      hideOnMobile: true,
      format: (value: number) => `${value.toFixed(2)}s`
    },
  ];

  // Define table columns for backtest history
  const backtestHistoryColumns = [
    { 
      id: 'timestamp', 
      label: 'Date/Time', 
      priority: 1,
      format: formatDateTime
    },
    { 
      id: 'period', 
      label: 'Period', 
      priority: 3,
      hideOnMobile: true,
      format: (value: string) => value
    },
    { 
      id: 'symbols_count', 
      label: 'Symbols', 
      priority: 2,
      format: (value: number) => `${value} symbols`
    },
    { 
      id: 'total_trades', 
      label: 'Trades', 
      priority: 2,
      format: (value: number) => value.toString()
    },
    { 
      id: 'win_rate', 
      label: 'Win Rate', 
      priority: 1,
      format: formatPercentage
    },
    { 
      id: 'total_return', 
      label: 'Return', 
      priority: 1,
      format: formatPercentage
    },
  ];

  // Transform scan history for table display
  const getScanHistoryRows = () => {
    return getPaginatedScans().map((scan: EnhancedScanResult) => ({
      id: scan.id,
      timestamp: scan.timestamp,
      symbols_scanned_count: scan.symbols_scanned.length,
      signals_found_count: scan.signals_found.length,
      scan_status: scan.scan_status || 'completed',
      execution_time: scan.execution_time,
      _original: scan
    }));
  };

  // Transform backtest history for table display
  const getBacktestHistoryRows = () => {
    return getPaginatedBacktests().map((backtest: BacktestResult) => ({
      id: backtest.id,
      timestamp: backtest.timestamp,
      period: `${backtest.start_date} to ${backtest.end_date}`,
      symbols_count: backtest.symbols.length,
      total_trades: backtest.performance.total_trades,
      win_rate: backtest.performance.win_rate,
      total_return: backtest.performance.total_return,
      _original: backtest
    }));
  };

  // Get status color for scan status
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'partial': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  // Mobile card renderer for scan history
  const renderScanCard = (row: any, index: number) => {
    const scan = row._original;
    const hasErrors = scan.diagnostics?.symbols_with_errors && Object.keys(scan.diagnostics.symbols_with_errors).length > 0;
    const hasNoData = scan.diagnostics?.symbols_without_data && scan.diagnostics.symbols_without_data.length > 0;
    
    return (
      <Box key={index}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {formatDateTime(row.timestamp)}
          </Typography>
          <Button
            size="small"
            startIcon={<Visibility />}
            onClick={() => viewDetails(row._original)}
            aria-label={`View scan details from ${formatDateTime(row.timestamp)}`}
          >
            View
          </Button>
        </Box>
        <Grid container spacing={1}>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">
              Status
            </Typography>
            <Chip 
              label={row.scan_status}
              color={getStatusColor(row.scan_status)}
              size="small"
            />
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">
              Symbols
            </Typography>
            <Chip 
              label={`${row.symbols_scanned_count}`} 
              size="small" 
              variant="outlined"
            />
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">
              Signals
            </Typography>
            <Chip 
              label={`${row.signals_found_count}`}
              color={row.signals_found_count > 0 ? 'success' : 'default'}
              size="small"
            />
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">
              Time
            </Typography>
            <Typography variant="body2">
              {row.execution_time.toFixed(2)}s
            </Typography>
          </Grid>
        </Grid>
        
        {/* Diagnostic Summary */}
        {scan.diagnostics && !showDiagnostics && (
          <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary" display="block">
              Data: {scan.diagnostics.symbols_with_data.length} success
              {hasNoData && `, ${scan.diagnostics.symbols_without_data.length} no data`}
              {hasErrors && `, ${Object.keys(scan.diagnostics.symbols_with_errors).length} errors`}
            </Typography>
            {scan.error_message && (
              <Typography variant="caption" color="error.main" display="block">
                {scan.error_message}
              </Typography>
            )}
          </Box>
        )}

        {/* Enhanced Diagnostic Details */}
        {showDiagnostics && scan.diagnostics && (
          <Box sx={{ mt: 2 }}>
            <DiagnosticDetails
              scanResult={scan}
              expanded={expandedDiagnostics.has(scan.id)}
              onToggle={() => toggleDiagnostics(scan.id)}
              showExportButton={true}
              onExport={handleDiagnosticExport}
              onRefresh={handleDiagnosticRefresh}
            />
          </Box>
        )}
      </Box>
    );
  };

  // Mobile card renderer for backtest history
  const renderBacktestCard = (row: any, index: number) => (
    <Box key={index}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {formatDateTime(row.timestamp)}
        </Typography>
        <Button
          size="small"
          startIcon={<Visibility />}
          onClick={() => viewDetails(row._original)}
          aria-label={`View backtest details from ${formatDateTime(row.timestamp)}`}
        >
          View
        </Button>
      </Box>
      <Grid container spacing={1}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Win Rate
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold"
            color={row.win_rate >= 0.5 ? 'success.main' : 'error.main'}
          >
            {formatPercentage(row.win_rate)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Return
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight="bold"
            color={row.total_return >= 0 ? 'success.main' : 'error.main'}
          >
            {formatPercentage(row.total_return)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Trades
          </Typography>
          <Typography variant="body2">
            {row.total_trades}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Symbols
          </Typography>
          <Typography variant="body2">
            {row.symbols_count}
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
        id="history-title"
      >
        History Viewer
      </Typography>
      
      {/* Screen reader announcement */}
      <div className="sr-only" aria-live="polite">
        History viewer loaded. Use filters to search through past scans and backtests.
      </div>

      {/* Filters */}
      <Card sx={{ mb: 3 }} role="region" aria-labelledby="filters-title">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom id="filters-title">
            Search Filters
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Symbol"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                placeholder="AAPL"
                size="small"
                inputProps={{
                  'aria-label': 'Filter by stock symbol',
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="signal-type-filter-label">Signal Type</InputLabel>
                <Select
                  labelId="signal-type-filter-label"
                  value={signalTypeFilter}
                  onChange={(e) => setSignalTypeFilter(e.target.value)}
                  label="Signal Type"
                  aria-label="Filter by signal type"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="long">Long</MenuItem>
                  <MenuItem value="short">Short</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={startDateFilter}
                onChange={(e) => setStartDateFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
                inputProps={{
                  'aria-label': 'Filter start date',
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={endDateFilter}
                onChange={(e) => setEndDateFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
                inputProps={{
                  'aria-label': 'Filter end date',
                }}
              />
            </Grid>
            <Grid item xs={12}>
              {isMobile ? (
                <Stack spacing={1}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<Search />}
                    onClick={applyFilters}
                    disabled={isLoading}
                  >
                    Apply Filters
                  </Button>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      onClick={clearFilters}
                      disabled={isLoading}
                      sx={{ flex: 1 }}
                    >
                      Clear
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={loadHistory}
                      disabled={isLoading}
                      sx={{ flex: 1 }}
                      aria-label="Refresh history data"
                    >
                      Refresh
                    </Button>
                  </Box>
                  <Button
                    fullWidth
                    variant={showDiagnostics ? "contained" : "outlined"}
                    onClick={() => setShowDiagnostics(!showDiagnostics)}
                    disabled={isLoading}
                    aria-label={showDiagnostics ? "Hide diagnostics" : "Show diagnostics"}
                  >
                    {showDiagnostics ? "Hide" : "Show"} Diagnostics
                  </Button>
                </Stack>
              ) : (
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    startIcon={<Search />}
                    onClick={applyFilters}
                    disabled={isLoading}
                  >
                    Apply Filters
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={clearFilters}
                    disabled={isLoading}
                  >
                    Clear
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadHistory}
                    disabled={isLoading}
                    aria-label="Refresh history data"
                  >
                    Refresh
                  </Button>
                  <Button
                    variant={showDiagnostics ? "contained" : "outlined"}
                    onClick={() => setShowDiagnostics(!showDiagnostics)}
                    disabled={isLoading}
                    aria-label={showDiagnostics ? "Hide diagnostics" : "Show diagnostics"}
                  >
                    {showDiagnostics ? "Hide" : "Show"} Diagnostics
                  </Button>
                </Box>
              )}
            </Grid>
          </Grid>
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

      {/* Loading Indicator */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <CircularProgress aria-label="Loading history data" />
        </Box>
      )}

      {/* Tabs */}
      <Card>
        <CardContent>
          <Tabs 
            value={activeTab} 
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant={isMobile ? "scrollable" : "standard"}
            scrollButtons={isMobile ? "auto" : false}
            allowScrollButtonsMobile
            aria-label="History type tabs"
          >
            <Tab 
              label={`Scan History (${scanHistory.length})`}
              id="history-tab-0"
              aria-controls="history-tabpanel-0"
            />
            <Tab 
              label={`Backtest History (${backtestHistory.length})`}
              id="history-tab-1"
              aria-controls="history-tabpanel-1"
            />
          </Tabs>

          {/* Scan History Tab */}
          <TabPanel value={activeTab} index={0}>
            {scanHistory.length === 0 ? (
              <Alert severity="info" role="status">No scan history found.</Alert>
            ) : (
              <>
                {isMobile ? (
                  // Mobile card view
                  <Stack spacing={2}>
                    {getPaginatedScans().map((scan, index) => (
                      <Card key={scan.id} variant="outlined">
                        <CardContent>
                          {renderScanCard({ _original: scan, ...scan }, index)}
                        </CardContent>
                      </Card>
                    ))}
                  </Stack>
                ) : (
                  // Desktop table view with optional diagnostics
                  <Box>
                    <ResponsiveTable
                      columns={scanHistoryColumns}
                      rows={getScanHistoryRows()}
                      ariaLabel="Scan history table"
                      mobileCardView={false}
                      stickyHeader={false}
                    />
                    
                    {/* Desktop Diagnostic Details */}
                    {showDiagnostics && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Diagnostic Details
                        </Typography>
                        <Stack spacing={2}>
                          {getPaginatedScans().map((scan) => (
                            scan.diagnostics && (
                              <Card key={`diagnostic-${scan.id}`} variant="outlined">
                                <CardContent>
                                  <Typography variant="subtitle1" gutterBottom>
                                    Scan from {formatDateTime(scan.timestamp)}
                                  </Typography>
                                  <DiagnosticDetails
                                    scanResult={scan}
                                    expanded={expandedDiagnostics.has(scan.id)}
                                    onToggle={() => toggleDiagnostics(scan.id)}
                                    showExportButton={true}
                                    onExport={handleDiagnosticExport}
                                    onRefresh={handleDiagnosticRefresh}
                                  />
                                </CardContent>
                              </Card>
                            )
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Box>
                )}
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={Math.ceil(scanHistory.length / itemsPerPage)}
                    page={scanPage}
                    onChange={(_, page) => setScanPage(page)}
                    size={isMobile ? "small" : "medium"}
                    aria-label="Scan history pagination"
                  />
                </Box>
              </>
            )}
          </TabPanel>

          {/* Backtest History Tab */}
          <TabPanel value={activeTab} index={1}>
            {backtestHistory.length === 0 ? (
              <Alert severity="info" role="status">No backtest history found.</Alert>
            ) : (
              <>
                <ResponsiveTable
                  columns={backtestHistoryColumns}
                  rows={getBacktestHistoryRows()}
                  ariaLabel="Backtest history table"
                  mobileCardView={true}
                  renderMobileCard={renderBacktestCard}
                  stickyHeader={false}
                />
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={Math.ceil(backtestHistory.length / itemsPerPage)}
                    page={backtestPage}
                    onChange={(_, page) => setBacktestPage(page)}
                    size={isMobile ? "small" : "medium"}
                    aria-label="Backtest history pagination"
                  />
                </Box>
              </>
            )}
          </TabPanel>
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
        aria-labelledby="detail-dialog-title"
        aria-describedby="detail-dialog-description"
      >
        <DialogTitle id="detail-dialog-title">
          {selectedItem && isScanResult(selectedItem) ? 'Scan Details' : 'Backtest Details'}
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ mt: 1 }} id="detail-dialog-description">
              <Typography variant="body2" color="text.secondary" gutterBottom>
                ID: {selectedItem.id}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Timestamp: {formatDateTime(selectedItem.timestamp)}
              </Typography>
              
              {isScanResult(selectedItem) ? (
                <>
                  {/* Basic Scan Information */}
                  <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                    Scan Overview
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Status
                      </Typography>
                      <Chip 
                        label={selectedItem.scan_status || 'completed'}
                        color={getStatusColor(selectedItem.scan_status || 'completed')}
                        size="small"
                        sx={{ mb: 1 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Execution Time
                      </Typography>
                      <Typography variant="body2">
                        {selectedItem.execution_time.toFixed(2)}s
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Symbols Scanned
                      </Typography>
                      <Typography variant="body2">
                        {selectedItem.symbols_scanned.join(', ')}
                      </Typography>
                    </Grid>
                  </Grid>

                  {/* Error Message */}
                  {selectedItem.error_message && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" gutterBottom color="error.main">
                        Error Details
                      </Typography>
                      <Alert severity="error">
                        {selectedItem.error_message}
                      </Alert>
                    </Box>
                  )}

                  {/* Enhanced Diagnostic Information */}
                  {selectedItem.diagnostics && (
                    <Box sx={{ mt: 2 }}>
                      <DiagnosticDetails
                        scanResult={selectedItem}
                        expanded={true}
                        onToggle={() => {}} // Always expanded in dialog
                        showExportButton={true}
                        onExport={handleDiagnosticExport}
                        onRefresh={handleDiagnosticRefresh}
                      />
                    </Box>
                  )}

                  {/* Signals Found */}
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Signals Found ({selectedItem.signals_found.length})
                    </Typography>
                    {selectedItem.signals_found.length > 0 ? (
                      selectedItem.signals_found.map((signal, index) => (
                        <Box key={index} sx={{ ml: 2, mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                          <Typography variant="body2">
                            <strong>{signal.symbol}</strong> - {signal.signal_type.toUpperCase()} at {formatPrice(signal.price)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Confidence: {formatPercentage(signal.confidence)}
                          </Typography>
                        </Box>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No signals found in this scan.
                      </Typography>
                    )}
                  </Box>
                </>
              ) : (
                <>
                  <Typography variant="body2" gutterBottom>
                    Period: {selectedItem.start_date} to {selectedItem.end_date}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Symbols: {selectedItem.symbols.join(', ')}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Total Trades: {selectedItem.performance.total_trades}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Win Rate: {formatPercentage(selectedItem.performance.win_rate)}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Total Return: {formatPercentage(selectedItem.performance.total_return)}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Max Drawdown: {formatPercentage(selectedItem.performance.max_drawdown)}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Sharpe Ratio: {selectedItem.performance.sharpe_ratio.toFixed(2)}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setDetailDialogOpen(false)}
            autoFocus
            aria-label="Close dialog"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HistoryViewer;