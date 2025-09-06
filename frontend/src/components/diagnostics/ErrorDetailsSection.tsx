import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Paper,
  Alert,
  Button,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  BugReport as BugIcon,
  NetworkCheck as NetworkIcon,
  Schedule as ScheduleIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import SymbolBadge from '../SymbolBadge';

export interface ErrorDetailsSectionProps {
  symbolsWithErrors: Record<string, string>;
  errorSummary?: Record<string, number>;
  onRetrySymbol?: (symbol: string) => void;
  onRetryErrorType?: (errorType: string) => void;
  className?: string;
}

interface ErrorGroup {
  type: string;
  category: string;
  symbols: string[];
  count: number;
  severity: 'error' | 'warning' | 'info';
  icon: React.ReactNode;
  description: string;
  remediation: string[];
  isRecoverable: boolean;
}

interface ErrorPattern {
  pattern: RegExp;
  category: string;
  severity: 'error' | 'warning' | 'info';
  icon: React.ReactNode;
  description: string;
  remediation: string[];
  isRecoverable: boolean;
}

const ErrorDetailsSection: React.FC<ErrorDetailsSectionProps> = ({
  symbolsWithErrors,
  errorSummary,
  onRetrySymbol,
  onRetryErrorType,
  className,
}) => {
  const theme = useTheme();
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Define error patterns for categorization
  const errorPatterns: ErrorPattern[] = [
    {
      pattern: /timeout|timed out|connection timeout/i,
      category: 'API Timeouts',
      severity: 'warning',
      icon: <ScheduleIcon />,
      description: 'Requests exceeded the allowed time limit',
      remediation: [
        'Retry the request during off-peak hours',
        'Check network connectivity',
        'Consider increasing timeout settings',
      ],
      isRecoverable: true,
    },
    {
      pattern: /no.*data|insufficient.*data|not enough.*data/i,
      category: 'Insufficient Data',
      severity: 'warning',
      icon: <InfoIcon />,
      description: 'Symbol has insufficient historical data for analysis',
      remediation: [
        'Check if symbol is newly listed',
        'Verify symbol is actively traded',
        'Try with a shorter analysis period',
      ],
      isRecoverable: false,
    },
    {
      pattern: /invalid.*ticker|ticker.*not.*found|symbol.*not.*found/i,
      category: 'Invalid Tickers',
      severity: 'error',
      icon: <ErrorIcon />,
      description: 'Symbol ticker is invalid or not recognized',
      remediation: [
        'Verify the ticker symbol is correct',
        'Check if symbol has been delisted',
        'Use the correct exchange suffix if needed',
      ],
      isRecoverable: false,
    },
    {
      pattern: /market.*closed|outside.*trading.*hours/i,
      category: 'Market Closed',
      severity: 'info',
      icon: <ScheduleIcon />,
      description: 'Market is currently closed for trading',
      remediation: [
        'Retry during market hours',
        'Use pre-market or after-hours data if available',
      ],
      isRecoverable: true,
    },
    {
      pattern: /rate.*limit|too.*many.*requests|quota.*exceeded/i,
      category: 'Rate Limits',
      severity: 'warning',
      icon: <SecurityIcon />,
      description: 'API rate limit has been exceeded',
      remediation: [
        'Wait for rate limit reset',
        'Reduce request frequency',
        'Consider upgrading API plan',
      ],
      isRecoverable: true,
    },
    {
      pattern: /network.*error|connection.*error|dns.*error/i,
      category: 'Network Issues',
      severity: 'error',
      icon: <NetworkIcon />,
      description: 'Network connectivity problems',
      remediation: [
        'Check internet connection',
        'Verify API endpoint is accessible',
        'Check firewall settings',
      ],
      isRecoverable: true,
    },
    {
      pattern: /server.*error|internal.*error|500|502|503/i,
      category: 'Server Errors',
      severity: 'error',
      icon: <BugIcon />,
      description: 'Server-side errors from the data provider',
      remediation: [
        'Retry the request later',
        'Check data provider status page',
        'Contact support if persistent',
      ],
      isRecoverable: true,
    },
  ];

  // Categorize errors into groups
  const errorGroups = useMemo((): ErrorGroup[] => {
    const groups = new Map<string, ErrorGroup>();
    
    Object.entries(symbolsWithErrors).forEach(([symbol, errorMessage]) => {
      // Find matching pattern
      const matchedPattern = errorPatterns.find(pattern => 
        pattern.pattern.test(errorMessage)
      );
      
      const category = matchedPattern?.category || 'Other Errors';
      
      if (!groups.has(category)) {
        groups.set(category, {
          type: category,
          category,
          symbols: [],
          count: 0,
          severity: matchedPattern?.severity || 'error',
          icon: matchedPattern?.icon || <ErrorIcon />,
          description: matchedPattern?.description || 'Unclassified error',
          remediation: matchedPattern?.remediation || ['Contact support for assistance'],
          isRecoverable: matchedPattern?.isRecoverable || false,
        });
      }
      
      const group = groups.get(category)!;
      group.symbols.push(symbol);
      group.count++;
    });
    
    // Sort groups by severity and count
    return Array.from(groups.values()).sort((a, b) => {
      const severityOrder = { error: 3, warning: 2, info: 1 };
      const severityDiff = severityOrder[b.severity] - severityOrder[a.severity];
      if (severityDiff !== 0) return severityDiff;
      return b.count - a.count;
    });
  }, [symbolsWithErrors]);

  // Toggle group expansion
  const toggleGroup = (groupType: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupType)) {
        newSet.delete(groupType);
      } else {
        newSet.add(groupType);
      }
      return newSet;
    });
  };

  // Handle retry for entire error group
  const handleRetryGroup = (group: ErrorGroup) => {
    if (onRetryErrorType) {
      onRetryErrorType(group.type);
    }
  };

  // Get severity color
  const getSeverityColor = (severity: 'error' | 'warning' | 'info') => {
    switch (severity) {
      case 'error': return theme.palette.error.main;
      case 'warning': return theme.palette.warning.main;
      case 'info': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  };

  // Render error group
  const renderErrorGroup = (group: ErrorGroup) => {
    const isExpanded = expandedGroups.has(group.type);
    
    return (
      <Accordion
        key={group.type}
        expanded={isExpanded}
        onChange={() => toggleGroup(group.type)}
        sx={{
          border: `1px solid ${getSeverityColor(group.severity)}`,
          borderLeft: `4px solid ${getSeverityColor(group.severity)}`,
          '&:before': { display: 'none' },
          mb: 1,
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: getSeverityColor(group.severity) + '10',
            '&:hover': {
              backgroundColor: getSeverityColor(group.severity) + '20',
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
            <Box sx={{ color: getSeverityColor(group.severity) }}>
              {group.icon}
            </Box>
            
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight="600">
                {group.category}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {group.description}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={`${group.count} symbol${group.count !== 1 ? 's' : ''}`}
                color={group.severity}
                size="small"
                variant="outlined"
              />
              
              {group.isRecoverable && (
                <Chip
                  label="Recoverable"
                  color="success"
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </AccordionSummary>
        
        <AccordionDetails>
          <Grid container spacing={2}>
            {/* Affected Symbols */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Affected Symbols ({group.count})
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {group.symbols.map(symbol => (
                  <SymbolBadge
                    key={symbol}
                    symbol={symbol}
                    status="error"
                    onClick={onRetrySymbol ? () => onRetrySymbol(symbol) : undefined}
                    size="small"
                  />
                ))}
              </Box>
            </Grid>
            
            {/* Error Messages Sample */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Sample Error Messages
              </Typography>
              <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                {group.symbols.slice(0, 3).map(symbol => (
                  <Paper
                    key={symbol}
                    elevation={0}
                    sx={{
                      p: 1,
                      mb: 1,
                      backgroundColor: theme.palette.grey[50],
                      border: `1px solid ${theme.palette.grey[200]}`,
                    }}
                  >
                    <Typography variant="caption" fontWeight="bold" color="text.primary">
                      {symbol}:
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ ml: 1, fontFamily: 'monospace' }}
                    >
                      {symbolsWithErrors[symbol]}
                    </Typography>
                  </Paper>
                ))}
                {group.symbols.length > 3 && (
                  <Typography variant="caption" color="text.secondary">
                    ... and {group.symbols.length - 3} more
                  </Typography>
                )}
              </Box>
            </Grid>
            
            {/* Remediation Steps */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Recommended Actions
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {group.remediation.map((step, index) => (
                  <Typography
                    key={index}
                    component="li"
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    {step}
                  </Typography>
                ))}
              </Box>
            </Grid>
            
            {/* Action Buttons */}
            {(group.isRecoverable && (onRetrySymbol || onRetryErrorType)) && (
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 1, pt: 1, borderTop: `1px solid ${theme.palette.divider}` }}>
                  {onRetryErrorType && (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={() => handleRetryGroup(group)}
                      color={group.severity}
                    >
                      Retry All {group.count} Symbols
                    </Button>
                  )}
                </Box>
              </Grid>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  // Calculate error statistics
  const totalErrors = Object.keys(symbolsWithErrors).length;
  const recoverableErrors = errorGroups.filter(g => g.isRecoverable).reduce((sum, g) => sum + g.count, 0);
  const criticalErrors = errorGroups.filter(g => g.severity === 'error').reduce((sum, g) => sum + g.count, 0);

  if (totalErrors === 0) {
    return (
      <Box className={className} role="region" aria-label="Error details">
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="body2">
            🎉 No errors detected! All symbols were processed successfully.
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box className={className} role="region" aria-label="Error details">
      {/* Error Summary */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: theme.palette.grey[50], borderRadius: 1 }}>
        <Typography variant="body1" color="text.primary" gutterBottom>
          Error Analysis Summary
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {totalErrors}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Errors
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {recoverableErrors}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Recoverable
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {criticalErrors}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Critical
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Error Groups */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" color="text.primary" gutterBottom>
          Error Categories ({errorGroups.length})
        </Typography>
        {errorGroups.map(renderErrorGroup)}
      </Box>

      {/* Recovery Actions */}
      {recoverableErrors > 0 && (onRetrySymbol || onRetryErrorType) && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            💡 {recoverableErrors} error{recoverableErrors !== 1 ? 's' : ''} may be recoverable through retry.
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Click on individual symbols or use the "Retry All" buttons to attempt recovery.
          </Typography>
        </Alert>
      )}

      {/* Error Frequency Patterns */}
      {errorSummary && Object.keys(errorSummary).length > 0 && (
        <Box sx={{ mt: 3, p: 2, backgroundColor: theme.palette.info.light + '20', borderRadius: 1 }}>
          <Typography variant="subtitle2" color="text.primary" gutterBottom>
            📊 Error Frequency Patterns
          </Typography>
          <Grid container spacing={1}>
            {Object.entries(errorSummary).map(([errorType, count]) => (
              <Grid item key={errorType} xs="auto">
                <Chip
                  label={`${errorType}: ${count}`}
                  size="small"
                  variant="outlined"
                  color="info"
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default ErrorDetailsSection;