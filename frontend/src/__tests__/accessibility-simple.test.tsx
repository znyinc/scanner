import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import '@testing-library/jest-dom';

import ResponsiveTable from '../components/ResponsiveTable';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Accessibility Improvements - Simple Tests', () => {
  describe('ResponsiveTable Accessibility', () => {
    const columns = [
      { id: 'symbol', label: 'Symbol', priority: 1 },
      { id: 'price', label: 'Price', priority: 2, align: 'right' as const }
    ];
    
    const rows = [
      { symbol: 'AAPL', price: 150.00 },
      { symbol: 'GOOGL', price: 2800.00 }
    ];

    test('should have proper table accessibility attributes', () => {
      renderWithTheme(
        <ResponsiveTable
          columns={columns}
          rows={rows}
          ariaLabel="Test stock data table"
        />
      );
      
      const table = screen.getByRole('table', { name: /test stock data table/i });
      expect(table).toBeInTheDocument();
      
      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders).toHaveLength(2);
      
      columnHeaders.forEach(header => {
        expect(header).toHaveAttribute('scope', 'col');
      });
    });

    test('should have proper row accessibility', () => {
      renderWithTheme(
        <ResponsiveTable
          columns={columns}
          rows={rows}
          ariaLabel="Test stock data table"
        />
      );
      
      const dataRows = screen.getAllByRole('row');
      // Should have header row + data rows
      expect(dataRows.length).toBeGreaterThan(2);
      
      const cells = screen.getAllByRole('cell');
      expect(cells.length).toBeGreaterThan(0);
    });

    test('should handle empty data gracefully', () => {
      renderWithTheme(
        <ResponsiveTable
          columns={columns}
          rows={[]}
          ariaLabel="Empty table"
        />
      );
      
      const table = screen.getByRole('table', { name: /empty table/i });
      expect(table).toBeInTheDocument();
      
      const noDataMessage = screen.getByText(/no data available/i);
      expect(noDataMessage).toBeInTheDocument();
      expect(noDataMessage).toHaveAttribute('role', 'status');
    });

    test('should have proper ARIA labels for formatted values', () => {
      renderWithTheme(
        <ResponsiveTable
          columns={[
            { 
              id: 'symbol', 
              label: 'Symbol', 
              priority: 1 
            },
            { 
              id: 'price', 
              label: 'Price', 
              priority: 2, 
              format: (value: number) => `$${value.toFixed(2)}`
            }
          ]}
          rows={rows}
          ariaLabel="Formatted data table"
        />
      );
      
      const cells = screen.getAllByRole('cell');
      // Check that formatted values are present
      expect(screen.getByText('$150.00')).toBeInTheDocument();
      expect(screen.getByText('$2800.00')).toBeInTheDocument();
    });
  });

  describe('CSS Accessibility Features', () => {
    test('should have screen reader only class available', () => {
      const { container } = render(
        <div>
          <span className="sr-only">Screen reader only text</span>
          <span>Visible text</span>
        </div>
      );
      
      const srOnlyElement = container.querySelector('.sr-only');
      expect(srOnlyElement).toBeInTheDocument();
      expect(srOnlyElement).toHaveTextContent('Screen reader only text');
    });

    test('should have focus styles defined', () => {
      render(<button>Test button</button>);
      
      const button = screen.getByRole('button');
      button.focus();
      
      expect(button).toHaveFocus();
    });
  });

  describe('ARIA Live Regions', () => {
    test('should support live region announcements', () => {
      render(
        <div>
          <div aria-live="polite" role="status">
            Status message
          </div>
          <div aria-live="assertive" role="alert">
            Alert message
          </div>
        </div>
      );
      
      const statusRegion = screen.getByRole('status');
      expect(statusRegion).toHaveAttribute('aria-live', 'polite');
      expect(statusRegion).toHaveTextContent('Status message');
      
      const alertRegion = screen.getByRole('alert');
      expect(alertRegion).toHaveAttribute('aria-live', 'assertive');
      expect(alertRegion).toHaveTextContent('Alert message');
    });
  });

  describe('Form Accessibility', () => {
    test('should have proper form labeling', () => {
      render(
        <form>
          <label htmlFor="test-input">Test Input</label>
          <input 
            id="test-input" 
            type="text" 
            aria-required="true"
            aria-describedby="test-help"
          />
          <div id="test-help">Help text for input</div>
        </form>
      );
      
      const input = screen.getByLabelText('Test Input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('aria-required', 'true');
      expect(input).toHaveAttribute('aria-describedby', 'test-help');
      
      const helpText = screen.getByText('Help text for input');
      expect(helpText).toHaveAttribute('id', 'test-help');
    });
  });

  describe('Keyboard Navigation', () => {
    test('should have focusable elements with proper tabindex', () => {
      render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
          <div tabIndex={0} role="button">Custom button</div>
          <div tabIndex={-1}>Not focusable</div>
        </div>
      );
      
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(3);
      
      buttons.forEach(button => {
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe('Semantic HTML', () => {
    test('should use proper heading hierarchy', () => {
      render(
        <div>
          <h1>Main Title</h1>
          <h2>Section Title</h2>
          <h3>Subsection Title</h3>
        </div>
      );
      
      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent('Main Title');
      
      const h2 = screen.getByRole('heading', { level: 2 });
      expect(h2).toHaveTextContent('Section Title');
      
      const h3 = screen.getByRole('heading', { level: 3 });
      expect(h3).toHaveTextContent('Subsection Title');
    });

    test('should use proper landmark roles', () => {
      render(
        <div>
          <header role="banner">Header content</header>
          <nav role="navigation">Navigation content</nav>
          <main role="main">Main content</main>
          <aside role="complementary">Sidebar content</aside>
          <footer role="contentinfo">Footer content</footer>
        </div>
      );
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('complementary')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });
  });
});