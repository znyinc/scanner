import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon,
  FilterList as FilterIcon,
  CheckCircle as SuccessIcon,
  Cancel as RejectIcon,
} from '@mui/icons-material';
import { SignalAnalysis } from '../../types';
import SymbolBadge from '../SymbolBadge';

export interface SignalAnalysisSectionProps {
  analysis: SignalAnalysis;
  showDistributions?: boolean;
  className?: string;
}

interface RejectionCategory {
  reason: string;
  symbols: string[];
  count: number;
  description: string;
  icon: React.ReactNode;
  color: string;
}

interface ConfidenceLevel {
  range: string;
  count: number;
  percentage: number;
  color: string;
}

const SignalAnalysisSection: React.FC<SignalAnalysisSectionProps> = ({
  analysis,
  showDistributions = true,
  className,
}) => {
  const theme = useTheme();

  // Process rejection reasons into categories
  const rejectionCategories = useMemo((): RejectionCategory[] => {
    const categories: RejectionCategory[] = [];
    
    Object.entries(analysis.rejection_reasons).forEach(([reason, symbols]) => {
      let description = '';
      let icon = <RejectIcon />;
      let color = theme.palette.error.main;
      
      // Categorize rejection reasons
      if (reason.toLowerCase().includes('fomo')) {
        description = 'Price moved too far too fast, indicating potential overextension';
        icon = <FilterIcon />;
        color = theme.palette.warning.main;
      } else if (reason.toLowerCase().includes('ema')) {
        description = 'Exponential Moving Averages not in required trending configuration';
        icon = <TrendingUpIcon />;
        color = theme.palette.info.main;
      } else if (reason.toLowerCase().includes('htf') || reason.toLowerCase().includes('timeframe')) {
        description = 'Higher timeframe trend not aligned with signal direction';
        icon = <AnalyticsIcon />;
        color = theme.palette.secondary.main;
      } else if (reason.toLowerCase().includes('volatility')) {
        description = 'Volatility outside acceptable parameters for signal generation';
        icon = <FilterIcon />;
        color = theme.palette.warning.main;
      } else if (reason.toLowerCase().includes('data')) {
        description = 'Insufficient or poor quality data for reliable analysis';
        icon = <RejectIcon />;
        color = theme.palette.error.main;
      }
      
      categories.push({
        reason,
        symbols,
        count: symbols.length,
        description,
        icon,
        color,
      });
    });
    
    // Sort by count (most common first)
    return categories.sort((a, b) => b.count - a.count);
  }, [analysis.rejection_reasons, theme.palette]);

  // Process confidence distribution
  const confidenceLevels = useMemo((): ConfidenceLevel[] => {
    const levels: ConfidenceLevel[] = [];
    const totalSignals = analysis.signals_found;
    
    if (totalSignals === 0) return levels;
    
    Object.entries(analysis.confidence_distribution).forEach(([range, count]) => {
      const percentage = (count / totalSignals) * 100;
      let color = theme.palette.grey[500];
      
      // Assign colors based on confidence level
      if (range.includes('90-100') || range.includes('High')) {
        color = theme.palette.success.main;
      } else if (range.includes('70-89') || range.includes('Medium')) {
        color = theme.palette.info.main;
      } else if (range.includes('50-69') || range.includes('Low')) {
        color = theme.palette.warning.main;
      } else {
        color = theme.palette.error.main;
      }
      
      levels.push({
        range,
        count,
        percentage,
        color,
      });
    });
    
    // Sort by range (highest confidence first)
    return levels.sort((a, b) => {
      const aNum = parseInt(a.range.split('-')[0]) || 0;
      const bNum = parseInt(b.range.split('-')[0]) || 0;
      return bNum - aNum;
    });
  }, [analysis.confidence_distribution, analysis.signals_found, theme.palette]);

  // Calculate summary statistics
  const totalSymbolsAnalyzed = Object.values(analysis.rejection_reasons).flat().length + 
                              Object.values(analysis.symbols_meeting_partial_criteria).flat().length +
                              analysis.signals_found;
  
  const signalRate = totalSymbolsAnalyzed > 0 ? (analysis.signals_found / totalSymbolsAnalyzed) * 100 : 0;
  const partialCriteriaCount = Object.values(analysis.symbols_meeting_partial_criteria).flat().length;

  // Render signal statistics
  const renderSignalStats = () => (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={3}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            border: `1px solid ${theme.palette.success.main}`,
            borderLeft: `4px solid ${theme.palette.success.main}`,
          }}
        >
          <SuccessIcon sx={{ color: theme.palette.success.main, fontSize: 32, mb: 1 }} />
          <Typography variant="h4" color="success.main" fontWeight="bold">
            {analysis.signals_found}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Signals Generated
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12} sm={3}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            border: `1px solid ${theme.palette.info.main}`,
            borderLeft: `4px solid ${theme.palette.info.main}`,
          }}
        >
          <AnalyticsIcon sx={{ color: theme.palette.info.main, fontSize: 32, mb: 1 }} />
          <Typography variant="h4" color="info.main" fontWeight="bold">
            {signalRate.toFixed(1)}%
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Signal Rate
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12} sm={3}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            border: `1px solid ${theme.palette.warning.main}`,
            borderLeft: `4px solid ${theme.palette.warning.main}`,
          }}
        >
          <FilterIcon sx={{ color: theme.palette.warning.main, fontSize: 32, mb: 1 }} />
          <Typography variant="h4" color="warning.main" fontWeight="bold">
            {partialCriteriaCount}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Partial Matches
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12} sm={3}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            border: `1px solid ${theme.palette.error.main}`,
            borderLeft: `4px solid ${theme.palette.error.main}`,
          }}
        >
          <RejectIcon sx={{ color: theme.palette.error.main, fontSize: 32, mb: 1 }} />
          <Typography variant="h4" color="error.main" fontWeight="bold">
            {rejectionCategories.reduce((sum, cat) => sum + cat.count, 0)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Rejections
          </Typography>
        </Paper>
      </Grid>
    </Grid>
  );

  // Render confidence distribution
  const renderConfidenceDistribution = () => {
    if (confidenceLevels.length === 0) return null;
    
    return (
      <Paper elevation={0} sx={{ p: 2, border: `1px solid ${theme.palette.divider}`, mb: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalyticsIcon />
          Signal Confidence Distribution
        </Typography>
        
        <Grid container spacing={2}>
          {confidenceLevels.map((level) => (
            <Grid item xs={12} sm={6} md={3} key={level.range}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    {level.range}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {level.count} signals ({level.percentage.toFixed(1)}%)
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={level.percentage}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: theme.palette.grey[200],
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: level.color,
                    },
                  }}
                />
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>
    );
  };

  // Render rejection reasons
  const renderRejectionReasons = () => {
    if (rejectionCategories.length === 0) return null;
    
    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RejectIcon />
          Rejection Analysis
        </Typography>
        
        {rejectionCategories.map((category) => (
          <Accordion key={category.reason} sx={{ mb: 1 }}>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              sx={{
                backgroundColor: category.color + '10',
                '&:hover': {
                  backgroundColor: category.color + '20',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Box sx={{ color: category.color }}>
                  {category.icon}
                </Box>
                
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" fontWeight="600">
                    {category.reason}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {category.description}
                  </Typography>
                </Box>
                
                <Chip
                  label={`${category.count} symbol${category.count !== 1 ? 's' : ''}`}
                  size="small"
                  sx={{
                    backgroundColor: category.color + '20',
                    color: category.color,
                    fontWeight: 'bold',
                  }}
                />
              </Box>
            </AccordionSummary>
            
            <AccordionDetails>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Affected Symbols ({category.count})
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {category.symbols.map(symbol => (
                  <SymbolBadge
                    key={symbol}
                    symbol={symbol}
                    status="warning"
                    size="small"
                  />
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  // Render partial criteria matches
  const renderPartialCriteria = () => {
    const partialEntries = Object.entries(analysis.symbols_meeting_partial_criteria);
    if (partialEntries.length === 0) return null;
    
    return (
      <Paper elevation={0} sx={{ p: 2, border: `1px solid ${theme.palette.divider}` }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterIcon />
          Partial Criteria Matches
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Symbols that met some but not all signal criteria
        </Typography>
        
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Criteria Met</TableCell>
                <TableCell align="right">Count</TableCell>
                <TableCell>Symbols</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {partialEntries.map(([criteria, symbols]) => (
                <TableRow key={criteria}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="500">
                      {criteria}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={symbols.length}
                      size="small"
                      color="info"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {symbols.slice(0, 5).map(symbol => (
                        <SymbolBadge
                          key={symbol}
                          symbol={symbol}
                          status="warning"
                          size="small"
                        />
                      ))}
                      {symbols.length > 5 && (
                        <Chip
                          label={`+${symbols.length - 5} more`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  };

  return (
    <Box className={className} role="region" aria-label="Signal analysis results">
      {/* Summary Header */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: theme.palette.grey[50], borderRadius: 1 }}>
        <Typography variant="body1" color="text.primary" gutterBottom>
          Signal Generation Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {analysis.signals_found > 0 ? (
            <>
              Generated {analysis.signals_found} signal{analysis.signals_found !== 1 ? 's' : ''} from {totalSymbolsAnalyzed} symbols analyzed
            </>
          ) : (
            <>
              No signals generated from {totalSymbolsAnalyzed} symbols analyzed
            </>
          )}
        </Typography>
      </Box>

      {/* Signal Statistics */}
      {renderSignalStats()}

      {/* Confidence Distribution */}
      {showDistributions && analysis.signals_found > 0 && renderConfidenceDistribution()}

      {/* Rejection Reasons */}
      {renderRejectionReasons()}

      {/* Partial Criteria Matches */}
      {renderPartialCriteria()}

      {/* Analysis Insights */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: theme.palette.info.light + '20', borderRadius: 1 }}>
        <Typography variant="subtitle2" color="text.primary" gutterBottom>
          💡 Analysis Insights
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {analysis.signals_found === 0 && (
            <Typography component="li" variant="caption" color="text.secondary">
              No signals generated - consider reviewing algorithm parameters or market conditions
            </Typography>
          )}
          {signalRate < 5 && totalSymbolsAnalyzed > 10 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Low signal rate ({signalRate.toFixed(1)}%) - algorithm may be too restrictive for current market conditions
            </Typography>
          )}
          {partialCriteriaCount > analysis.signals_found * 2 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Many symbols meeting partial criteria - consider adjusting filter thresholds
            </Typography>
          )}
          {rejectionCategories.length > 0 && rejectionCategories[0].count > totalSymbolsAnalyzed * 0.5 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Most rejections due to "{rejectionCategories[0].reason}" - focus optimization efforts here
            </Typography>
          )}
          {analysis.signals_found > 0 && confidenceLevels.length > 0 && (
            <Typography component="li" variant="caption" color="success.main">
              Signal generation is working - review confidence distribution for quality assessment
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default SignalAnalysisSection;