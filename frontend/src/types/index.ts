// Core data types for the stock scanner application

export interface MarketData {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicators {
  ema5: number;
  ema8: number;
  ema13: number;
  ema21: number;
  ema50: number;
  atr: number;
  atr_long_line: number;
  atr_short_line: number;
}

export interface Signal {
  symbol: string;
  signal_type: 'long' | 'short';
  timestamp: string;
  price: number;
  indicators: TechnicalIndicators;
  confidence: number;
}

export interface AlgorithmSettings {
  atr_multiplier: number;
  ema5_rising_threshold: number;
  ema8_rising_threshold: number;
  ema21_rising_threshold: number;
  volatility_filter: number;
  fomo_filter: number;
  higher_timeframe: string;
}

export interface ScanDiagnostics {
  symbols_with_data: string[];
  symbols_without_data: string[];
  symbols_with_errors: Record<string, string>;
  data_fetch_time: number;
  algorithm_time: number;
  total_data_points: Record<string, number>;
  error_summary: Record<string, number>;
}

export interface ScanResult {
  id: string;
  timestamp: string;
  symbols_scanned: string[];
  signals_found: Signal[];
  settings_used: AlgorithmSettings;
  execution_time: number;
  scan_status?: string;
  error_message?: string;
  diagnostics?: ScanDiagnostics;
}

export interface Trade {
  symbol: string;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  trade_type: 'long' | 'short';
  pnl: number;
  pnl_percent: number;
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_return: number;
  average_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

export interface BacktestResult {
  id: string;
  timestamp: string;
  start_date: string;
  end_date: string;
  symbols: string[];
  trades: Trade[];
  performance: PerformanceMetrics;
  settings_used: AlgorithmSettings;
}

export interface HistoryFilters {
  start_date?: string;
  end_date?: string;
  signal_type?: 'long' | 'short' | 'all';
  symbol?: string;
}

// Error handling types
export type ErrorCategory = 
  | 'validation'
  | 'api_error'
  | 'network'
  | 'database'
  | 'algorithm'
  | 'system'
  | 'user_input'
  | 'rate_limit'
  | 'timeout'
  | 'authentication'
  | 'permission';

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface ApiError {
  code: string;
  message: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  recovery_suggestions: string[];
  timestamp?: string;
  request_id?: string;
  technical_details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

// UI State types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  error?: ApiError;
  retryCount?: number;
}

export interface NotificationMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  variant?: 'primary' | 'secondary';
}

// Enhanced diagnostic types for the new diagnostic UI components
export interface SymbolDiagnostic {
  symbol: string;
  status: 'success' | 'no_data' | 'insufficient_data' | 'error';
  data_points_1m: number;
  data_points_15m: number;
  timeframe_coverage: Record<string, boolean>;
  error_message?: string;
  fetch_time: number;
  processing_time: number;
}

export interface PerformanceMetrics {
  memory_usage_mb: number;
  api_requests_made: number;
  api_rate_limit_remaining: number;
  cache_hit_rate: number;
  concurrent_requests: number;
  bottleneck_phase?: string;
}

export interface SignalAnalysis {
  signals_found: number;
  symbols_meeting_partial_criteria: Record<string, string[]>;
  rejection_reasons: Record<string, string[]>;
  confidence_distribution: Record<string, number>;
}

export interface DataQualityMetrics {
  total_data_points: number;
  success_rate: number;
  average_fetch_time: number;
  data_completeness: number;
  quality_score: number;
}

export interface EnhancedScanDiagnostics extends ScanDiagnostics {
  symbol_details: Record<string, SymbolDiagnostic>;
  performance_metrics: PerformanceMetrics;
  signal_analysis: SignalAnalysis;
  data_quality_metrics: DataQualityMetrics;
  settings_snapshot: AlgorithmSettings;
}

export interface EnhancedScanResult extends ScanResult {
  diagnostics?: EnhancedScanDiagnostics;
}