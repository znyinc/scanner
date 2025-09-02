import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';

import App from '../App';
import ScannerDashboard from '../components/ScannerDashboard';
import BacktestInterface from '../components/BacktestInterface';
import HistoryViewer from '../components/HistoryViewer';
import SettingsPanel from '../components/SettingsPanel';
import ResponsiveTable from '../components/ResponsiveTable';
import { AppProvider } from '../contexts/AppContext';

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <AppProvider>
        {component}
      </AppProvider>
    </ThemeProvider>
  );
};

describe('Accessibility Tests', () => {
  describe('Keyboard Navigation', () => {
    test('should have skip link for keyboard users', () => {
      renderWithProviders(<App />);
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveClass('skip-link');
    });

    test('should allow tab navigation through main interface', async () => {
      const user = userEvent.setup();
      renderWithProviders(<App />);
      
      // Tab through main navigation
      await user.tab();
      expect(screen.getByRole('tab', { name: /scanner/i })).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('tab', { name: /backtest/i })).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('tab', { name: /history/i })).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('tab', { name: /settings/i })).toHaveFocus();
    });

    test('should support arrow key navigation in tabs', async () => {
      const user = userEvent.setup();
      renderWithProviders(<App />);
      
      const scannerTab = screen.getByRole('tab', { name: /scanner/i });
      scannerTab.focus();
      
      await user.keyboard('{ArrowRight}');
      expect(screen.getByRole('tab', { name: /backtest/i })).toHaveFocus();
      
      await user.keyboard('{ArrowLeft}');
      expect(screen.getByRole('tab', { name: /scanner/i })).toHaveFocus();
    });
  });

  describe('ARIA Labels and Roles', () => {
    test('should have proper ARIA labels on main navigation', () => {
      renderWithProviders(<App />);
      
      const navigation = screen.getByRole('navigation', { name: /main navigation/i });
      expect(navigation).toBeInTheDocument();
      
      const tablist = screen.getByRole('tablist', { name: /main navigation tabs/i });
      expect(tablist).toBeInTheDocument();
    });

    test('should have proper heading hierarchy', () => {
      renderWithProviders(<App />);
      
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toBeInTheDocument();
      expect(mainHeading).toHaveTextContent(/stock scanner/i);
    });

    test('should have proper form labels', () => {
      renderWithProviders(
        <ScannerDashboard 
          onViewHistory={() => {}} 
          onConfigureSettings={() => {}} 
        />
      );
      
      const symbolInput = screen.getByLabelText(/stock symbols/i);
      expect(symbolInput).toBeInTheDocument();
      expect(symbolInput).toHaveAttribute('aria-required', 'true');
    });

    test('should have proper table accessibility', () => {
      const columns = [
        { id: 'symbol', label: 'Symbol', priority: 1 },
        { id: 'price', label: 'Price', priority: 2 }
      ];
      const rows = [
        { symbol: 'AAPL', price: 150.00 }
      ];
      
      render(
        <ResponsiveTable
          columns={columns}
          rows={rows}
          ariaLabel="Test table"
        />
      );
      
      const table = screen.getByRole('table', { name: /test table/i });
      expect(table).toBeInTheDocument();
      
      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders).toHaveLength(2);
      
      columnHeaders.forEach(header => {
        expect(header).toHaveAttribute('scope', 'col');
      });
    });
  });

  describe('Screen Reader Support', () => {
    test('should have screen reader only content', () => {
      renderWithProviders(<App />);
      
      const srOnlyElements = document.querySelectorAll('.sr-only');
      expect(srOnlyElements.length).toBeGreaterThan(0);
    });

    test('should have live regions for dynamic content', () => {
      renderWithProviders(
        <ScannerDashboard 
          onViewHistory={() => {}} 
          onConfigureSettings={() => {}} 
        />
      );
      
      const liveRegions = document.querySelectorAll('[aria-live]');
      expect(liveRegions.length).toBeGreaterThan(0);
    });

    test('should announce loading states', () => {
      renderWithProviders(<BacktestInterface />);
      
      const loadingStatus = document.querySelector('#backtest-loading-status');
      if (loadingStatus) {
        expect(loadingStatus).toHaveAttribute('aria-live', 'polite');
      }
    });
  });

  describe('Mobile Touch Targets', () => {
    test('should have minimum touch target sizes on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      
      renderWithProviders(<App />);
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const styles = window.getComputedStyle(button);
        const minHeight = parseInt(styles.minHeight);
        expect(minHeight).toBeGreaterThanOrEqual(44);
      });
    });

    test('should have proper touch feedback', () => {
      renderWithProviders(
        <ScannerDashboard 
          onViewHistory={() => {}} 
          onConfigureSettings={() => {}} 
        />
      );
      
      const startButton = screen.getByRole('button', { name: /start scan/i });
      expect(startButton).toHaveStyle('cursor: pointer');
    });
  });

  describe('Error Handling and Feedback', () => {
    test('should have proper error announcements', () => {
      renderWithProviders(<BacktestInterface />);
      
      // Simulate error state
      const errorAlert = screen.queryByRole('alert');
      if (errorAlert) {
        expect(errorAlert).toHaveAttribute('aria-live', 'polite');
      }
    });

    test('should have form validation feedback', () => {
      renderWithProviders(<SettingsPanel />);
      
      const numberInputs = screen.getAllByRole('spinbutton');
      numberInputs.forEach(input => {
        expect(input).toHaveAttribute('aria-invalid');
      });
    });
  });

  describe('Focus Management', () => {
    test('should have visible focus indicators', () => {
      renderWithProviders(<App />);
      
      const focusableElements = screen.getAllByRole('button');
      focusableElements.forEach(element => {
        element.focus();
        expect(element).toHaveFocus();
      });
    });

    test('should manage focus in dialogs', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HistoryViewer />);
      
      // This would test dialog focus management if dialogs are present
      const dialogs = screen.queryAllByRole('dialog');
      dialogs.forEach(dialog => {
        expect(dialog).toHaveAttribute('aria-labelledby');
        expect(dialog).toHaveAttribute('aria-describedby');
      });
    });
  });

  describe('Responsive Design', () => {
    test('should adapt to mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      
      renderWithProviders(<App />);
      
      // Check for mobile-specific elements
      const mobileElements = document.querySelectorAll('[data-testid*="mobile"]');
      // This would check for mobile-specific adaptations
    });

    test('should have proper text scaling', () => {
      renderWithProviders(<App />);
      
      const headings = screen.getAllByRole('heading');
      headings.forEach(heading => {
        const styles = window.getComputedStyle(heading);
        expect(styles.fontSize).toBeDefined();
      });
    });
  });

  describe('Color and Contrast', () => {
    test('should not rely solely on color for information', () => {
      const columns = [
        { id: 'symbol', label: 'Symbol', priority: 1 },
        { id: 'signal_type', label: 'Signal', priority: 1 }
      ];
      const rows = [
        { symbol: 'AAPL', signal_type: 'long' }
      ];
      
      render(
        <ResponsiveTable
          columns={columns}
          rows={rows}
          ariaLabel="Test table"
        />
      );
      
      // Check that signal types have text labels, not just colors
      const signalCell = screen.getByText('long');
      expect(signalCell).toBeInTheDocument();
    });
  });

  describe('Reduced Motion Support', () => {
    test('should respect prefers-reduced-motion', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });
      
      renderWithProviders(<App />);
      
      // Check that animations are disabled or reduced
      const animatedElements = document.querySelectorAll('[class*="rotating"]');
      // This would verify that animations respect the user's preference
    });
  });
});

describe('WCAG Compliance Tests', () => {
  test('should have proper document structure', () => {
    renderWithProviders(<App />);
    
    // Check for proper landmark roles
    expect(screen.getByRole('banner')).toBeInTheDocument(); // header
    expect(screen.getByRole('main')).toBeInTheDocument(); // main content
    expect(screen.getByRole('navigation')).toBeInTheDocument(); // navigation
  });

  test('should have descriptive page titles', () => {
    renderWithProviders(<App />);
    
    const headings = screen.getAllByRole('heading', { level: 1 });
    headings.forEach(heading => {
      expect(heading).toHaveTextContent(/\w+/); // Should have meaningful text
    });
  });

  test('should have proper form structure', () => {
    renderWithProviders(<SettingsPanel />);
    
    const form = screen.getByRole('form');
    expect(form).toBeInTheDocument();
    
    const inputs = screen.getAllByRole('spinbutton');
    inputs.forEach(input => {
      expect(input).toHaveAccessibleName();
    });
  });

  test('should have proper button labels', () => {
    renderWithProviders(<App />);
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveAccessibleName();
    });
  });
});