import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Refresh, TrendingUp, TrendingDown } from '@mui/icons-material';
import { ApiService, handleApiError } from '../services/api';

interface MarketDataRow {
  symbol: string;
  lastPrice: number | null;
  priceChange: number | null;
  priceChangePercent: number | null;
  volume: number | null;
  exchange: string | null;
  status: 'loading' | 'success' | 'error';
  error?: string;
}

interface MarketDataTableProps {
  symbols: string[];
  onRefresh?: () => void;
}

const MarketDataTable: React.FC<MarketDataTableProps> = ({ symbols, onRefresh }) => {
  const [marketData, setMarketData] = useState<MarketDataRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const fetchMarketData = async () => {
    if (symbols.length === 0) return;

    setIsLoading(true);
    
    // Initialize data rows
    const initialData: MarketDataRow[] = symbols.map(symbol => ({
      symbol: symbol.toUpperCase(),
      lastPrice: null,
      priceChange: null,
      priceChangePercent: null,
      volume: null,
      exchange: null,
      status: 'loading'
    }));
    
    setMarketData(initialData);

    // Fetch data for each symbol
    const updatedData = await Promise.all(
      symbols.map(async (symbol, index) => {
        try {
          // Call a simple market data endpoint (we'll create this)
          const response = await ApiService.getMarketData(symbol.toUpperCase());
          
          return {
            symbol: symbol.toUpperCase(),
            lastPrice: response.lastPrice,
            priceChange: response.priceChange,
            priceChangePercent: response.priceChangePercent,
            volume: response.volume,
            exchange: response.exchange,
            status: 'success' as const
          };
        } catch (error) {
          return {
            symbol: symbol.toUpperCase(),
            lastPrice: null,
            priceChange: null,
            priceChangePercent: null,
            volume: null,
            exchange: null,
            status: 'error' as const,
            error: handleApiError(error).message
          };
        }
      })
    );

    setMarketData(updatedData);
    setIsLoading(false);
  };

  const formatPrice = (price: number | null): string => {
    if (price === null) return 'N/A';
    return `$${price.toFixed(2)}`;
  };

  const formatChange = (change: number | null, percent: number | null): React.ReactNode => {
    if (change === null || percent === null) return 'N/A';
    
    const isPositive = change >= 0;
    const color = isPositive ? 'success.main' : 'error.main';
    const icon = isPositive ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />;
    
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color }}>
        {icon}
        <span>{isPositive ? '+' : ''}${change.toFixed(2)} ({isPositive ? '+' : ''}{percent.toFixed(2)}%)</span>
      </Box>
    );
  };

  const formatVolume = (volume: number | null): string => {
    if (volume === null) return 'N/A';
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toLocaleString();
  };

  const getStatusChip = (status: MarketDataRow['status']) => {
    switch (status) {
      case 'loading':
        return <CircularProgress size={16} />;
      case 'success':
        return <Chip label="Success" color="success" size="small" />;
      case 'error':
        return <Chip label="Error" color="error" size="small" />;
      default:
        return null;
    }
  };

  if (symbols.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Market Data Verification
          </Typography>
          <Alert severity="info">
            Enter stock symbols above to test market data retrieval
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Market Data Verification
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchMarketData}
            disabled={isLoading}
            size="small"
          >
            {isLoading ? 'Loading...' : 'Fetch Data'}
          </Button>
        </Box>

        {marketData.length > 0 && (
          <TableContainer component={Paper} variant="outlined">
            <Table size={isMobile ? "small" : "medium"}>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Symbol</strong></TableCell>
                  <TableCell align="right"><strong>Last Price</strong></TableCell>
                  {!isMobile && <TableCell align="right"><strong>Change</strong></TableCell>}
                  {!isMobile && <TableCell align="right"><strong>Volume</strong></TableCell>}
                  {!isMobile && <TableCell><strong>Exchange</strong></TableCell>}
                  <TableCell align="center"><strong>Status</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {marketData.map((row) => (
                  <TableRow key={row.symbol}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {row.symbol}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {formatPrice(row.lastPrice)}
                      </Typography>
                    </TableCell>
                    {!isMobile && (
                      <TableCell align="right">
                        {formatChange(row.priceChange, row.priceChangePercent)}
                      </TableCell>
                    )}
                    {!isMobile && (
                      <TableCell align="right">
                        <Typography variant="body2">
                          {formatVolume(row.volume)}
                        </Typography>
                      </TableCell>
                    )}
                    {!isMobile && (
                      <TableCell>
                        <Typography variant="body2">
                          {row.exchange || 'N/A'}
                        </Typography>
                      </TableCell>
                    )}
                    <TableCell align="center">
                      {getStatusChip(row.status)}
                      {row.error && (
                        <Typography variant="caption" color="error" display="block" sx={{ mt: 0.5 }}>
                          {row.error}
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {isMobile && marketData.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Mobile view shows Symbol, Price, and Status. Use desktop for full details.
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MarketDataTable;