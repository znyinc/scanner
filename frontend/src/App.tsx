import React from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Tabs,
  Tab,
  Box,
  useMediaQuery,
} from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import { AppProvider, useAppContext, useAppActions } from './contexts/AppContext';
import ScannerDashboard from './components/ScannerDashboard';
import BacktestInterface from './components/BacktestInterface';
import HistoryViewer from './components/HistoryViewer';
import SettingsPanel from './components/SettingsPanel';
import NotificationSystem from './components/NotificationSystem';
import StatusIndicator from './components/StatusIndicator';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  typography: {
    // Responsive typography
    h4: {
      fontSize: '1.75rem',
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h6: {
      fontSize: '1.25rem',
      '@media (max-width:600px)': {
        fontSize: '1.1rem',
      },
    },
  },
  components: {
    // Add rotating animation for sync icon
    MuiSvgIcon: {
      styleOverrides: {
        root: {
          '&.rotating': {
            animation: 'spin 2s linear infinite',
          },
        },
      },
    },
    // Enhanced button accessibility and touch targets
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 44, // Minimum touch target size
          '@media (max-width:600px)': {
            minHeight: 48, // Larger touch targets on mobile
            fontSize: '0.875rem',
          },
        },
      },
    },
    // Enhanced table responsiveness
    MuiTable: {
      styleOverrides: {
        root: {
          '@media (max-width:600px)': {
            fontSize: '0.75rem',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          '@media (max-width:600px)': {
            padding: '8px 4px',
            fontSize: '0.75rem',
          },
        },
      },
    },
    // Enhanced tab accessibility
    MuiTab: {
      styleOverrides: {
        root: {
          minHeight: 48,
          '@media (max-width:600px)': {
            minWidth: 'auto',
            fontSize: '0.75rem',
            padding: '6px 8px',
          },
        },
      },
    },
    // Enhanced form controls
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            '@media (max-width:600px)': {
              fontSize: '16px', // Prevents zoom on iOS
            },
          },
        },
      },
    },
  },
});

// Add keyframes for rotation animation
const globalStyles = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div 
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const AppContent: React.FC = () => {
  const { state } = useAppContext();
  const { setActiveTab } = useAppActions();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const navigateToHistory = () => {
    setActiveTab(2);
  };

  const navigateToSettings = () => {
    setActiveTab(3);
  };

  // Skip link for keyboard navigation
  const handleSkipToMain = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.focus();
        mainContent.scrollIntoView();
      }
    }
  };

  return (
    <>
      <style>{globalStyles}</style>
      <CssBaseline />
      
      {/* Skip to main content link for keyboard users */}
      <a 
        href="#main-content" 
        className="skip-link"
        onKeyDown={handleSkipToMain}
        aria-label="Skip to main content"
      >
        Skip to main content
      </a>
      
      <AppBar position="static" role="banner">
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
          <TrendingUp sx={{ mr: { xs: 1, sm: 2 } }} aria-hidden="true" />
          <Typography 
            variant="h6" 
            component="h1" 
            sx={{ 
              flexGrow: 1,
              fontSize: { xs: '1rem', sm: '1.25rem' },
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            {isMobile ? 'Stock Scanner' : 'Stock Scanner - EMA-ATR Algorithm'}
          </Typography>
          <StatusIndicator />
        </Toolbar>
      </AppBar>

      <Container 
        maxWidth="xl" 
        component="main"
        id="main-content"
        tabIndex={-1}
        sx={{ 
          mt: { xs: 1, sm: 2 },
          px: { xs: 1, sm: 2 },
          pb: { xs: 2, sm: 3 },
          outline: 'none'
        }}
        role="main"
        aria-label="Main application content"
      >
        <nav role="navigation" aria-label="Main navigation">
          <Tabs 
            value={state.activeTab} 
            onChange={handleTabChange}
            variant={isMobile ? "scrollable" : "standard"}
            scrollButtons={isMobile ? "auto" : false}
            allowScrollButtonsMobile
            sx={{ 
              borderBottom: 1, 
              borderColor: 'divider', 
              mb: { xs: 1, sm: 2 },
              '& .MuiTabs-flexContainer': {
                gap: { xs: 0, sm: 1 }
              },
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
                '&.Mui-selected': {
                  fontWeight: 600,
                }
              }
            }}
            aria-label="Main navigation tabs"
          >
            <Tab 
              label="Scanner" 
              id="tab-0"
              aria-controls="tabpanel-0"
              sx={{ minWidth: { xs: 'auto', sm: 90 } }}
            />
            <Tab 
              label="Backtest" 
              id="tab-1"
              aria-controls="tabpanel-1"
              sx={{ minWidth: { xs: 'auto', sm: 90 } }}
            />
            <Tab 
              label="History" 
              id="tab-2"
              aria-controls="tabpanel-2"
              sx={{ minWidth: { xs: 'auto', sm: 90 } }}
            />
            <Tab 
              label="Settings" 
              id="tab-3"
              aria-controls="tabpanel-3"
              sx={{ minWidth: { xs: 'auto', sm: 90 } }}
            />
          </Tabs>
        </nav>

        <TabPanel value={state.activeTab} index={0}>
          <ScannerDashboard 
            onViewHistory={navigateToHistory}
            onConfigureSettings={navigateToSettings}
          />
        </TabPanel>

        <TabPanel value={state.activeTab} index={1}>
          <BacktestInterface />
        </TabPanel>

        <TabPanel value={state.activeTab} index={2}>
          <HistoryViewer />
        </TabPanel>

        <TabPanel value={state.activeTab} index={3}>
          <SettingsPanel />
        </TabPanel>
      </Container>

      <NotificationSystem />
    </>
  );
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ThemeProvider>
  );
}

export default App;