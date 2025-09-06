import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Chip,
  Tooltip,
  Paper,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { AlgorithmSettings } from '../../types';

export interface ScanSettingsSectionProps {
  settings: AlgorithmSettings;
  defaultSettings?: AlgorithmSettings;
  showDifferences?: boolean;
  className?: string;
}

interface SettingGroup {
  title: string;
  icon: React.ReactNode;
  settings: SettingItem[];
}

interface SettingItem {
  key: keyof AlgorithmSettings;
  label: string;
  value: any;
  unit?: string;
  description: string;
  isModified?: boolean;
  formatValue?: (value: any) => string;
}

const ScanSettingsSection: React.FC<ScanSettingsSectionProps> = ({
  settings,
  defaultSettings,
  showDifferences = true,
  className,
}) => {
  const theme = useTheme();

  // Default algorithm settings for comparison
  const defaultAlgorithmSettings: AlgorithmSettings = {
    atr_multiplier: 2.0,
    ema5_rising_threshold: 0.1,
    ema8_rising_threshold: 0.1,
    ema21_rising_threshold: 0.1,
    volatility_filter: 0.02,
    fomo_filter: 0.05,
    higher_timeframe: '15m',
  };

  const compareSettings = defaultSettings || defaultAlgorithmSettings;

  // Format percentage values with raw value
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(4)} (${(value * 100).toFixed(1)}%)`;
  };

  // Format multiplier values
  const formatMultiplier = (value: number): string => {
    return `${value.toFixed(1)}x`;
  };

  // Check if setting is modified from default
  const isModified = (key: keyof AlgorithmSettings): boolean => {
    if (!showDifferences) return false;
    return settings[key] !== compareSettings[key];
  };

  // Organize settings into logical groups
  const settingGroups = useMemo((): SettingGroup[] => [
    {
      title: 'ATR Configuration',
      icon: <SpeedIcon />,
      settings: [
        {
          key: 'atr_multiplier',
          label: 'ATR Multiplier',
          value: settings.atr_multiplier,
          unit: 'x',
          description: 'Multiplier applied to Average True Range for volatility filtering',
          isModified: isModified('atr_multiplier'),
          formatValue: formatMultiplier,
        },
      ],
    },
    {
      title: 'EMA Thresholds',
      icon: <TrendingUpIcon />,
      settings: [
        {
          key: 'ema5_rising_threshold',
          label: 'EMA5 Rising',
          value: settings.ema5_rising_threshold,
          unit: '%',
          description: 'Minimum percentage change required for EMA5 to be considered rising',
          isModified: isModified('ema5_rising_threshold'),
          formatValue: formatPercentage,
        },
        {
          key: 'ema8_rising_threshold',
          label: 'EMA8 Rising',
          value: settings.ema8_rising_threshold,
          unit: '%',
          description: 'Minimum percentage change required for EMA8 to be considered rising',
          isModified: isModified('ema8_rising_threshold'),
          formatValue: formatPercentage,
        },
        {
          key: 'ema21_rising_threshold',
          label: 'EMA21 Rising',
          value: settings.ema21_rising_threshold,
          unit: '%',
          description: 'Minimum percentage change required for EMA21 to be considered rising',
          isModified: isModified('ema21_rising_threshold'),
          formatValue: formatPercentage,
        },
      ],
    },
    {
      title: 'Risk Filters',
      icon: <SettingsIcon />,
      settings: [
        {
          key: 'volatility_filter',
          label: 'Volatility Filter',
          value: settings.volatility_filter,
          unit: '%',
          description: 'Maximum allowed volatility for signal generation',
          isModified: isModified('volatility_filter'),
          formatValue: formatPercentage,
        },
        {
          key: 'fomo_filter',
          label: 'FOMO Filter',
          value: settings.fomo_filter,
          unit: '%',
          description: 'Filter to prevent Fear of Missing Out trades on overextended moves',
          isModified: isModified('fomo_filter'),
          formatValue: formatPercentage,
        },
      ],
    },
    {
      title: 'Timeframe Settings',
      icon: <TimelineIcon />,
      settings: [
        {
          key: 'higher_timeframe',
          label: 'Higher Timeframe',
          value: settings.higher_timeframe,
          description: 'Higher timeframe used for trend confirmation',
          isModified: isModified('higher_timeframe'),
        },
      ],
    },
  ], [settings, compareSettings, showDifferences]);

  // Render individual setting item
  const renderSettingItem = (setting: SettingItem) => {
    const displayValue = setting.formatValue 
      ? setting.formatValue(setting.value)
      : `${setting.value}${setting.unit || ''}`;

    return (
      <Grid item xs={12} sm={6} md={4} key={setting.key}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            border: `1px solid ${theme.palette.divider}`,
            borderLeft: setting.isModified 
              ? `4px solid ${theme.palette.warning.main}`
              : `4px solid ${theme.palette.grey[300]}`,
            backgroundColor: setting.isModified 
              ? theme.palette.warning.light + '10'
              : 'transparent',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: theme.shadows[2],
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Tooltip title={setting.description} placement="top" arrow>
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
                {setting.label}
              </Typography>
            </Tooltip>
            {setting.isModified && (
              <Chip
                label="Modified"
                size="small"
                color="warning"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            )}
          </Box>
          
          <Typography
            variant="h6"
            fontWeight="bold"
            color={setting.isModified ? 'warning.main' : 'text.primary'}
            sx={{ mb: 0.5 }}
          >
            {displayValue}
          </Typography>
          
          {setting.isModified && compareSettings && (
            <Typography variant="caption" color="text.secondary">
              Default: {setting.formatValue 
                ? setting.formatValue(compareSettings[setting.key])
                : `${compareSettings[setting.key]}${setting.unit || ''}`}
            </Typography>
          )}
        </Paper>
      </Grid>
    );
  };

  // Render setting group
  const renderSettingGroup = (group: SettingGroup, index: number) => (
    <Box key={group.title} sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Box sx={{ color: theme.palette.primary.main }}>
          {group.icon}
        </Box>
        <Typography variant="h6" color="text.primary" fontWeight="600">
          {group.title}
        </Typography>
      </Box>
      
      <Grid container spacing={2}>
        {group.settings.map(renderSettingItem)}
      </Grid>
      
      {index < settingGroups.length - 1 && (
        <Divider sx={{ mt: 3 }} />
      )}
    </Box>
  );

  // Count modified settings
  const modifiedCount = useMemo(() => {
    if (!showDifferences) return 0;
    return Object.keys(settings).filter(key => 
      isModified(key as keyof AlgorithmSettings)
    ).length;
  }, [settings, compareSettings, showDifferences]);

  return (
    <Box className={className} role="region" aria-label="Scan settings configuration">
      {/* Summary header */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: theme.palette.grey[50], borderRadius: 1 }}>
        <Typography variant="body1" color="text.primary" gutterBottom>
          Algorithm Configuration
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {showDifferences && modifiedCount > 0 ? (
            <>
              {modifiedCount} parameter{modifiedCount !== 1 ? 's' : ''} modified from default values
            </>
          ) : (
            'All parameters using default values'
          )}
        </Typography>
      </Box>

      {/* Settings groups */}
      {settingGroups.map((group, index) => renderSettingGroup(group, index))}

      {/* Legend for modified settings */}
      {showDifferences && modifiedCount > 0 && (
        <Box sx={{ mt: 3, p: 2, backgroundColor: theme.palette.warning.light + '20', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                backgroundColor: theme.palette.warning.main,
                borderRadius: 0.5,
              }}
            />
            Orange border indicates parameters that differ from default values
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ScanSettingsSection;