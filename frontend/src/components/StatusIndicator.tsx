import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Wifi,
  WifiOff,
  Cloud,
  CloudOff,
  Error,
  Sync,
} from '@mui/icons-material';
import { useAppContext } from '../contexts/AppContext';
import { formatApiStatus, formatNetworkStatus } from '../utils/formatters';

const StatusIndicator: React.FC = () => {
  const { state } = useAppContext();

  const getApiIcon = () => {
    switch (state.apiStatus) {
      case 'online':
        return <Cloud />;
      case 'offline':
        return <CloudOff />;
      case 'error':
        return <Error />;
      case 'checking':
        return <Sync className="rotating" />;
      default:
        return <Error />;
    }
  };

  const getNetworkIcon = () => {
    return state.networkStatus ? <Wifi /> : <WifiOff />;
  };

  const apiStatusFormatted = formatApiStatus(state.apiStatus);
  const networkStatusFormatted = formatNetworkStatus(state.networkStatus);

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      <Tooltip title={`Network: ${networkStatusFormatted.text}`}>
        <Chip
          icon={getNetworkIcon()}
          label="Network"
          size="small"
          color={networkStatusFormatted.color}
          variant="outlined"
        />
      </Tooltip>
      
      <Tooltip title={`API Server: ${apiStatusFormatted.text}`}>
        <Chip
          icon={getApiIcon()}
          label="API"
          size="small"
          color={apiStatusFormatted.color}
          variant="outlined"
        />
      </Tooltip>
      
      {(!state.networkStatus || state.apiStatus !== 'online') && (
        <Typography variant="caption" color="error">
          Some features may be unavailable
        </Typography>
      )}
    </Box>
  );
};

export default StatusIndicator;