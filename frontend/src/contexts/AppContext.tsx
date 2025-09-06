import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AlgorithmSettings, ScanResult, BacktestResult, ApiError } from '../types';
import { ApiService, handleApiError } from '../services/api';

// State interface
interface AppState {
  // Settings
  settings: AlgorithmSettings | null;
  settingsLoading: boolean;
  settingsError: string | null;
  
  // Scan data
  currentScanResult: ScanResult | null;
  scanHistory: ScanResult[];
  scanLoading: boolean;
  scanError: string | null;
  
  // Backtest data
  currentBacktestResult: BacktestResult | null;
  backtestHistory: BacktestResult[];
  backtestLoading: boolean;
  backtestError: string | null;
  
  // App status
  apiStatus: 'online' | 'offline' | 'error' | 'checking';
  networkStatus: boolean;
  
  // UI state
  activeTab: number;
  notifications: Notification[];
}

// Notification interface
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
  autoHide?: boolean;
  error?: ApiError;
  actions?: Array<{
    label: string;
    action: () => void;
    variant?: 'primary' | 'secondary';
  }>;
}

// Action types
type AppAction =
  // Settings actions
  | { type: 'SETTINGS_LOADING' }
  | { type: 'SETTINGS_SUCCESS'; payload: AlgorithmSettings }
  | { type: 'SETTINGS_ERROR'; payload: string }
  
  // Scan actions
  | { type: 'SCAN_LOADING' }
  | { type: 'SCAN_SUCCESS'; payload: ScanResult }
  | { type: 'SCAN_ERROR'; payload: string }
  | { type: 'SCAN_HISTORY_SUCCESS'; payload: ScanResult[] }
  
  // Backtest actions
  | { type: 'BACKTEST_LOADING' }
  | { type: 'BACKTEST_SUCCESS'; payload: BacktestResult }
  | { type: 'BACKTEST_ERROR'; payload: string }
  | { type: 'BACKTEST_HISTORY_SUCCESS'; payload: BacktestResult[] }
  
  // App status actions
  | { type: 'SET_API_STATUS'; payload: 'online' | 'offline' | 'error' | 'checking' }
  | { type: 'SET_NETWORK_STATUS'; payload: boolean }
  
  // UI actions
  | { type: 'SET_ACTIVE_TAB'; payload: number }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'id' | 'timestamp'> }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_NOTIFICATIONS' }
  
  // Clear actions
  | { type: 'CLEAR_SCAN_ERROR' }
  | { type: 'CLEAR_BACKTEST_ERROR' }
  | { type: 'CLEAR_SETTINGS_ERROR' };

// Initial state
const initialState: AppState = {
  settings: null,
  settingsLoading: false,
  settingsError: null,
  
  currentScanResult: null,
  scanHistory: [],
  scanLoading: false,
  scanError: null,
  
  currentBacktestResult: null,
  backtestHistory: [],
  backtestLoading: false,
  backtestError: null,
  
  apiStatus: 'checking',
  networkStatus: navigator.onLine,
  
  activeTab: 0,
  notifications: [],
};

