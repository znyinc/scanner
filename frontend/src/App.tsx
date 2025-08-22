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
    <div hidden={value !== index}>
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const AppContent: React.FC = () => {
  const { state } = useAppContext();
  const { setActiveTab } = useAppActions();

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const navigateToHistory = () => {
    setActiveTab(2);
  };

  const navigateToSettings = () => {
    setActiveTab(3);
  };

  return (
    <>
      <style>{globalStyles}</style>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <TrendingUp sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Stock Scanner - EMA-ATR Algorithm
          </Typography>
          <StatusIndicator />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 2 }}>
        <Tabs 
          value={state.activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        >
          <Tab label="Scanner" />
          <Tab label="Backtest" />
          <Tab label="History" />
          <Tab label="Settings" />
        </Tabs>

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