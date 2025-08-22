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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Tooltip,
  IconButton,
} from '@mui/material';
import { Save, RestoreFromTrash, Info } from '@mui/icons-material';
import { ApiService, handleApiError } from '../services/api';
import { AlgorithmSettings } from '../types';

const defaultSettings: AlgorithmSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

const SettingsPanel: React.FC = () => {
  const [settings, setSettings] = useState<AlgorithmSettings>(defaultSettings);
  const [originalSettings, setOriginalSettings] = useState<AlgorithmSettings>(defaultSettings);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [hasChanges, setHasChanges] = useState<boolean>(false);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    // Check if settings have changed
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [settings, originalSettings]);

  const loadSettings = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const currentSettings = await ApiService.getSettings();
      setSettings(currentSettings);
      setOriginalSettings(currentSettings);
    } catch (err) {
      setError(handleApiError(err));
      // Use default settings if loading fails
      setSettings(defaultSettings);
      setOriginalSettings(defaultSettings);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    // Validate settings before saving
    const validationError = validateSettings(settings);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    setError('');
    setSuccess('');
    
    try {
      const updatedSettings = await ApiService.updateSettings(settings);
      setSettings(updatedSettings);
      setOriginalSettings(updatedSettings);
      setSuccess('Settings saved successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsSaving(false);
    }
  };

  const resetToDefaults = () => {
    setSettings(defaultSettings);
    setError('');
    setSuccess('');
  };

  const discardChanges = () => {
    setSettings(originalSettings);
    setError('');
    setSuccess('');
  };

  const validateSettings = (settingsToValidate: AlgorithmSettings): string | null => {
    if (settingsToValidate.atr_multiplier <= 0 || settingsToValidate.atr_multiplier > 10) {
      return 'ATR Multiplier must be between 0 and 10';
    }
    
    if (settingsToValidate.ema5_rising_threshold < 0 || settingsToValidate.ema5_rising_threshold > 1) {
      return 'EMA5 Rising Threshold must be between 0 and 1';
    }
    
    if (settingsToValidate.ema8_rising_threshold < 0 || settingsToValidate.ema8_rising_threshold > 1) {
      return 'EMA8 Rising Threshold must be between 0 and 1';
    }
    
    if (settingsToValidate.ema21_rising_threshold < 0 || settingsToValidate.ema21_rising_threshold > 1) {
      return 'EMA21 Rising Threshold must be between 0 and 1';
    }
    
    if (settingsToValidate.volatility_filter <= 0 || settingsToValidate.volatility_filter > 5) {
      return 'Volatility Filter must be between 0 and 5';
    }
    
    if (settingsToValidate.fomo_filter <= 0 || settingsToValidate.fomo_filter > 5) {
      return 'FOMO Filter must be between 0 and 5';
    }
    
    return null;
  };

  const handleNumberChange = (field: keyof AlgorithmSettings, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setSettings(prev => ({ ...prev, [field]: numValue }));
    }
  };

  const handleStringChange = (field: keyof AlgorithmSettings, value: string) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Algorithm Settings
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Configure the parameters for the EMA-ATR trading algorithm. Changes will affect all future scans and backtests.
      </Typography>

      {/* Error and Success Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Grid container spacing={3}>
            {/* ATR Settings */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                ATR (Average True Range) Settings
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="ATR Multiplier"
                  type="number"
                  value={settings.atr_multiplier}
                  onChange={(e) => handleNumberChange('atr_multiplier', e.target.value)}
                  inputProps={{ min: 0.1, max: 10, step: 0.1 }}
                  helperText="Multiplier for ATR line calculations (0.1 - 10)"
                />
                <Tooltip title="Controls the distance of ATR lines from EMAs. Higher values create wider bands.">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="Volatility Filter"
                  type="number"
                  value={settings.volatility_filter}
                  onChange={(e) => handleNumberChange('volatility_filter', e.target.value)}
                  inputProps={{ min: 0.1, max: 5, step: 0.1 }}
                  helperText="ATR volatility filter multiplier (0.1 - 5)"
                />
                <Tooltip title="Filters out low volatility stocks. Higher values require more volatility.">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* EMA Settings */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                EMA Rising Thresholds
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Minimum percentage change required to consider an EMA as "rising"
              </Typography>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="EMA5 Rising Threshold"
                  type="number"
                  value={settings.ema5_rising_threshold}
                  onChange={(e) => handleNumberChange('ema5_rising_threshold', e.target.value)}
                  inputProps={{ min: 0, max: 1, step: 0.001 }}
                  helperText="Threshold for EMA5 (0 - 1)"
                />
                <Tooltip title="Percentage change required for EMA5 to be considered rising. Default: 0.02 (2%)">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="EMA8 Rising Threshold"
                  type="number"
                  value={settings.ema8_rising_threshold}
                  onChange={(e) => handleNumberChange('ema8_rising_threshold', e.target.value)}
                  inputProps={{ min: 0, max: 1, step: 0.001 }}
                  helperText="Threshold for EMA8 (0 - 1)"
                />
                <Tooltip title="Percentage change required for EMA8 to be considered rising. Default: 0.01 (1%)">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="EMA21 Rising Threshold"
                  type="number"
                  value={settings.ema21_rising_threshold}
                  onChange={(e) => handleNumberChange('ema21_rising_threshold', e.target.value)}
                  inputProps={{ min: 0, max: 1, step: 0.001 }}
                  helperText="Threshold for EMA21 (0 - 1)"
                />
                <Tooltip title="Percentage change required for EMA21 to be considered rising. Default: 0.005 (0.5%)">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Additional Filters */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Additional Filters
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  label="FOMO Filter"
                  type="number"
                  value={settings.fomo_filter}
                  onChange={(e) => handleNumberChange('fomo_filter', e.target.value)}
                  inputProps={{ min: 0.1, max: 5, step: 0.1 }}
                  helperText="FOMO filter multiplier (0.1 - 5)"
                />
                <Tooltip title="Filters out stocks with excessive momentum to avoid FOMO trades.">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <FormControl fullWidth>
                  <InputLabel>Higher Timeframe</InputLabel>
                  <Select
                    value={settings.higher_timeframe}
                    onChange={(e) => handleStringChange('higher_timeframe', e.target.value)}
                    label="Higher Timeframe"
                  >
                    <MenuItem value="5m">5 minutes</MenuItem>
                    <MenuItem value="15m">15 minutes</MenuItem>
                    <MenuItem value="30m">30 minutes</MenuItem>
                    <MenuItem value="1h">1 hour</MenuItem>
                  </Select>
                </FormControl>
                <Tooltip title="Higher timeframe used for trend confirmation. Default: 15m">
                  <IconButton size="small">
                    <Info />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={resetToDefaults}
                  startIcon={<RestoreFromTrash />}
                  disabled={isSaving}
                >
                  Reset to Defaults
                </Button>
                
                {hasChanges && (
                  <Button
                    variant="outlined"
                    onClick={discardChanges}
                    disabled={isSaving}
                  >
                    Discard Changes
                  </Button>
                )}
                
                <Button
                  variant="contained"
                  onClick={saveSettings}
                  startIcon={isSaving ? <CircularProgress size={20} /> : <Save />}
                  disabled={isSaving || !hasChanges}
                >
                  {isSaving ? 'Saving...' : 'Save Settings'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SettingsPanel;