// Reducer
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    // Settings
    case 'SETTINGS_LOADING':
      return { ...state, settingsLoading: true, settingsError: null };
    case 'SETTINGS_SUCCESS':
      return { ...state, settings: action.payload, settingsLoading: false, settingsError: null };
    case 'SETTINGS_ERROR':
      return { ...state, settingsLoading: false, settingsError: action.payload };
    
    // Scan
    case 'SCAN_LOADING':
      return { ...state, scanLoading: true, scanError: null };
    case 'SCAN_SUCCESS':
      return { 
        ...state, 
        currentScanResult: action.payload, 
        scanLoading: false, 
        scanError: null,
        scanHistory: [action.payload, ...state.scanHistory]
      };
    case 'SCAN_ERROR':
      return { ...state, scanLoading: false, scanError: action.payload };
    case 'SCAN_HISTORY_SUCCESS':
      return { ...state, scanHistory: action.payload };
    
    // Backtest
    case 'BACKTEST_LOADING':
      return { ...state, backtestLoading: true, backtestError: null };
    case 'BACKTEST_SUCCESS':
      return { 
        ...state, 
        currentBacktestResult: action.payload, 
        backtestLoading: false, 
        backtestError: null,
        backtestHistory: [action.payload, ...state.backtestHistory]
      };
    case 'BACKTEST_ERROR':
      return { ...state, backtestLoading: false, backtestError: action.payload };
    case 'BACKTEST_HISTORY_SUCCESS':
      return { ...state, backtestHistory: action.payload };
    
    // App status
    case 'SET_API_STATUS':
      return { ...state, apiStatus: action.payload };
    case 'SET_NETWORK_STATUS':
      return { ...state, networkStatus: action.payload };
    
    // UI
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'ADD_NOTIFICATION':
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
      };
      return { ...state, notifications: [...state.notifications, notification] };
    case 'REMOVE_NOTIFICATION':
      return { 
        ...state, 
        notifications: state.notifications.filter(n => n.id !== action.payload) 
      };
    case 'CLEAR_NOTIFICATIONS':
      return { ...state, notifications: [] };
    
    // Clear errors
    case 'CLEAR_SCAN_ERROR':
      return { ...state, scanError: null };
    case 'CLEAR_BACKTEST_ERROR':
      return { ...state, backtestError: null };
    case 'CLEAR_SETTINGS_ERROR':
      return { ...state, settingsError: null };
    
    default:
      return state;
  }
};

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Monitor network status
  useEffect(() => {
    const handleOnline = () => dispatch({ type: 'SET_NETWORK_STATUS', payload: true });
    const handleOffline = () => dispatch({ type: 'SET_NETWORK_STATUS', payload: false });

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Check API status periodically
  useEffect(() => {
    const checkApiStatus = async () => {
      dispatch({ type: 'SET_API_STATUS', payload: 'checking' });
      try {
        const isHealthy = await ApiService.healthCheck();
        dispatch({ type: 'SET_API_STATUS', payload: isHealthy ? 'online' : 'error' });
      } catch {
        dispatch({ type: 'SET_API_STATUS', payload: 'offline' });
      }
    };

    // Initial check
    checkApiStatus();

    // Check every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  // Load initial settings
  useEffect(() => {
    const loadSettings = async () => {
      dispatch({ type: 'SETTINGS_LOADING' });
      try {
        const settings = await ApiService.getSettings();
        dispatch({ type: 'SETTINGS_SUCCESS', payload: settings });
      } catch (error: any) {
        dispatch({ type: 'SETTINGS_ERROR', payload: error.message });
      }
    };

    loadSettings();
  }, []);

  // Auto-remove notifications
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    state.notifications.forEach(notification => {
      if (notification.autoHide !== false) {
        const timer = setTimeout(() => {
          dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id });
        }, 5000);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [state.notifications]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

// Action creators for common operations
export const useAppActions = () => {
  const { dispatch } = useAppContext();

  return {
    // Settings actions
    loadSettings: async () => {
      dispatch({ type: 'SETTINGS_LOADING' });
      try {
        const settings = await ApiService.getSettings();
        dispatch({ type: 'SETTINGS_SUCCESS', payload: settings });
        return settings;
      } catch (error: any) {
        dispatch({ type: 'SETTINGS_ERROR', payload: error.message });
        throw error;
      }
    },

    updateSettings: async (settings: AlgorithmSettings) => {
      dispatch({ type: 'SETTINGS_LOADING' });
      try {
        const updatedSettings = await ApiService.updateSettings(settings);
        dispatch({ type: 'SETTINGS_SUCCESS', payload: updatedSettings });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'success', message: 'Settings updated successfully' }
        });
        return updatedSettings;
      } catch (error: any) {
        dispatch({ type: 'SETTINGS_ERROR', payload: error.message });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'error', message: `Failed to update settings: ${error.message}` }
        });
        throw error;
      }
    },

    // Scan actions
    initiateScan: async (symbols: string[], settings: AlgorithmSettings, onProgress?: (progress: number, message?: string) => void) => {
      
      dispatch({ type: 'SCAN_LOADING' });
      try {
        const result = await ApiService.initiateScan(symbols, settings, onProgress);
        
        dispatch({ type: 'SCAN_SUCCESS', payload: result });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { 
            type: 'success', 
            message: `Scan completed: ${result.signals_found.length} signals found` 
          }
        });
        return result;
      } catch (error: any) {

        dispatch({ type: 'SCAN_ERROR', payload: error.message });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'error', message: `Scan failed: ${error.message}` }
        });
        throw error;
      }
    },

    loadScanHistory: async (filters?: any) => {
      try {
        const history = await ApiService.getScanHistory(filters);
        dispatch({ type: 'SCAN_HISTORY_SUCCESS', payload: history });
        return history;
      } catch (error: any) {
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'error', message: `Failed to load scan history: ${error.message}` }
        });
        throw error;
      }
    },

    // Backtest actions
    runBacktest: async (
      symbols: string[], 
      startDate: string, 
      endDate: string, 
      settings: AlgorithmSettings,
      onProgress?: (progress: number, message?: string) => void
    ) => {
      dispatch({ type: 'BACKTEST_LOADING' });
      try {
        const result = await ApiService.runBacktest(symbols, startDate, endDate, settings, onProgress);
        dispatch({ type: 'BACKTEST_SUCCESS', payload: result });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { 
            type: 'success', 
            message: `Backtest completed: ${result.performance.total_trades} trades analyzed` 
          }
        });
        return result;
      } catch (error: any) {
        dispatch({ type: 'BACKTEST_ERROR', payload: error.message });
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'error', message: `Backtest failed: ${error.message}` }
        });
        throw error;
      }
    },

    loadBacktestHistory: async (filters?: any) => {
      try {
        const history = await ApiService.getBacktestHistory(filters);
        dispatch({ type: 'BACKTEST_HISTORY_SUCCESS', payload: history });
        return history;
      } catch (error: any) {
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { type: 'error', message: `Failed to load backtest history: ${error.message}` }
        });
        throw error;
      }
    },

    // UI actions
    setActiveTab: (tab: number) => {
      dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
    },

    addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
    },

    removeNotification: (id: string) => {
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
    },

    clearNotifications: () => {
      dispatch({ type: 'CLEAR_NOTIFICATIONS' });
    },

    // Clear error actions
    clearScanError: () => dispatch({ type: 'CLEAR_SCAN_ERROR' }),
    clearBacktestError: () => dispatch({ type: 'CLEAR_BACKTEST_ERROR' }),
    clearSettingsError: () => dispatch({ type: 'CLEAR_SETTINGS_ERROR' }),
  };
};