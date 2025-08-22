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
} from '@mui/material';
import { Search, Visibility, Refresh } from '@mui/icons-material';
import { ApiService, handleApiError } from '../services/api';
import { ScanResult, BacktestResult, HistoryFilters } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

const HistoryViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([]);
  const [backtestHistory, setBacktestHistory] = useState<BacktestResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  // Filters
  const [filters, setFilters] = useState<HistoryFilters>({});
  const [symbolFilter, setSymbolFilter] = useState<string>('');
  const [signalTypeFilter, setSignalTypeFilter] = useState<string>('all');
  const [startDateFilter, setStartDateFilter] = useState<string>('');
  const [endDateFilter, setEndDateFilter] = useState<string>('');
  
  // Pagination
  const [scanPage, setScanPage] = useState<number>(1);
  const [backtestPage, setBacktestPage] = useState<number>(1);
  const itemsPerPage = 10;
  
  // Detail dialog
  const [selectedItem, setSelectedItem] = useState<ScanResult | BacktestResult | null>(null);
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
      setError(handleApiError(err));
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
      setError(handleApiError(err));
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

  const viewDetails = (item: ScanResult | BacktestResult) => {
    setSelectedItem(item);
    setDetailDialogOpen(true);
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

  const isScanResult = (item: ScanResult | BacktestResult): item is ScanResult => {
    return 'signals_found' in item;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        History Viewer
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Symbol"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                placeholder="AAPL"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Signal Type</InputLabel>
                <Select
                  value={signalTypeFilter}
                  onChange={(e) => setSignalTypeFilter(e.target.value)}
                  label="Signal Type"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="long">Long</MenuItem>
                  <MenuItem value="short">Short</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={startDateFilter}
                onChange={(e) => setStartDateFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={endDateFilter}
                onChange={(e) => setEndDateFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
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
                >
                  Refresh
                </Button>
              </Box>
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

      {/* Loading Indicator */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Tabs */}
      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label={`Scan History (${scanHistory.length})`} />
            <Tab label={`Backtest History (${backtestHistory.length})`} />
          </Tabs>

          {/* Scan History Tab */}
          <TabPanel value={activeTab} index={0}>
            {scanHistory.length === 0 ? (
              <Alert severity="info">No scan history found.</Alert>
            ) : (
              <>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date/Time</TableCell>
                        <TableCell>Symbols Scanned</TableCell>
                        <TableCell>Signals Found</TableCell>
                        <TableCell>Execution Time</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {getPaginatedScans().map((scan: ScanResult) => (
                        <TableRow key={scan.id}>
                          <TableCell>{formatDateTime(scan.timestamp)}</TableCell>
                          <TableCell>
                            <Chip 
                              label={`${scan.symbols_scanned.length} symbols`} 
                              size="small" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={`${scan.signals_found.length} signals`}
                              color={scan.signals_found.length > 0 ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{scan.execution_time.toFixed(2)}s</TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              startIcon={<Visibility />}
                              onClick={() => viewDetails(scan)}
                            >
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={Math.ceil(scanHistory.length / itemsPerPage)}
                    page={scanPage}
                    onChange={(_, page) => setScanPage(page)}
                  />
                </Box>
              </>
            )}
          </TabPanel>

          {/* Backtest History Tab */}
          <TabPanel value={activeTab} index={1}>
            {backtestHistory.length === 0 ? (
              <Alert severity="info">No backtest history found.</Alert>
            ) : (
              <>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date/Time</TableCell>
                        <TableCell>Period</TableCell>
                        <TableCell>Symbols</TableCell>
                        <TableCell>Total Trades</TableCell>
                        <TableCell>Win Rate</TableCell>
                        <TableCell>Total Return</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {getPaginatedBacktests().map((backtest: BacktestResult) => (
                        <TableRow key={backtest.id}>
                          <TableCell>{formatDateTime(backtest.timestamp)}</TableCell>
                          <TableCell>
                            {backtest.start_date} to {backtest.end_date}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={`${backtest.symbols.length} symbols`} 
                              size="small" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{backtest.performance.total_trades}</TableCell>
                          <TableCell>
                            <Typography 
                              color={backtest.performance.win_rate >= 0.5 ? 'success.main' : 'error.main'}
                            >
                              {formatPercentage(backtest.performance.win_rate)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              color={backtest.performance.total_return >= 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercentage(backtest.performance.total_return)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              startIcon={<Visibility />}
                              onClick={() => viewDetails(backtest)}
                            >
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={Math.ceil(backtestHistory.length / itemsPerPage)}
                    page={backtestPage}
                    onChange={(_, page) => setBacktestPage(page)}
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
      >
        <DialogTitle>
          {selectedItem && isScanResult(selectedItem) ? 'Scan Details' : 'Backtest Details'}
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                ID: {selectedItem.id}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Timestamp: {formatDateTime(selectedItem.timestamp)}
              </Typography>
              
              {isScanResult(selectedItem) ? (
                <>
                  <Typography variant="body2" gutterBottom>
                    Symbols Scanned: {selectedItem.symbols_scanned.join(', ')}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Execution Time: {selectedItem.execution_time.toFixed(2)}s
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Signals Found: {selectedItem.signals_found.length}
                  </Typography>
                  {selectedItem.signals_found.map((signal, index) => (
                    <Box key={index} sx={{ ml: 2, mb: 1 }}>
                      <Typography variant="body2">
                        {signal.symbol} - {signal.signal_type.toUpperCase()} at {formatPrice(signal.price)}
                      </Typography>
                    </Box>
                  ))}
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
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HistoryViewer;