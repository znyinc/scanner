import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Chip,
  Grid,
  Paper,
  Tabs,
  Tab,
  Pagination,
  useTheme,
  useMediaQuery,
  Skeleton,
} from '@mui/material';
import {
  Search as SearchIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
// import * as ReactWindow from 'react-window';
import SymbolBadge from '../SymbolBadge';
import { SymbolDiagnostic } from '../../types';

export interface SymbolsScannedSectionProps {
  symbolDetails: Record<string, SymbolDiagnostic>;
  symbolsWithData: string[];
  symbolsWithoutData: string[];
  symbolsWithErrors: Record<string, string>;
  enableVirtualization?: boolean;
  itemsPerPage?: number;
  className?: string;
}

interface SymbolCategory {
  id: string;
  label: string;
  count: number;
  color: 'success' | 'warning' | 'error' | 'default';
  icon: React.ReactNode;
  symbols: string[];
}

interface VirtualizedItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    symbols: string[];
    symbolDetails: Record<string, SymbolDiagnostic>;
    onSymbolClick?: (symbol: string) => void;
  };
}

const ITEMS_PER_PAGE = 50;
const ITEM_HEIGHT = 40;
const MAX_ITEMS_FOR_VIRTUALIZATION = 100;

const SymbolsScannedSection: React.FC<SymbolsScannedSectionProps> = ({
  symbolDetails,
  symbolsWithData,
  symbolsWithoutData,
  symbolsWithErrors,
  enableVirtualization = true,
  itemsPerPage = ITEMS_PER_PAGE,
  className,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);

  // Create symbol categories
  const categories = useMemo((): SymbolCategory[] => {
    const allSymbols = [
      ...symbolsWithData,
      ...symbolsWithoutData,
      ...Object.keys(symbolsWithErrors),
    ];

    return [
      {
        id: 'all',
        label: 'All Symbols',
        count: allSymbols.length,
        color: 'default',
        icon: <InfoIcon fontSize="small" />,
        symbols: allSymbols,
      },
      {
        id: 'success',
        label: 'Successful',
        count: symbolsWithData.length,
        color: 'success',
        icon: <SuccessIcon fontSize="small" />,
        symbols: symbolsWithData,
      },
      {
        id: 'no-data',
        label: 'No Data',
        count: symbolsWithoutData.length,
        color: 'warning',
        icon: <WarningIcon fontSize="small" />,
        symbols: symbolsWithoutData,
      },
      {
        id: 'errors',
        label: 'Errors',
        count: Object.keys(symbolsWithErrors).length,
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        symbols: Object.keys(symbolsWithErrors),
      },
    ];
  }, [symbolsWithData, symbolsWithoutData, symbolsWithErrors]);

  // Get current category
  const currentCategory = categories.find(cat => cat.id === selectedCategory) || categories[0];

  // Filter symbols based on search term
  const filteredSymbols = useMemo(() => {
    let symbols = currentCategory.symbols;
    
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      symbols = symbols.filter(symbol => 
        symbol.toLowerCase().includes(searchLower)
      );
    }
    
    return symbols.sort();
  }, [currentCategory.symbols, searchTerm]);

  // Pagination logic
  const totalPages = Math.ceil(filteredSymbols.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedSymbols = filteredSymbols.slice(startIndex, endIndex);

  // Determine if we should use virtualization (disabled for now)
  const shouldUseVirtualization = false; // Temporarily disabled due to react-window compatibility issues

  // Get symbol status for badge
  const getSymbolStatus = (symbol: string): 'success' | 'warning' | 'error' | 'no-data' => {
    if (symbolsWithData.includes(symbol)) return 'success';
    if (symbolsWithErrors[symbol]) return 'error';
    if (symbolsWithoutData.includes(symbol)) return 'no-data';
    return 'no-data';
  };

  // Handle search input change
  const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setCurrentPage(1); // Reset to first page when searching
  }, []);

  // Handle category change
  const handleCategoryChange = useCallback((_: React.SyntheticEvent, newValue: string) => {
    setSelectedCategory(newValue);
    setCurrentPage(1); // Reset to first page when changing category
  }, []);

  // Handle page change
  const handlePageChange = useCallback((_: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  }, []);

  // Handle symbol click
  const handleSymbolClick = useCallback((symbol: string) => {
    // Could be used for navigation or detailed view
    console.log('Symbol clicked:', symbol);
  }, []);

  // Virtualized list item renderer (disabled for now)
  // const VirtualizedItem: React.FC<VirtualizedItemProps> = ({ index, style, data }) => {
  //   const symbol = data.symbols[index];
  //   const status = getSymbolStatus(symbol);
  //   const diagnostic = data.symbolDetails[symbol];

  //   return (
  //     <div style={style}>
  //       <Box sx={{ p: 0.5 }}>
  //         <SymbolBadge
  //           symbol={symbol}
  //           status={status}
  //           diagnostic={diagnostic}
  //           showDetails={true}
  //           onClick={() => data.onSymbolClick?.(symbol)}
  //         />
  //       </Box>
  //     </div>
  //   );
  // };

  // Regular symbol grid renderer
  const renderSymbolGrid = () => {
    if (paginatedSymbols.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {searchTerm ? 'No symbols match your search criteria.' : 'No symbols in this category.'}
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={1} sx={{ mb: 2 }}>
        {paginatedSymbols.map((symbol) => {
          const status = getSymbolStatus(symbol);
          const diagnostic = symbolDetails[symbol];
          
          return (
            <Grid item key={symbol} xs="auto">
              <SymbolBadge
                symbol={symbol}
                status={status}
                diagnostic={diagnostic}
                showDetails={true}
                onClick={() => handleSymbolClick(symbol)}
              />
            </Grid>
          );
        })}
      </Grid>
    );
  };

  // Virtualized symbol list renderer (disabled for now)
  const renderVirtualizedList = () => {
    // For now, fall back to regular grid when virtualization is requested
    return renderSymbolGrid();
  };

  return (
    <Box className={className} role="region" aria-label="Symbols scanned results">
      {/* Summary Statistics */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="body1" color="text.primary" gutterBottom>
          Symbol Processing Summary
        </Typography>
        <Grid container spacing={1}>
          {categories.slice(1).map((category) => (
            <Grid item key={category.id} xs="auto">
              <Chip
                label={`${category.label}: ${category.count}`}
                color={category.color}
                variant="outlined"
                size="small"
              />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Search and Filter Controls */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search symbols..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <Tabs
          value={selectedCategory}
          onChange={handleCategoryChange}
          variant={isMobile ? "scrollable" : "standard"}
          scrollButtons="auto"
          allowScrollButtonsMobile
        >
          {categories.map((category) => (
            <Tab
              key={category.id}
              value={category.id}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <span>{category.label}</span>
                  <Chip
                    label={category.count}
                    size="small"
                    color={category.color}
                    variant="outlined"
                    sx={{ ml: 0.5, fontSize: '0.7rem', height: 18 }}
                  />
                </Box>
              }
            />
          ))}
        </Tabs>
      </Box>

      {/* Results Display */}
      <Paper elevation={0} sx={{ p: 2, border: `1px solid ${theme.palette.divider}` }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {filteredSymbols.length} symbol{filteredSymbols.length !== 1 ? 's' : ''} found
            {searchTerm && ` matching "${searchTerm}"`}
          </Typography>
          
          {shouldUseVirtualization && (
            <Chip
              label="Virtualized"
              size="small"
              color="info"
              variant="outlined"
            />
          )}
        </Box>

        {/* Symbol Display */}
        {shouldUseVirtualization ? renderVirtualizedList() : renderSymbolGrid()}

        {/* Pagination */}
        {!shouldUseVirtualization && totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              size={isMobile ? "small" : "medium"}
              showFirstButton
              showLastButton
            />
          </Box>
        )}

        {/* Results Info */}
        {!shouldUseVirtualization && filteredSymbols.length > itemsPerPage && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 1 }}>
            Showing {startIndex + 1}-{Math.min(endIndex, filteredSymbols.length)} of {filteredSymbols.length} symbols
          </Typography>
        )}
      </Paper>

      {/* Performance Note */}
      {filteredSymbols.length > MAX_ITEMS_FOR_VIRTUALIZATION && !enableVirtualization && (
        <Box sx={{ mt: 2, p: 1, backgroundColor: theme.palette.info.light + '20', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            💡 Large symbol list detected. Consider enabling virtualization for better performance.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default SymbolsScannedSection;