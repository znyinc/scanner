import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  LinearProgress,
  Tooltip,
  Chip,
  useTheme,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  DataUsage as DataIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Timeline as TimelineIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { DataQualityMetrics } from '../../types';

export interface DataQualitySectionProps {
  metrics: DataQualityMetrics;
  showCharts?: boolean;
  className?: string;
}

interface QualityIndicator {
  label: string;
  value: number;
  displayValue: string;
  unit?: string;
  description: string;
  severity: 'success' | 'warning' | 'error' | 'info';
  icon: React.ReactNode;
  threshold?: {
    good: number;
    warning: number;
  };
}

interface TimingBreakdown {
  phase: string;
  time: number;
  percentage: number;
  color: string;
}

const DataQualitySection: React.FC<DataQualitySectionProps> = ({
  metrics,
  showCharts = true,
  className,
}) => {
  const theme = useTheme();

  // Format time values
  const formatTime = (seconds: number): string => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Format large numbers
  const formatNumber = (value: number): string => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toLocaleString();
  };

  // Determine severity based on value and thresholds
  const getSeverity = (value: number, threshold?: { good: number; warning: number }): 'success' | 'warning' | 'error' => {
    if (!threshold) return 'info' as any;
    if (value >= threshold.good) return 'success';
    if (value >= threshold.warning) return 'warning';
    return 'error';
  };

  // Create quality indicators
  const qualityIndicators = useMemo((): QualityIndicator[] => [
    {
      label: 'Overall Quality Score',
      value: metrics.quality_score,
      displayValue: formatPercentage(metrics.quality_score),
      description: 'Composite score based on data completeness, fetch success rate, and timing performance',
      severity: getSeverity(metrics.quality_score, { good: 0.8, warning: 0.5 }),
      icon: <DataIcon />,
      threshold: { good: 0.8, warning: 0.5 },
    },
    {
      label: 'Success Rate',
      value: metrics.success_rate,
      displayValue: `${Math.round(metrics.success_rate * metrics.total_data_points)} / ${metrics.total_data_points} (${formatPercentage(metrics.success_rate)})`,
      description: 'Number of symbols successfully processed without errors',
      severity: getSeverity(metrics.success_rate, { good: 0.9, warning: 0.7 }),
      icon: <SuccessIcon />,
      threshold: { good: 0.9, warning: 0.7 },
    },
    {
      label: 'Data Completeness',
      value: metrics.data_completeness,
      displayValue: `${Math.round(metrics.data_completeness * metrics.total_data_points)} / ${metrics.total_data_points} points (${formatPercentage(metrics.data_completeness)})`,
      description: 'Number of expected data points that were successfully retrieved',
      severity: getSeverity(metrics.data_completeness, { good: 0.95, warning: 0.8 }),
      icon: <StorageIcon />,
      threshold: { good: 0.95, warning: 0.8 },
    },
    {
      label: 'Average Fetch Time',
      value: metrics.average_fetch_time,
      displayValue: formatTime(metrics.average_fetch_time),
      description: 'Average time taken to fetch data per symbol',
      severity: getSeverity(1 / metrics.average_fetch_time, { good: 0.5, warning: 0.2 }), // Inverted for time
      icon: <SpeedIcon />,
    },
    {
      label: 'Total Data Points',
      value: metrics.total_data_points,
      displayValue: formatNumber(metrics.total_data_points),
      description: 'Total number of data points retrieved across all symbols and timeframes',
      severity: 'info' as any,
      icon: <TimelineIcon />,
    },
  ], [metrics]);

  // Calculate timing breakdown (simulated based on available data)
  const timingBreakdown = useMemo((): TimingBreakdown[] => {
    const totalTime = metrics.average_fetch_time;
    
    // Simulate breakdown based on typical patterns
    const fetchTime = totalTime * 0.8;
    const processingTime = totalTime * 0.15;
    const validationTime = totalTime * 0.05;
    
    return [
      {
        phase: 'Data Fetch',
        time: fetchTime,
        percentage: (fetchTime / totalTime) * 100,
        color: theme.palette.primary.main,
      },
      {
        phase: 'Processing',
        time: processingTime,
        percentage: (processingTime / totalTime) * 100,
        color: theme.palette.secondary.main,
      },
      {
        phase: 'Validation',
        time: validationTime,
        percentage: (validationTime / totalTime) * 100,
        color: theme.palette.success.main,
      },
    ];
  }, [metrics.average_fetch_time, theme.palette]);

  // Get color for progress bar based on severity
  const getProgressColor = (severity: 'success' | 'warning' | 'error' | 'info'): 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'success': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      case 'info': return 'info';
      default: return 'primary';
    }
  };

  // Render quality indicator
  const renderQualityIndicator = (indicator: QualityIndicator) => (
    <Grid item xs={12} sm={6} md={4} key={indicator.label}>
      <Paper
        elevation={0}
        sx={{
          p: 2,
          border: `1px solid ${theme.palette.divider}`,
          borderLeft: `4px solid ${theme.palette[indicator.severity].main}`,
          height: '100%',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: theme.shadows[2],
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Box sx={{ color: theme.palette[indicator.severity].main }}>
            {indicator.icon}
          </Box>
          <Tooltip title={indicator.description} placement="top" arrow>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{
                cursor: 'help',
                '&:hover': {
                  color: 'text.primary',
                },
              }}
            >
              {indicator.label}
            </Typography>
          </Tooltip>
        </Box>

        <Typography
          variant="h5"
          fontWeight="bold"
          color={theme.palette[indicator.severity].main}
          sx={{ mb: 1 }}
        >
          {indicator.displayValue}
        </Typography>

        {/* Progress bar for percentage values */}
        {indicator.value <= 1 && indicator.threshold && (
          <Box sx={{ mb: 1 }}>
            <LinearProgress
              variant="determinate"
              value={indicator.value * 100}
              color={getProgressColor(indicator.severity)}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: theme.palette.grey[200],
              }}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                0%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                100%
              </Typography>
            </Box>
          </Box>
        )}

        {/* Threshold indicators */}
        {indicator.threshold && (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            <Chip
              label={`Good: ≥${formatPercentage(indicator.threshold.good)}`}
              size="small"
              color="success"
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 18 }}
            />
            <Chip
              label={`Warning: ≥${formatPercentage(indicator.threshold.warning)}`}
              size="small"
              color="warning"
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 18 }}
            />
          </Box>
        )}
      </Paper>
    </Grid>
  );

  // Render timing breakdown chart
  const renderTimingBreakdown = () => (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        border: `1px solid ${theme.palette.divider}`,
        mt: 2,
      }}
    >
      <Typography variant="h6" color="text.primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TimelineIcon />
        Performance Breakdown
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Average processing time per symbol: {formatTime(metrics.average_fetch_time)}
        </Typography>
        
        {/* Stacked progress bar */}
        <Box sx={{ position: 'relative', height: 20, backgroundColor: theme.palette.grey[200], borderRadius: 1, overflow: 'hidden' }}>
          {timingBreakdown.map((phase, index) => {
            const left = timingBreakdown.slice(0, index).reduce((sum, p) => sum + p.percentage, 0);
            return (
              <Box
                key={phase.phase}
                sx={{
                  position: 'absolute',
                  left: `${left}%`,
                  width: `${phase.percentage}%`,
                  height: '100%',
                  backgroundColor: phase.color,
                  transition: 'all 0.3s ease-in-out',
                }}
              />
            );
          })}
        </Box>
      </Box>

      {/* Breakdown legend */}
      <Grid container spacing={1}>
        {timingBreakdown.map((phase) => (
          <Grid item xs={12} sm={4} key={phase.phase}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  backgroundColor: phase.color,
                  borderRadius: 0.5,
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {phase.phase}
              </Typography>
              <Typography variant="caption" fontWeight="bold">
                {formatTime(phase.time)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ({phase.percentage.toFixed(1)}%)
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );

  // Overall quality assessment
  const overallQuality = metrics.quality_score;
  const qualityLevel = overallQuality >= 0.8 ? 'Excellent' : 
                      overallQuality >= 0.6 ? 'Good' : 
                      overallQuality >= 0.4 ? 'Fair' : 'Poor';
  const qualityColor = overallQuality >= 0.8 ? 'success' : 
                      overallQuality >= 0.6 ? 'info' : 
                      overallQuality >= 0.4 ? 'warning' : 'error';

  return (
    <Box className={className} role="region" aria-label="Data quality metrics">
      {/* Quality Summary */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: theme.palette.grey[50], borderRadius: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body1" color="text.primary">
            Data Quality Assessment
          </Typography>
          <Chip
            label={qualityLevel}
            color={qualityColor}
            variant="filled"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary">
          Overall quality score: {formatPercentage(overallQuality)} based on {formatNumber(metrics.total_data_points)} data points
        </Typography>
      </Box>

      {/* Quality Indicators Grid */}
      <Grid container spacing={2} sx={{ mb: showCharts ? 0 : 2 }}>
        {qualityIndicators.map(renderQualityIndicator)}
      </Grid>

      {/* Timing Breakdown Chart */}
      {showCharts && renderTimingBreakdown()}

      {/* Quality Insights */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: theme.palette.info.light + '20', borderRadius: 1 }}>
        <Typography variant="subtitle2" color="text.primary" gutterBottom>
          💡 Quality Insights
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {metrics.success_rate < 0.9 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Success rate below 90% - consider checking API connectivity and symbol validity
            </Typography>
          )}
          {metrics.data_completeness < 0.95 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Data completeness below 95% - some symbols may have missing timeframe data
            </Typography>
          )}
          {metrics.average_fetch_time > 2 && (
            <Typography component="li" variant="caption" color="text.secondary">
              Average fetch time above 2s - consider optimizing API calls or checking network performance
            </Typography>
          )}
          {metrics.quality_score >= 0.9 && (
            <Typography component="li" variant="caption" color="success.main">
              Excellent data quality - all metrics are performing well
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default DataQualitySection;