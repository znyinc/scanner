import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPanel from '../SettingsPanel';
import { ApiService } from '../../services/api';
import { AlgorithmSettings } from '../../types';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

const mockSettings: AlgorithmSettings = {
  atr_multiplier: 2.0,
  ema5_rising_threshold: 0.02,
  ema8_rising_threshold: 0.01,
  ema21_rising_threshold: 0.005,
  volatility_filter: 1.5,
  fomo_filter: 1.0,
  higher_timeframe: '15m',
};

describe('SettingsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getSettings.mockResolvedValue(mockSettings);
    mockApiService.updateSettings.mockResolvedValue(mockSettings);
  });

  it('renders settings panel with initial elements', async () => {
    render(<SettingsPanel />);

    expect(screen.getByText('Algorithm Settings')).toBeInTheDocument();
    expect(screen.getByText('ATR (Average True Range) Settings')).toBeInTheDocument();
    expect(screen.getByText('EMA Rising Thresholds')).toBeInTheDocument();
    expect(screen.getByText('Additional Filters')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });
  });

  it('loads and displays current settings', async () => {
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('2')).toBeInTheDocument(); // ATR multiplier
      expect(screen.getByDisplayValue('0.02')).toBeInTheDocument(); // EMA5 threshold
      expect(screen.getByDisplayValue('0.01')).toBeInTheDocument(); // EMA8 threshold
      expect(screen.getByDisplayValue('0.005')).toBeInTheDocument(); // EMA21 threshold
      expect(screen.getByDisplayValue('1.5')).toBeInTheDocument(); // Volatility filter
      expect(screen.getByDisplayValue('1')).toBeInTheDocument(); // FOMO filter
    });
  });

  it('allows editing settings values', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    expect(atrMultiplierInput).toHaveValue(2.5);
  });

  it('shows Save Settings button as enabled when changes are made', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const saveButton = screen.getByText('Save Settings');
    expect(saveButton).toBeDisabled();

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    await waitFor(() => {
      expect(saveButton).not.toBeDisabled();
    });
  });

  it('saves settings when Save Settings button is clicked', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    const saveButton = screen.getByText('Save Settings');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockApiService.updateSettings).toHaveBeenCalledWith({
        ...mockSettings,
        atr_multiplier: 2.5,
      });
    });
  });

  it('displays success message after successful save', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    const saveButton = screen.getByText('Save Settings');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument();
    });
  });

  it('displays error message when save fails', async () => {
    const user = userEvent.setup();
    mockApiService.updateSettings.mockRejectedValue(new Error('Server error'));

    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    const saveButton = screen.getByText('Save Settings');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });

  it('resets to default values when Reset to Defaults is clicked', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Change a value first
    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '3.0');

    const resetButton = screen.getByText('Reset to Defaults');
    await user.click(resetButton);

    await waitFor(() => {
      expect(atrMultiplierInput).toHaveValue(2); // Default value
    });
  });

  it('discards changes when Discard Changes is clicked', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Change a value first
    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '3.0');

    await waitFor(() => {
      expect(screen.getByText('Discard Changes')).toBeInTheDocument();
    });

    const discardButton = screen.getByText('Discard Changes');
    await user.click(discardButton);

    await waitFor(() => {
      expect(atrMultiplierInput).toHaveValue(2); // Original value
    });
  });

  it('validates settings before saving', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    // Set invalid value (negative)
    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '-1');

    const saveButton = screen.getByText('Save Settings');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('ATR Multiplier must be between 0 and 10')).toBeInTheDocument();
    });

    expect(mockApiService.updateSettings).not.toHaveBeenCalled();
  });

  it('allows changing higher timeframe selection', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const higherTimeframeSelect = screen.getByLabelText('Higher Timeframe');
    await user.click(higherTimeframeSelect);

    const thirtyMinOption = screen.getByText('30 minutes');
    await user.click(thirtyMinOption);

    await waitFor(() => {
      expect(screen.getByDisplayValue('30m')).toBeInTheDocument();
    });
  });

  it('shows loading state during save operation', async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: AlgorithmSettings) => void;
    const savePromise = new Promise<AlgorithmSettings>((resolve) => {
      resolvePromise = resolve;
    });
    mockApiService.updateSettings.mockReturnValue(savePromise);

    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const atrMultiplierInput = screen.getByLabelText('ATR Multiplier');
    await user.clear(atrMultiplierInput);
    await user.type(atrMultiplierInput, '2.5');

    const saveButton = screen.getByText('Save Settings');
    await user.click(saveButton);

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(saveButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!(mockSettings);

    await waitFor(() => {
      expect(screen.getByText('Save Settings')).toBeInTheDocument();
      expect(saveButton).toBeDisabled(); // Should be disabled again since no changes
    });
  });

  it('displays tooltips for setting explanations', async () => {
    const user = userEvent.setup();
    render(<SettingsPanel />);

    await waitFor(() => {
      expect(mockApiService.getSettings).toHaveBeenCalled();
    });

    const infoButtons = screen.getAllByTestId('InfoIcon');
    expect(infoButtons.length).toBeGreaterThan(0);

    // Test hovering over one of the info icons
    await user.hover(infoButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument();
    });
  });

  it('handles loading error gracefully', async () => {
    mockApiService.getSettings.mockRejectedValue(new Error('Failed to load'));

    render(<SettingsPanel />);

    await waitFor(() => {
      // Should still render with default values
      expect(screen.getByText('Algorithm Settings')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2')).toBeInTheDocument(); // Default ATR multiplier
    });
  });
});