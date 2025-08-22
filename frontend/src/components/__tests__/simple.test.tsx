import React from 'react';
import { render, screen } from '@testing-library/react';
import { ApiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Simple test to verify the setup works
describe('Simple Component Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('can render a simple component', () => {
    const SimpleComponent = () => <div>Hello World</div>;
    render(<SimpleComponent />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('can mock API service', () => {
    mockApiService.getSettings.mockResolvedValue({
      atr_multiplier: 2.0,
      ema5_rising_threshold: 0.02,
      ema8_rising_threshold: 0.01,
      ema21_rising_threshold: 0.005,
      volatility_filter: 1.5,
      fomo_filter: 1.0,
      higher_timeframe: '15m',
    });

    expect(mockApiService.getSettings).toBeDefined();
  });
});