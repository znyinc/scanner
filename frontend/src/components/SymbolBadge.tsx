import React, { useState } from 'react';
import {
  Chip,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { SymbolDiagnostic } from '../types';

export type SymbolStatus = 'success' | 'warning' | 'error' | 'no-data';

export interface SymbolBadgeProps {
  symbol: string;
  status: SymbolStatus;
  onClick?: () => void;
  showDetails?: boolean;
  diagnostic?: SymbolDiagnostic;
  size?: 'small' | 'medium';
  variant?: 'filled' | 'outlined';
  disabled?: boolean;
  className?: string;
}

const SymbolBadge: React.FC<SymbolBadgeProps> = ({
  symbol,
  status,
  onClick,
  showDetails = false,
  diagnostic,
  size = 'small',
  variant = 'filled',
  disabled = false,
  className,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Get status configuration
  const getStatusConfig = (status: SymbolStatus) => {
    switch (status) {
      case 'success':
        return {
          color: theme.palette.success.main,
          backgroundColor: theme.palette.success.light,
          icon: <SuccessIcon sx={{ fontSize: 16 }} />,
          label: 'Success',
          description: 'Data retrieved successfully',
        };
      case 'warning':
        return {
          color: theme.palette.warning.main,
          backgroundColor: theme.palette.warning.light,
          icon: <WarningIcon sx={{ fontSize: 16 }} />,
          label: 'Warning',
          description: 'Partial data or minor issues',
        };
      case 'error':
        return {
          color: theme.palette.error.main,
          backgroundColor: theme.palette.error.light,
          icon: <ErrorIcon sx={{ fontSize: 16 }} />,
          label: 'Error',
          description: 'Failed to retrieve data',
        };
      case 'no-data':
      default:
        return {
          color: theme.palette.grey[600],
          backgroundColor: theme.palette.grey[200],
          icon: <InfoIcon sx={{ fontSize: 16 }} />,
          label: 'No Data',
          description: 'No data available',
        };
    }
  };

  const statusConfig = getStatusConfig(status);

  // Handle badge click
  const handleBadgeClick = () => {
    if (disabled) return;
    
    if (showDetails && diagnostic) {
      setDetailsOpen(true);
    } else if (onClick) {
      onClick();
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleBadgeClick();
    }
  };

  // Format timing values
  const formatTime = (time: number): string => {
    return `${time.toFixed(3)}s`;
  };

  // Get tooltip content
  const getTooltipContent = () => {
    if (!diagnostic) {
      return `${symbol}: ${statusConfig.description}`;
    }

    const lines = [
      `Symbol: ${symbol}`,
      `Status: ${statusConfig.label}`,
    ];

    if (diagnostic.error_message) {
      lines.push(`Error: ${diagnostic.error_message}`);
    } else {
      lines.push(`1m Data: ${diagnostic.data_points_1m} points`);
      lines.push(`15m Data: ${diagnostic.data_points_15m} points`);
      lines.push(`Fetch Time: ${formatTime(diagnostic.fetch_time)}`);
    }

    return lines.join('\n');
  };

  // Determine chip color based on status
  const getChipColor = () => {
    switch (status) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'no-data':
      default:
        return 'default';
    }
  };

  const chipElement = (
    <Chip
      label={symbol}
      size={size}
      variant={variant}
      color={getChipColor()}
      icon={statusConfig.icon}
      onClick={handleBadgeClick}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      className={className}
      sx={{
        cursor: disabled ? 'default' : 'pointer',
        '&:hover': {
          backgroundColor: disabled ? undefined : statusConfig.backgroundColor,
        },
        '&:focus': {
          outline: `2px solid ${statusConfig.color}`,
          outlineOffset: 2,
        },
        transition: 'background-color 0.2s ease-in-out',
      }}
      aria-label={`${symbol} - ${statusConfig.label}${diagnostic?.error_message ? `: ${diagnostic.error_message}` : ''}`}
      role={onClick || showDetails ? 'button' : undefined}
      tabIndex={disabled ? -1 : 0}
    />
  );

  return (
    <>
      {showDetails && diagnostic ? (
        <Tooltip
          title={getTooltipContent()}
          placement="top"
          arrow
          enterDelay={500}
          leaveDelay={200}
        >
          {chipElement}
        </Tooltip>
      ) : (
        <Tooltip
          title={`${symbol}: ${statusConfig.description}`}
          placement="top"
          arrow
          enterDelay={500}
          leaveDelay={200}
        >
          {chipElement}
        </Tooltip>
      )}

      {/* Details Dialog */}
      {showDetails && diagnostic && (
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="sm"
          fullWidth
          fullScreen={isMobile}
          aria-labelledby="symbol-details-title"
          aria-describedby="symbol-details-description"
        >
          <DialogTitle id="symbol-details-title">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {statusConfig.icon}
              <Typography variant="h6" component="span">
                {symbol} Details
              </Typography>
            </Box>
          </DialogTitle>
          
          <DialogContent id="symbol-details-description">
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  label={statusConfig.label}
                  color={getChipColor()}
                  size="small"
                  icon={statusConfig.icon}
                />
              </Grid>

              {diagnostic.error_message ? (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Error Message
                  </Typography>
                  <Typography
                    variant="body2"
                    color="error.main"
                    sx={{
                      p: 1,
                      backgroundColor: 'error.light',
                      borderRadius: 1,
                      fontFamily: 'monospace',
                    }}
                  >
                    {diagnostic.error_message}
                  </Typography>
                </Grid>
              ) : (
                <>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      1-Minute Data Points
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {diagnostic.data_points_1m.toLocaleString()}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      15-Minute Data Points
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {diagnostic.data_points_15m.toLocaleString()}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Fetch Time
                    </Typography>
                    <Typography variant="body2">
                      {formatTime(diagnostic.fetch_time)}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Processing Time
                    </Typography>
                    <Typography variant="body2">
                      {formatTime(diagnostic.processing_time)}
                    </Typography>
                  </Grid>

                  {Object.keys(diagnostic.timeframe_coverage).length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Timeframe Coverage
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {Object.entries(diagnostic.timeframe_coverage).map(([timeframe, available]) => (
                          <Chip
                            key={timeframe}
                            label={timeframe}
                            size="small"
                            color={available ? 'success' : 'error'}
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Grid>
                  )}
                </>
              )}
            </Grid>
          </DialogContent>

          <DialogActions>
            <Button
              onClick={() => setDetailsOpen(false)}
              color="primary"
              autoFocus
            >
              Close
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </>
  );
};

export default SymbolBadge;