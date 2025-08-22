// Data formatting utilities for the stock scanner application

/**
 * Format a number as currency (USD)
 */
export const formatCurrency = (value: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format a number as a price (without currency symbol)
 */
export const formatPrice = (price: number, decimals: number = 2): string => {
  return price.toFixed(decimals);
};

/**
 * Format a number as a percentage
 */
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format a large number with appropriate suffixes (K, M, B)
 */
export const formatLargeNumber = (value: number, decimals: number = 1): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(decimals)}B`;
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed(decimals)}M`;
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed(decimals)}K`;
  }
  return value.toFixed(decimals);
};

/**
 * Format volume with appropriate suffixes
 */
export const formatVolume = (volume: number): string => {
  return formatLargeNumber(volume, 0);
};

/**
 * Format a date/time string for display
 */
export const formatDateTime = (dateTime: string | Date, options?: Intl.DateTimeFormatOptions): string => {
  const date = typeof dateTime === 'string' ? new Date(dateTime) : dateTime;
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  };
  
  return new Intl.DateTimeFormat('en-US', defaultOptions).format(date);
};

/**
 * Format a date string for display (date only)
 */
export const formatDate = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(dateObj);
};

/**
 * Format a time string for display (time only)
 */
export const formatTime = (time: string | Date): string => {
  const timeObj = typeof time === 'string' ? new Date(time) : time;
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(timeObj);
};

/**
 * Format execution time in seconds
 */
export const formatExecutionTime = (seconds: number): string => {
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(0)}ms`;
  } else if (seconds < 60) {
    return `${seconds.toFixed(2)}s`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }
};

/**
 * Format a duration in milliseconds to human readable format
 */
export const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

/**
 * Format a stock symbol for display
 */
export const formatSymbol = (symbol: string): string => {
  return symbol.toUpperCase();
};

/**
 * Format signal type for display
 */
export const formatSignalType = (signalType: string): string => {
  return signalType.toUpperCase();
};

/**
 * Get color for signal type
 */
export const getSignalColor = (signalType: string): 'success' | 'error' => {
  return signalType.toLowerCase() === 'long' ? 'success' : 'error';
};

/**
 * Get color for P&L values
 */
export const getPnLColor = (value: number): 'success.main' | 'error.main' | 'text.primary' => {
  if (value > 0) return 'success.main';
  if (value < 0) return 'error.main';
  return 'text.primary';
};

/**
 * Format confidence score
 */
export const formatConfidence = (confidence: number): string => {
  return formatPercentage(confidence, 1);
};

/**
 * Format Sharpe ratio
 */
export const formatSharpeRatio = (ratio: number): string => {
  return ratio.toFixed(2);
};

/**
 * Format win rate with color indication
 */
export const formatWinRate = (winRate: number): { text: string; color: string } => {
  const text = formatPercentage(winRate);
  const color = winRate >= 0.5 ? 'success.main' : 'error.main';
  return { text, color };
};

/**
 * Format return value with color indication
 */
export const formatReturn = (returnValue: number): { text: string; color: string } => {
  const text = formatPercentage(returnValue);
  const color = getPnLColor(returnValue);
  return { text, color };
};

/**
 * Format technical indicator values
 */
export const formatIndicator = (value: number, decimals: number = 2): string => {
  return value.toFixed(decimals);
};

/**
 * Format ATR value
 */
export const formatATR = (atr: number): string => {
  return formatIndicator(atr, 3);
};

/**
 * Format EMA value
 */
export const formatEMA = (ema: number): string => {
  return formatIndicator(ema, 2);
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
};

/**
 * Format array of symbols for display
 */
export const formatSymbolList = (symbols: string[], maxDisplay: number = 3): string => {
  const formatted = symbols.map(formatSymbol);
  
  if (formatted.length <= maxDisplay) {
    return formatted.join(', ');
  }
  
  const displayed = formatted.slice(0, maxDisplay);
  const remaining = formatted.length - maxDisplay;
  return `${displayed.join(', ')} +${remaining} more`;
};

/**
 * Format file size for export
 */
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * Format API status for display
 */
export const formatApiStatus = (status: 'online' | 'offline' | 'error' | 'checking'): {
  text: string;
  color: 'success' | 'error' | 'warning' | 'info';
} => {
  switch (status) {
    case 'online':
      return { text: 'Online', color: 'success' };
    case 'offline':
      return { text: 'Offline', color: 'error' };
    case 'error':
      return { text: 'Error', color: 'warning' };
    case 'checking':
      return { text: 'Checking...', color: 'info' };
    default:
      return { text: 'Unknown', color: 'error' };
  }
};

/**
 * Format network status for display
 */
export const formatNetworkStatus = (isOnline: boolean): {
  text: string;
  color: 'success' | 'error';
} => {
  return {
    text: isOnline ? 'Connected' : 'Disconnected',
    color: isOnline ? 'success' : 'error',
  };
};

/**
 * Validate and format stock symbol input
 */
export const validateAndFormatSymbols = (input: string): {
  valid: string[];
  invalid: string[];
  formatted: string;
} => {
  const symbols = input
    .split(',')
    .map(s => s.trim().toUpperCase())
    .filter(s => s.length > 0);
  
  const valid: string[] = [];
  const invalid: string[] = [];
  
  symbols.forEach(symbol => {
    // Basic validation: 1-5 characters, letters only
    if (/^[A-Z]{1,5}$/.test(symbol)) {
      valid.push(symbol);
    } else {
      invalid.push(symbol);
    }
  });
  
  return {
    valid,
    invalid,
    formatted: valid.join(', '),
  };
};

/**
 * Format progress percentage
 */
export const formatProgress = (progress: number): string => {
  return `${Math.round(progress)}%`;
};

/**
 * Format loading message with progress
 */
export const formatLoadingMessage = (message: string, progress?: number): string => {
  if (progress !== undefined) {
    return `${message} (${formatProgress(progress)})`;
  }
  return message;
};