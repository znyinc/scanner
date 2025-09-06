"""
Enhanced diagnostic service for comprehensive scan analysis.
Collects detailed performance metrics, data quality scores, and symbol-level diagnostics.
"""

import logging
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from ..models.enhanced_diagnostics import (
    SymbolDiagnostic, PerformanceMetrics, SignalAnalysis, 
    DataQualityMetrics, EnhancedScanDiagnostics
)
from ..models.signals import AlgorithmSettings, Signal
from ..models.market_data import MarketData

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticContext:
    """Context for collecting diagnostics during scan execution."""
    scan_id: str
    start_time: float
    settings: AlgorithmSettings
    total_symbols: int
    
    # Performance tracking
    memory_start: float
    api_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    concurrent_requests: int = 0
    max_concurrent_requests: int = 0
    
    # Symbol tracking
    symbol_diagnostics: Dict[str, SymbolDiagnostic] = None
    symbol_timings: Dict[str, Dict[str, float]] = None
    
    # Signal analysis
    signals_by_symbol: Dict[str, List[Signal]] = None
    rejection_reasons: Dict[str, List[str]] = None
    partial_criteria: Dict[str, List[str]] = None
    
    # Data quality tracking
    total_data_points: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    fetch_times: List[float] = None
    
    # Error tracking
    error_categories: Dict[str, int] = None
    bottleneck_phases: List[Tuple[str, float]] = None
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.symbol_diagnostics is None:
            self.symbol_diagnostics = {}
        if self.symbol_timings is None:
            self.symbol_timings = {}
        if self.signals_by_symbol is None:
            self.signals_by_symbol = {}
        if self.rejection_reasons is None:
            self.rejection_reasons = defaultdict(list)
        if self.partial_criteria is None:
            self.partial_criteria = {}
        if self.fetch_times is None:
            self.fetch_times = []
        if self.error_categories is None:
            self.error_categories = defaultdict(int)
        if self.bottleneck_phases is None:
            self.bottleneck_phases = []


