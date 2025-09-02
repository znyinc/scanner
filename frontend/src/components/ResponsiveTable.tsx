import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Card,
  CardContent,
  Typography,
  Box,
  useMediaQuery,
  useTheme,
  Stack,
} from '@mui/material';

interface Column {
  id: string;
  label: string;
  minWidth?: number;
  align?: 'right' | 'left' | 'center';
  format?: (value: any) => string;
  hideOnMobile?: boolean;
  priority?: number; // 1 = highest priority (always show), higher numbers hide first on mobile
}

interface ResponsiveTableProps {
  columns: Column[];
  rows: any[];
  ariaLabel?: string;
  maxHeight?: number;
  stickyHeader?: boolean;
  mobileCardView?: boolean;
  renderMobileCard?: (row: any, index: number) => React.ReactNode;
}

const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  columns,
  rows,
  ariaLabel = "Data table",
  maxHeight = 400,
  stickyHeader = false,
  mobileCardView = true,
  renderMobileCard,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Filter columns based on screen size and priority
  const getVisibleColumns = () => {
    if (!isMobile && !isTablet) return columns;
    
    if (isMobile) {
      // On mobile, show only priority 1 columns or first 3 columns if no priorities set
      const priorityColumns = columns.filter(col => col.priority === 1);
      if (priorityColumns.length > 0) {
        return priorityColumns;
      }
      return columns.slice(0, 3);
    }
    
    if (isTablet) {
      // On tablet, hide columns with hideOnMobile or priority > 3
      return columns.filter(col => !col.hideOnMobile && (col.priority || 1) <= 3);
    }
    
    return columns;
  };

  const visibleColumns = getVisibleColumns();

  // Mobile card view
  if (isMobile && mobileCardView && renderMobileCard) {
    return (
      <Box role="table" aria-label={ariaLabel}>
        <div className="sr-only" aria-live="polite">
          Showing {rows.length} items in card view format
        </div>
        <Stack spacing={2}>
          {rows.length === 0 ? (
            <Typography 
              variant="body2" 
              color="text.secondary" 
              textAlign="center"
              role="status"
              aria-live="polite"
            >
              No data available
            </Typography>
          ) : (
            rows.map((row, index) => (
              <Card 
                key={index} 
                variant="outlined"
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    boxShadow: 2,
                    transform: 'translateY(-1px)',
                  },
                  '&:active': {
                    transform: 'translateY(0)',
                    boxShadow: 1,
                  },
                  // Enhanced touch feedback
                  '@media (hover: none)': {
                    '&:active': {
                      backgroundColor: 'action.selected',
                    }
                  }
                }}
                role="row"
                tabIndex={0}
                aria-rowindex={index + 1}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    // Handle card selection if needed
                  }
                }}
              >
                <CardContent sx={{ 
                  p: 2, 
                  '&:last-child': { pb: 2 },
                  // Improve touch target size
                  minHeight: 48
                }}>
                  {renderMobileCard(row, index)}
                </CardContent>
              </Card>
            ))
          )}
        </Stack>
      </Box>
    );
  }

  // Standard table view with responsive columns
  return (
    <TableContainer 
      component={Paper} 
      sx={{ 
        maxHeight: isMobile ? 'none' : maxHeight,
        overflowX: 'auto',
        // Improve mobile scrolling
        WebkitOverflowScrolling: 'touch',
        // Add scroll indicators for mobile
        '&::-webkit-scrollbar': {
          height: isMobile ? 4 : 8,
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'rgba(0,0,0,0.1)',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0,0,0,0.3)',
          borderRadius: 4,
        },
      }}
      role="region"
      aria-label={`${ariaLabel} - scrollable table`}
      tabIndex={0}
    >
      <Table 
        stickyHeader={stickyHeader && !isMobile}
        aria-label={ariaLabel}
        size={isMobile ? 'small' : 'medium'}
      >
        <TableHead>
          <TableRow role="row">
            {visibleColumns.map((column, index) => (
              <TableCell
                key={column.id}
                align={column.align}
                style={{ 
                  minWidth: isMobile ? 'auto' : column.minWidth,
                  fontWeight: 600
                }}
                scope="col"
                aria-sort="none"
                role="columnheader"
                tabIndex={0}
                aria-colindex={index + 1}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell 
                colSpan={visibleColumns.length} 
                align="center"
                role="cell"
                aria-colspan={visibleColumns.length}
              >
                <Typography 
                  variant="body2" 
                  color="text.secondary"
                  role="status"
                  aria-live="polite"
                >
                  No data available
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row, rowIndex) => (
              <TableRow 
                hover 
                role="row" 
                tabIndex={0}
                key={rowIndex}
                aria-rowindex={rowIndex + 2} // +2 because header is row 1
                sx={{
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover,
                  },
                  '&:focus': {
                    backgroundColor: theme.palette.action.selected,
                    outline: `2px solid ${theme.palette.primary.main}`,
                    outlineOffset: -2,
                  },
                  // Enhanced touch feedback
                  '@media (hover: none)': {
                    '&:active': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  },
                  cursor: 'pointer',
                  // Improve touch target size
                  minHeight: isMobile ? 48 : 'auto',
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    // Handle row selection if needed
                  }
                }}
              >
                {visibleColumns.map((column, colIndex) => {
                  const value = row[column.id];
                  return (
                    <TableCell 
                      key={column.id} 
                      align={column.align}
                      role="cell"
                      aria-colindex={colIndex + 1}
                      sx={{
                        maxWidth: isMobile ? '120px' : 'none',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: isMobile ? 'nowrap' : 'normal',
                        // Improve touch target size
                        minHeight: isMobile ? 48 : 'auto',
                        py: isMobile ? 1.5 : 1,
                      }}
                    >
                      <span aria-label={`${column.label}: ${column.format ? column.format(value) : value}`}>
                        {column.format ? column.format(value) : value}
                      </span>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ResponsiveTable;