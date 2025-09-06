import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  LinearProgress,
  Chip,
  Alert,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Api as ApiIcon,
  Storage as CacheIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { PerformanceMetrics } from '../../types';

export interface PerformanceMetricsSectionProps {
  metrics: PerformanceMetrics;
  showBottlenecks?: boolean;
  className?: string;
}

interface MetricIndicator {
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
  isPercentage?: boolean;
  isInverted?: boolean; // For metrics where lower is better
}

interface BottleneckAnalysis {
  phase: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  impact: string;
  recommendations: string[];
}

const PerformanceMetricsSection: React.FC<PerformanceMetricsSectionProps> = ({
  metrics,
  showBottlenecks = true,
  className,
}) => {
  const theme = useTheme();

  // Format memory values
  const formatMemory = (mb: number): string => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb.toFixed(1)} MB`;
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Format time for rate limit reset
  const formatRateLimitTime = (remaining: number): string => {
    if (remaining <= 0) return 'Limit reached';
    if (remaining >= 1000) return `${Math.floor(remaining / 1000)}K+ remaining`;
    return `${remaining} remaining`;
  };

  // Determine severity based on value and thresholds
  const getSeverity = (
    value: number, 
    threshold?: { good: number; warning: number },
    isInverted: boolean = false
  ): 'success' | 'warning' | 'error' | 'info' => {
    if (!threshold) return 'info';
    
    if (isInverted) {
      // For metrics where lower is better (like memory usage, response time)
      if (value <= threshold.good) return 'success';
      if (value <= threshold.warning) return 'warning';
      return 'error';
    } else {
      // For metrics where higher is better (like cache hit rate)
      if (value >= threshold.good) return 'success';
      if (value >= threshold.warning) return 'warning';
      return 'error';
    }
  };

  // Create performance indicators
  const performanceIndicators = useMemo((): MetricIndicator[] => [
    {
      label: 'Memory Usage',
      value: metrics.memory_usage_mb,
      displayValue: formatMemory(metrics.memory_usage_mb),
      description: 'Current memory consumption of the scanning process',
      severity: getSeverity(metrics.memory_usage_mb, { good: 512, warning: 1024 }, true),
      icon: <MemoryIcon />,
      threshold: { good: 512, warning: 1024 },
      isInverted: true,
    },
    {
      label: 'API Requests Made',
      value: metrics.api_requests_made,
      displayValue: metrics.api_requests_made.toLocaleString(),
      description: 'Total number of API requests made during the scan',
      severity: 'info',
      icon: <ApiIcon />,
    },
    {
      label: 'Rate Limit Status',
      value: metrics.api_rate_limit_remaining,
      displayValue: formatRateLimitTime(metrics.api_rate_limit_remaining),
      description: 'Remaining API requests before hitting rate limit',
      severity: getSeverity(metrics.api_rate_limit_remaining, { good: 1000, warning: 100 }),
      icon: <SpeedIcon />,
      threshold: { good: 1000, warning: 100 },
    },
    {
      label: 'Cache Hit Rate',
      value: metrics.cache_hit_rate,
      displayValue: `${Math.round(metrics.cache_hit_rate * metrics.api_requests_made)} / ${metrics.api_requests_made} requests (${formatPercentage(metrics.cache_hit_rate)})`,
      description: 'Number of data requests served from cache vs total requests',
      severity: getSeverity(metrics.cache_hit_rate, { good: 0.8, warning: 0.5 }),
      icon: <CacheIcon />,
      threshold: { good: 0.8, warning: 0.5 },
      isPercentage: true,
    },
    {
      label: 'Concurrent Requests',
      value: metrics.concurrent_requests,
      displayValue: metrics.concurrent_requests.toString(),
      description: 'Number of simultaneous API requests being processed',
      severity: getSeverity(metrics.concurrent_requests, { good: 10, warning: 20 }, true),
      icon: <TimelineIcon />,
      threshold: { good: 10, warning: 20 },
      isInverted: true,
    },
  ], [metrics]);

  // Analyze bottlenecks
  const bottleneckAnalysis = useMemo((): BottleneckAnalysis[] => {
    const bottlenecks: BottleneckAnalysis[] = [];
    
    // Memory bottleneck
    if (metrics.memory_usage_mb > 1024) {
      bottlenecks.push({
        phase: 'Memory Usage',
        severity: metrics.memory_usage_mb > 2048 ? 'high' : 'medium',
        description: 'High memory consumption detected',
        impact: 'May cause system slowdown or out-of-memory errors',
        recommendations: [
          'Consider processing symbols in smaller batches',
          'Implement data cleanup after processing',
          'Monitor for memory leaks in data processing',
        ],
      });
    }
    
    // Rate limit bottleneck
    if (metrics.api_rate_limit_remaining < 100) {
      bottlenecks.push({
        phase: 'API Rate Limits',
        severity: metrics.api_rate_limit_remaining < 10 ? 'high' : 'medium',
        description: 'Approaching API rate limits',
        impact: 'Scan performance will be throttled or requests may fail',
        recommendations: [
          'Implement request queuing and throttling',
          'Consider upgrading API plan for higher limits',
          'Optimize data requests to reduce API calls',
        ],
      });
    }
    
    // Cache performance bottleneck
    if (metrics.cache_hit_rate < 0.5) {
      bottlenecks.push({
        phase: 'Cache Performance',
        severity: metrics.cache_hit_rate < 0.2 ? 'high' : 'medium',
        description: 'Low cache hit rate detected',
        impact: 'Increased API usage and slower response times',
        recommendations: [
          'Review cache configuration and TTL settings',
          'Implement more aggressive caching strategies',
          'Pre-warm cache with commonly requested data',
        ],
      });
    }
    
    // Concurrency bottleneck
    if (metrics.concurrent_requests > 20) {
      bottlenecks.push({
        phase: 'Request Concurrency',
        severity: metrics.concurrent_requests > 50 ? 'high' : 'medium',
        description: 'High number of concurrent requests',
        impact: 'May overwhelm API endpoints or cause timeouts',
        recommendations: [
          'Implement connection pooling and request queuing',
          'Reduce concurrent request limits',
          'Add circuit breaker patterns for resilience',
        ],
      });
    }
    
    // Identify the primary bottleneck
    if (metrics.bottleneck_phase) {
      const existingBottleneck = bottlenecks.find(b => 
        b.phase.toLowerCase().includes(metrics.bottleneck_phase!.toLowerCase())
      );
      
      if (!existingBottleneck) {
        bottlenecks.push({
          phase: metrics.bottleneck_phase,
          severity: 'medium',
          description: 'System-identified performance bottleneck',
          impact: 'Primary constraint on scan performance',
          recommendations: [
            'Focus optimization efforts on this component',
            'Monitor this metric closely during peak usage',
          ],
        });
      }
    }
    
    return bottlenecks.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }, [metrics]);

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

  // Render performance indicator
  const renderPerformanceIndicator = (indicator: MetricIndicator) => (
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

        {/* Progress bar for metrics with thresholds */}
        {indicator.threshold && indicator.isPercentage && (
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
          </Box>
        )}

        {/* Status indicator */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {indicator.severity === 'success' && <SuccessIcon sx={{ fontSize: 16, color: 'success.main' }} />}
          {indicator.severity === 'warning' && <WarningIcon sx={{ fontSize: 16, color: 'warning.main' }} />}
          {indicator.severity === 'error' && <ErrorIcon sx={{ fontSize: 16, color: 'error.main' }} />}
          <Typography variant="caption" color={`${indicator.severity}.main`} fontWeight="bold">
            {indicator.severity === 'success' && 'Optimal'}
            {indicator.severity === 'warning' && 'Attention Needed'}
            {indicator.severity === 'error' && 'Critical'}
            {indicator.severity === 'info' && 'Normal'}
          </Typography>
        </Box>
      </Paper>
    </Grid>
  );

  // Render bottleneck analysis
  const renderBottleneckAnalysis = () => {
    if (bottleneckAnalysis.length === 0) {
      return (
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="body2">
            🎉 No performance bottlenecks detected! System is operating efficiently.
          </Typography>
        </Alert>
      );
    }

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon />
          Performance Bottlenecks ({bottleneckAnalysis.length})
        </Typography>
        
        {bottleneckAnalysis.map((bottleneck, index) => {
          const severityColor = bottleneck.severity === 'high' ? 'error' : 
                               bottleneck.severity === 'medium' ? 'warning' : 'info';
          
          return (
            <Paper
              key={index}
              elevation={0}
              sx={{
                p: 2,
                mb: 1,
                border: `1px solid ${theme.palette[severityColor].main}`,
                borderLeft: `4px solid ${theme.palette[severityColor].main}`,
                backgroundColor: theme.palette[severityColor].light + '10',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle1" fontWeight="600" color={`${severityColor}.main`}>
                  {bottleneck.phase}
                </Typography>
                <Chip
                  label={`${bottleneck.severity.toUpperCase()} PRIORITY`}
                  color={severityColor}
                  size="small"
                  variant="filled"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {bottleneck.description}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mb: 1 }}>
                Impact: {bottleneck.impact}
              </Typography>
              
              <Typography variant="subtitle2" color="text.primary" gutterBottom>
                Recommendations:
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {bottleneck.recommendations.map((rec, recIndex) => (
                  <Typography
                    key={recIndex}
                    component="li"
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    {rec}
                  </Typography>
                ))}
              </Box>
            </Paper>
          );
        })}
      </Box>
    );
  };

  // Calculate overall performance score
  const performanceScore = useMemo(() => {
    const scores = performanceIndicators
      .filter(indicator => indicator.threshold)
      .map(indicator => {
        if (!indicator.threshold) return 1;
        
        const { good, warning } = indicator.threshold;
        const value = indicator.value;
        
        if (indicator.isInverted) {
          if (value <= good) return 1;
          if (value <= warning) return 0.7;
          return 0.3;
        } else {
          if (value >= good) return 1;
          if (value >= warning) return 0.7;
          return 0.3;
        }
      });
    
    return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 1;
  }, [performanceIndicators]);

  const performanceGrade = performanceScore >= 0.8 ? 'Excellent' : 
                          performanceScore >= 0.6 ? 'Good' : 
                          performanceScore >= 0.4 ? 'Fair' : 'Poor';
  const performanceColor = performanceScore >= 0.8 ? 'success' : 
                          performanceScore >= 0.6 ? 'info' : 
                          performanceScore >= 0.4 ? 'warning' : 'error';

  return (
    <Box className={className} role="region" aria-label="Performance metrics">
      {/* Performance Summary */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: theme.palette.grey[50], borderRadius: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body1" color="text.primary">
            System Performance Overview
          </Typography>
          <Chip
            label={`${performanceGrade} (${(performanceScore * 100).toFixed(0)}%)`}
            color={performanceColor}
            variant="filled"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary">
          {metrics.api_requests_made} API requests processed using {formatMemory(metrics.memory_usage_mb)} memory
        </Typography>
      </Box>

      {/* Performance Indicators Grid */}
      <Grid container spacing={2} sx={{ mb: showBottlenecks ? 3 : 2 }}>
        {performanceIndicators.map(renderPerformanceIndicator)}
      </Grid>

      {/* Bottleneck Analysis */}
      {showBottlenecks && renderBottleneckAnalysis()}

      {/* Performance Insights */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: theme.palette.info.light + '20', borderRadius: 1 }}>
        <Typography variant="subtitle2" color="text.primary" gutterBottom>
          💡 Performance Insights
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {metrics.cache_hit_rate > 0.8 && (
            <Typography component="li" variant="caption" color="success.main">
              Excellent cache performance - {formatPercentage(metrics.cache_hit_rate)} hit rate reducing API load
            </Typography>
          )}
          {metrics.memory_usage_mb < 512 && (
            <Typography component="li" variant="caption" color="success.main">
              Efficient memory usage - system is well-optimized for current workload
            </Typography>
          )}
          {metrics.api_rate_limit_remaining > 1000 && (
            <Typography component="li" variant="caption" color="success.main">
              Healthy API rate limit buffer - no throttling concerns
            </Typography>
          )}
          {bottleneckAnalysis.length === 0 && (
            <Typography component="li" variant="caption" color="success.main">
              No performance bottlenecks detected - system is operating optimally
            </Typography>
          )}
          {performanceScore < 0.6 && (
            <Typography component="li" variant="caption" color="warning.main">
              Multiple performance issues detected - consider system optimization
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default PerformanceMetricsSection;