class DiagnosticService:
    """Service for collecting enhanced diagnostic information during scan execution."""
    
    def __init__(self):
        """Initialize diagnostic service."""
        self._contexts: Dict[str, DiagnosticContext] = {}
        self._lock = threading.Lock()
    
    def start_scan_diagnostics(self, scan_id: str, settings: AlgorithmSettings, 
                              total_symbols: int) -> DiagnosticContext:
        """
        Start collecting diagnostics for a scan.
        
        Args:
            scan_id: Unique scan identifier
            settings: Algorithm settings used for the scan
            total_symbols: Total number of symbols to be scanned
            
        Returns:
            DiagnosticContext for tracking scan progress
        """
        with self._lock:
            # Get initial memory usage
            process = psutil.Process()
            memory_start = process.memory_info().rss / 1024 / 1024  # MB
            
            context = DiagnosticContext(
                scan_id=scan_id,
                start_time=time.time(),
                settings=settings,
                total_symbols=total_symbols,
                memory_start=memory_start
            )
            
            self._contexts[scan_id] = context
            logger.info(f"Started diagnostic collection for scan {scan_id}")
            return context
    
    def record_data_fetch_start(self, scan_id: str, symbols: List[str]) -> None:
        """Record the start of data fetching phase."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        fetch_start = time.time()
        
        # Initialize symbol timings
        for symbol in symbols:
            context.symbol_timings[symbol] = {'fetch_start': fetch_start}
        
        logger.debug(f"Started data fetch for {len(symbols)} symbols in scan {scan_id}")
    
    def record_symbol_fetch_result(self, scan_id: str, symbol: str, 
                                  data_1m: List[MarketData], data_15m: List[MarketData],
                                  fetch_time: float, error: Optional[str] = None) -> None:
        """
        Record the result of fetching data for a single symbol.
        
        Args:
            scan_id: Scan identifier
            symbol: Stock symbol
            data_1m: 1-minute timeframe data (empty if failed)
            data_15m: 15-minute timeframe data (empty if failed)
            fetch_time: Time taken to fetch data
            error: Error message if fetch failed
        """
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        
        # Determine status
        if error:
            status = "error"
        elif not data_1m and not data_15m:
            status = "no_data"
        elif len(data_1m) < 50 or len(data_15m) < 20:  # Insufficient for analysis
            status = "insufficient_data"
        else:
            status = "success"
        
        # Create symbol diagnostic
        symbol_diagnostic = SymbolDiagnostic(
            symbol=symbol,
            status=status,
            data_points_1m=len(data_1m) if data_1m else 0,
            data_points_15m=len(data_15m) if data_15m else 0,
            timeframe_coverage={
                "1m": len(data_1m) > 0,
                "15m": len(data_15m) > 0
            },
            error_message=error,
            fetch_time=fetch_time,
            processing_time=0.0  # Will be updated during processing
        )
        
        context.symbol_diagnostics[symbol] = symbol_diagnostic
        context.fetch_times.append(fetch_time)
        
        # Update counters
        if status == "success":
            context.successful_fetches += 1
            context.total_data_points += len(data_1m) + len(data_15m)
        else:
            context.failed_fetches += 1
            
        # Categorize errors
        if error:
            if "timeout" in error.lower():
                context.error_categories["api_timeout"] += 1
            elif "rate limit" in error.lower():
                context.error_categories["rate_limit"] += 1
            elif "not found" in error.lower() or "invalid" in error.lower():
                context.error_categories["invalid_symbol"] += 1
            elif "market closed" in error.lower():
                context.error_categories["market_closed"] += 1
            else:
                context.error_categories["other_error"] += 1
        
        logger.debug(f"Recorded fetch result for {symbol}: {status}, {fetch_time:.3f}s")
    
    def record_api_request(self, scan_id: str, rate_limit_remaining: Optional[int] = None) -> None:
        """Record an API request for rate limiting tracking."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.api_requests += 1
        
        # Track rate limit if provided
        if rate_limit_remaining is not None:
            # Store the most recent rate limit info
            setattr(context, 'last_rate_limit_remaining', rate_limit_remaining)
    
    def record_cache_hit(self, scan_id: str) -> None:
        """Record a cache hit."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.cache_hits += 1
    
    def record_cache_miss(self, scan_id: str) -> None:
        """Record a cache miss."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.cache_misses += 1
    
    def record_concurrent_request_start(self, scan_id: str) -> None:
        """Record the start of a concurrent request."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.concurrent_requests += 1
        context.max_concurrent_requests = max(
            context.max_concurrent_requests, 
            context.concurrent_requests
        )
    
    def record_concurrent_request_end(self, scan_id: str) -> None:
        """Record the end of a concurrent request."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.concurrent_requests = max(0, context.concurrent_requests - 1)
    
    def record_symbol_processing_start(self, scan_id: str, symbol: str) -> None:
        """Record the start of algorithm processing for a symbol."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        if symbol in context.symbol_timings:
            context.symbol_timings[symbol]['processing_start'] = time.time()
    
    def record_symbol_processing_result(self, scan_id: str, symbol: str, 
                                      signals: List[Signal], 
                                      rejection_reasons: List[str],
                                      partial_criteria: List[str]) -> None:
        """
        Record the result of processing a symbol through the algorithm.
        
        Args:
            scan_id: Scan identifier
            symbol: Stock symbol
            signals: Generated signals (empty if none)
            rejection_reasons: Reasons why signals were rejected
            partial_criteria: Criteria that were met but not sufficient for signal
        """
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        
        # Update processing time
        if (symbol in context.symbol_timings and 
            'processing_start' in context.symbol_timings[symbol]):
            processing_time = time.time() - context.symbol_timings[symbol]['processing_start']
            if symbol in context.symbol_diagnostics:
                context.symbol_diagnostics[symbol].processing_time = processing_time
        
        # Record signals
        if signals:
            context.signals_by_symbol[symbol] = signals
        
        # Record rejection reasons
        for reason in rejection_reasons:
            context.rejection_reasons[reason].append(symbol)
        
        # Record partial criteria
        if partial_criteria:
            context.partial_criteria[symbol] = partial_criteria
        
        logger.debug(f"Recorded processing result for {symbol}: "
                    f"{len(signals)} signals, {len(rejection_reasons)} rejections")
    
    def record_phase_timing(self, scan_id: str, phase_name: str, duration: float) -> None:
        """Record timing for a specific phase of the scan."""
        if scan_id not in self._contexts:
            return
        
        context = self._contexts[scan_id]
        context.bottleneck_phases.append((phase_name, duration))
        
        logger.debug(f"Recorded phase timing for {phase_name}: {duration:.3f}s")
    
    def calculate_data_quality_score(self, context: DiagnosticContext) -> float:
        """
        Calculate an overall data quality score (0-100).
        
        Args:
            context: Diagnostic context
            
        Returns:
            Quality score from 0 to 100
        """
        if context.total_symbols == 0:
            return 0.0
        
        # Success rate (40% weight)
        success_rate = context.successful_fetches / context.total_symbols
        success_score = success_rate * 40
        
        # Data completeness (30% weight)
        total_expected_points = context.total_symbols * 100  # Assume 100 points per symbol ideal
        completeness = min(1.0, context.total_data_points / total_expected_points) if total_expected_points > 0 else 0
        completeness_score = completeness * 30
        
        # Fetch performance (20% weight)
        if context.fetch_times:
            avg_fetch_time = sum(context.fetch_times) / len(context.fetch_times)
            # Good performance is under 2 seconds per symbol
            performance_ratio = max(0, min(1.0, (3.0 - avg_fetch_time) / 3.0))
            performance_score = performance_ratio * 20
        else:
            performance_score = 0
        
        # Error rate (10% weight)
        error_rate = context.failed_fetches / context.total_symbols
        error_score = (1.0 - error_rate) * 10
        
        total_score = success_score + completeness_score + performance_score + error_score
        return round(total_score, 2)
    
    def finalize_scan_diagnostics(self, scan_id: str) -> Optional[EnhancedScanDiagnostics]:
        """
        Finalize and return comprehensive diagnostics for a completed scan.
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            EnhancedScanDiagnostics object or None if scan not found
        """
        if scan_id not in self._contexts:
            logger.warning(f"No diagnostic context found for scan {scan_id}")
            return None
        
        context = self._contexts[scan_id]
        
        try:
            # Calculate final metrics
            end_time = time.time()
            total_execution_time = end_time - context.start_time
            
            # Get current memory usage
            try:
                process = psutil.Process()
                memory_current = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = memory_current - context.memory_start
            except Exception as e:
                logger.warning(f"Could not get memory usage: {e}")
                memory_usage = 0.0
            
            # Calculate cache hit rate
            total_cache_requests = context.cache_hits + context.cache_misses
            cache_hit_rate = (context.cache_hits / total_cache_requests) if total_cache_requests > 0 else 0.0
            
            # Identify bottleneck phase
            bottleneck_phase = None
            if context.bottleneck_phases:
                bottleneck_phase = max(context.bottleneck_phases, key=lambda x: x[1])[0]
            
            # Create performance metrics
            performance_metrics = PerformanceMetrics(
                memory_usage_mb=memory_usage,
                api_requests_made=context.api_requests,
                api_rate_limit_remaining=getattr(context, 'last_rate_limit_remaining', 0),
                cache_hit_rate=cache_hit_rate,
                concurrent_requests=context.max_concurrent_requests,
                bottleneck_phase=bottleneck_phase
            )
            
            # Create signal analysis
            total_signals = sum(len(signals) for signals in context.signals_by_symbol.values())
            
            # Calculate confidence distribution
            confidence_distribution = {"high": 0, "medium": 0, "low": 0}
            for signals in context.signals_by_symbol.values():
                for signal in signals:
                    if signal.confidence >= 0.8:
                        confidence_distribution["high"] += 1
                    elif signal.confidence >= 0.6:
                        confidence_distribution["medium"] += 1
                    else:
                        confidence_distribution["low"] += 1
            
            signal_analysis = SignalAnalysis(
                signals_found=total_signals,
                symbols_meeting_partial_criteria=dict(context.partial_criteria),
                rejection_reasons=dict(context.rejection_reasons),
                confidence_distribution=confidence_distribution
            )
            
            # Calculate data quality metrics
            avg_fetch_time = (sum(context.fetch_times) / len(context.fetch_times)) if context.fetch_times else 0.0
            success_rate = context.successful_fetches / context.total_symbols if context.total_symbols > 0 else 0.0
            data_completeness = min(1.0, context.total_data_points / (context.total_symbols * 100)) if context.total_symbols > 0 else 0.0
            quality_score = self.calculate_data_quality_score(context)
            
            data_quality_metrics = DataQualityMetrics(
                total_data_points=context.total_data_points,
                success_rate=success_rate,
                average_fetch_time=avg_fetch_time,
                data_completeness=data_completeness,
                quality_score=quality_score
            )
            
            # Prepare legacy format data for compatibility
            symbols_with_data = [
                symbol for symbol, diag in context.symbol_diagnostics.items()
                if diag.status == "success"
            ]
            symbols_without_data = [
                symbol for symbol, diag in context.symbol_diagnostics.items()
                if diag.status == "no_data"
            ]
            symbols_with_errors = {
                symbol: diag.error_message for symbol, diag in context.symbol_diagnostics.items()
                if diag.status == "error" and diag.error_message
            }
            total_data_points_legacy = {
                symbol: diag.data_points_1m + diag.data_points_15m
                for symbol, diag in context.symbol_diagnostics.items()
            }
            
            # Calculate phase timings
            data_fetch_time = sum(context.fetch_times) if context.fetch_times else 0.0
            algorithm_time = sum(
                diag.processing_time for diag in context.symbol_diagnostics.values()
            )
            
            # Create enhanced diagnostics
            enhanced_diagnostics = EnhancedScanDiagnostics(
                # Legacy fields
                symbols_with_data=symbols_with_data,
                symbols_without_data=symbols_without_data,
                symbols_with_errors=symbols_with_errors,
                data_fetch_time=data_fetch_time,
                algorithm_time=algorithm_time,
                total_data_points=total_data_points_legacy,
                error_summary=dict(context.error_categories),
                
                # Enhanced fields
                symbol_details=context.symbol_diagnostics,
                performance_metrics=performance_metrics,
                signal_analysis=signal_analysis,
                data_quality_metrics=data_quality_metrics,
                settings_snapshot=context.settings
            )
            
            logger.info(f"Finalized diagnostics for scan {scan_id}: "
                       f"Quality score: {quality_score}, "
                       f"Success rate: {success_rate:.2%}, "
                       f"Signals found: {total_signals}")
            
            return enhanced_diagnostics
            
        except Exception as e:
            logger.error(f"Error finalizing diagnostics for scan {scan_id}: {e}")
            return None
        
        finally:
            # Clean up context
            with self._lock:
                if scan_id in self._contexts:
                    del self._contexts[scan_id]
    
    def get_active_scans(self) -> List[str]:
        """Get list of currently active scan IDs."""
        with self._lock:
            return list(self._contexts.keys())
    
    def cleanup_scan(self, scan_id: str) -> None:
        """Clean up diagnostic context for a scan."""
        with self._lock:
            if scan_id in self._contexts:
                del self._contexts[scan_id]
                logger.debug(f"Cleaned up diagnostic context for scan {scan_id}")