"""
Scanner service for real-time stock scanning.
Combines data fetching and algorithm evaluation with batch processing and persistence.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from ..database import get_session
from ..models.database_models import ScanResultDB
from ..models.results import ScanResult, ScanDiagnostics
from ..models.enhanced_diagnostics import EnhancedScanDiagnostics, EnhancedScanResult
from ..models.signals import Signal, AlgorithmSettings
from ..models.market_data import MarketData
from .data_service import DataService
from .algorithm_engine import AlgorithmEngine
from .diagnostic_service import DiagnosticService

logger = logging.getLogger(__name__)


@dataclass
class ScanFilters:
    """Filters for scan history retrieval."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    symbols: Optional[List[str]] = None
    signal_types: Optional[List[str]] = None  # ['long', 'short']
    min_confidence: Optional[float] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


@dataclass
class ScanStats:
    """Statistics for scan execution."""
    total_symbols: int
    symbols_processed: int
    symbols_failed: int
    signals_found: int
    execution_time: float
    data_fetch_time: float
    algorithm_time: float


class ScannerService:
    """Service for real-time stock scanning with batch processing and persistence."""
    
    def __init__(self, data_service: Optional[DataService] = None, 
                 algorithm_engine: Optional[AlgorithmEngine] = None,
                 diagnostic_service: Optional[DiagnosticService] = None,
                 max_workers: int = 5):
        """
        Initialize scanner service.
        
        Args:
            data_service: Data service instance (creates new if None)
            algorithm_engine: Algorithm engine instance (creates new if None)
            diagnostic_service: Diagnostic service instance (creates new if None)
            max_workers: Maximum number of worker threads for batch processing
        """
        self.data_service = data_service or DataService()
        self.algorithm_engine = algorithm_engine or AlgorithmEngine()
        self.diagnostic_service = diagnostic_service or DiagnosticService()
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def scan_stocks(self, symbols: List[str], 
                         settings: Optional[AlgorithmSettings] = None,
                         enable_enhanced_diagnostics: bool = True) -> ScanResult:
        """
        Scan multiple stocks for trading signals.
        
        Args:
            symbols: List of stock symbols to scan
            settings: Algorithm settings (uses defaults if None)
            enable_enhanced_diagnostics: Whether to collect enhanced diagnostics
            
        Returns:
            ScanResult with found signals and execution statistics
        """
        if not symbols:
            raise ValueError("No symbols provided for scanning")
        
        if settings is None:
            settings = AlgorithmSettings()
        
        start_time = time.time()
        scan_id = str(uuid.uuid4())
        
        logger.info(f"Starting scan {scan_id} for {len(symbols)} symbols")
        
        # Clean and validate symbols
        valid_symbols = [s.strip().upper() for s in symbols if s and s.strip()]
        if not valid_symbols:
            raise ValueError("No valid symbols provided")
        
        # Initialize enhanced diagnostics if enabled
        diagnostic_context = None
        if enable_enhanced_diagnostics:
            diagnostic_context = self.diagnostic_service.start_scan_diagnostics(
                scan_id, settings, len(valid_symbols)
            )
        
        # Initialize scan statistics
        stats = ScanStats(
            total_symbols=len(valid_symbols),
            symbols_processed=0,
            symbols_failed=0,
            signals_found=0,
            execution_time=0.0,
            data_fetch_time=0.0,
            algorithm_time=0.0
        )
        
        all_signals = []
        
        # Initialize diagnostics tracking (legacy format)
        symbols_with_data = []
        symbols_without_data = []
        symbols_with_errors = {}
        total_data_points = {}
        error_summary = {}
        scan_status = "completed"
        error_message = None
        
        try:
            # Record data fetch phase start
            if diagnostic_context:
                self.diagnostic_service.record_data_fetch_start(scan_id, valid_symbols)
            
            # Fetch current market data for all symbols
            data_fetch_start = time.time()
            
            try:
                current_data = await self._fetch_data_with_diagnostics(
                    valid_symbols, period="3mo", interval="1h", scan_id=scan_id
                )
            except Exception as e:
                logger.error(f"Error fetching current data: {e}")
                current_data = {}
                error_summary["data_fetch_error"] = error_summary.get("data_fetch_error", 0) + 1
            
            try:
                # Fetch higher timeframe data
                htf_data = await self._fetch_htf_data_with_diagnostics(
                    valid_symbols, timeframe=settings.higher_timeframe, 
                    period="3mo", scan_id=scan_id
                )
            except Exception as e:
                logger.error(f"Error fetching HTF data: {e}")
                htf_data = {}
                error_summary["htf_fetch_error"] = error_summary.get("htf_fetch_error", 0) + 1
            
            stats.data_fetch_time = time.time() - data_fetch_start
            
            # Record data fetch phase timing
            if diagnostic_context:
                self.diagnostic_service.record_phase_timing(scan_id, "data_fetch", stats.data_fetch_time)
            
            logger.info(f"Data fetch completed in {stats.data_fetch_time:.2f}s")
            
            # Analyze data availability
            for symbol in valid_symbols:
                symbol_data = current_data.get(symbol, [])
                if symbol_data:
                    symbols_with_data.append(symbol)
                    total_data_points[symbol] = len(symbol_data)
                    logger.info(f"Symbol {symbol}: {len(symbol_data)} data points available")
                else:
                    symbols_without_data.append(symbol)
                    total_data_points[symbol] = 0
                    logger.warning(f"Symbol {symbol}: No data available")
            
            # Process symbols in batches for algorithm evaluation
            algorithm_start = time.time()
            
            # Use thread pool for CPU-intensive algorithm processing
            futures = []
            for symbol in valid_symbols:
                if diagnostic_context:
                    self.diagnostic_service.record_concurrent_request_start(scan_id)
                
                future = self._executor.submit(
                    self._process_single_symbol_with_diagnostics,
                    symbol,
                    current_data.get(symbol, []),
                    htf_data.get(symbol, []),
                    settings,
                    scan_id if diagnostic_context else None
                )
                futures.append((symbol, future))
            
            # Collect results as they complete
            for symbol, future in futures:
                try:
                    if diagnostic_context:
                        self.diagnostic_service.record_concurrent_request_end(scan_id)
                    
                    result = future.result(timeout=30)  # 30 second timeout per symbol
                    
                    if isinstance(result, dict):
                        # Enhanced result with diagnostics
                        signals = result.get('signals', [])
                        rejection_reasons = result.get('rejection_reasons', [])
                        partial_criteria = result.get('partial_criteria', [])
                        
                        if diagnostic_context:
                            self.diagnostic_service.record_symbol_processing_result(
                                scan_id, symbol, signals, rejection_reasons, partial_criteria
                            )
                    else:
                        # Legacy result format
                        signals = result if result else []
                    
                    if signals:
                        all_signals.extend(signals)
                        stats.signals_found += len(signals)
                        logger.info(f"Found {len(signals)} signals for {symbol}")
                    else:
                        logger.info(f"No signals found for {symbol}")
                    
                    stats.symbols_processed += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing {symbol}: {error_msg}")
                    symbols_with_errors[symbol] = error_msg
                    stats.symbols_failed += 1
                    
                    if diagnostic_context:
                        self.diagnostic_service.record_concurrent_request_end(scan_id)
                    
                    # Categorize error types
                    if "insufficient data" in error_msg.lower():
                        error_summary["insufficient_data"] = error_summary.get("insufficient_data", 0) + 1
                    elif "timeout" in error_msg.lower():
                        error_summary["timeout"] = error_summary.get("timeout", 0) + 1
                    else:
                        error_summary["algorithm_error"] = error_summary.get("algorithm_error", 0) + 1
            
            stats.algorithm_time = time.time() - algorithm_start
            stats.execution_time = time.time() - start_time
            
            # Record algorithm phase timing
            if diagnostic_context:
                self.diagnostic_service.record_phase_timing(scan_id, "algorithm_processing", stats.algorithm_time)
            
            # Determine scan status
            if stats.symbols_failed == 0:
                scan_status = "completed"
            elif stats.symbols_processed > 0:
                scan_status = "partial"
            else:
                scan_status = "failed"
                error_message = f"All {stats.total_symbols} symbols failed to process"
            
            logger.info(f"Scan {scan_status}: {stats.symbols_processed}/{stats.total_symbols} symbols processed, "
                       f"{stats.signals_found} signals found in {stats.execution_time:.2f}s")
            
            # Finalize enhanced diagnostics
            enhanced_diagnostics = None
            data_quality_score = None
            if diagnostic_context:
                enhanced_diagnostics = self.diagnostic_service.finalize_scan_diagnostics(scan_id)
                if enhanced_diagnostics:
                    data_quality_score = enhanced_diagnostics.data_quality_metrics.quality_score
            
            # Create detailed diagnostics (legacy format for compatibility)
            diagnostics = ScanDiagnostics(
                symbols_with_data=symbols_with_data,
                symbols_without_data=symbols_without_data,
                symbols_with_errors=symbols_with_errors,
                data_fetch_time=stats.data_fetch_time,
                algorithm_time=stats.algorithm_time,
                total_data_points=total_data_points,
                error_summary=error_summary
            )
            
            # Create scan result with enhanced diagnostics
            if enhanced_diagnostics:
                scan_result = EnhancedScanResult(
                    id=scan_id,
                    timestamp=datetime.now(),
                    symbols_scanned=valid_symbols,
                    signals_found=all_signals,
                    settings_used=settings,
                    execution_time=stats.execution_time,
                    enhanced_diagnostics=enhanced_diagnostics,
                    scan_status=scan_status,
                    error_message=error_message,
                    data_quality_score=data_quality_score
                )
            else:
                # Fallback to legacy format
                scan_result = ScanResult(
                    id=scan_id,
                    timestamp=datetime.now(),
                    symbols_scanned=valid_symbols,
                    signals_found=all_signals,
                    settings_used=settings,
                    execution_time=stats.execution_time,
                    diagnostics=diagnostics,
                    scan_status=scan_status,
                    error_message=error_message
                )
            
            # Persist scan result to database
            await self._save_scan_result(scan_result)
            
            return scan_result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Critical error during scan {scan_id}: {error_msg}")
            stats.execution_time = time.time() - start_time
            
            # Create diagnostics for failed scan
            diagnostics = ScanDiagnostics(
                symbols_with_data=symbols_with_data,
                symbols_without_data=symbols_without_data,
                symbols_with_errors=symbols_with_errors,
                data_fetch_time=stats.data_fetch_time,
                algorithm_time=stats.algorithm_time,
                total_data_points=total_data_points,
                error_summary=error_summary
            )
            
            # Create scan result even for failed scans
            scan_result = ScanResult(
                id=scan_id,
                timestamp=datetime.now(),
                symbols_scanned=valid_symbols,
                signals_found=all_signals,
                settings_used=settings,
                execution_time=stats.execution_time,
                diagnostics=diagnostics,
                scan_status="failed",
                error_message=error_msg
            )
            
            # Try to save partial results
            try:
                await self._save_scan_result(scan_result)
                logger.info(f"Saved failed scan result {scan_id} with diagnostics")
            except Exception as save_error:
                logger.error(f"Failed to save scan result: {str(save_error)}")
            
            raise e
    
    async def _fetch_data_with_diagnostics(self, symbols: List[str], period: str, 
                                          interval: str, scan_id: str) -> Dict[str, List[MarketData]]:
        """Fetch current data with diagnostic tracking."""
        result = {}
        
        for symbol in symbols:
            fetch_start = time.time()
            error = None
            
            try:
                # Record API request
                self.diagnostic_service.record_api_request(scan_id)
                
                # Fetch data for symbol
                symbol_data = await self.data_service.fetch_current_data(
                    [symbol], period=period, interval=interval
                )
                
                data = symbol_data.get(symbol, [])
                result[symbol] = data
                
                fetch_time = time.time() - fetch_start
                
                # Record fetch result
                self.diagnostic_service.record_symbol_fetch_result(
                    scan_id, symbol, data, [], fetch_time, error
                )
                
            except Exception as e:
                error = str(e)
                fetch_time = time.time() - fetch_start
                result[symbol] = []
                
                # Record fetch failure
                self.diagnostic_service.record_symbol_fetch_result(
                    scan_id, symbol, [], [], fetch_time, error
                )
        
        return result
    
    async def _fetch_htf_data_with_diagnostics(self, symbols: List[str], timeframe: str,
                                              period: str, scan_id: str) -> Dict[str, List[MarketData]]:
        """Fetch higher timeframe data with diagnostic tracking."""
        result = {}
        
        for symbol in symbols:
            fetch_start = time.time()
            error = None
            
            try:
                # Record API request
                self.diagnostic_service.record_api_request(scan_id)
                
                # Fetch HTF data for symbol
                symbol_data = await self.data_service.fetch_higher_timeframe_data(
                    [symbol], timeframe=timeframe, period=period
                )
                
                data = symbol_data.get(symbol, [])
                result[symbol] = data
                
                fetch_time = time.time() - fetch_start
                
                # Update existing symbol diagnostic with HTF data
                if scan_id in self.diagnostic_service._contexts:
                    context = self.diagnostic_service._contexts[scan_id]
                    if symbol in context.symbol_diagnostics:
                        context.symbol_diagnostics[symbol].data_points_15m = len(data)
                        context.symbol_diagnostics[symbol].timeframe_coverage["15m"] = len(data) > 0
                
            except Exception as e:
                error = str(e)
                result[symbol] = []
                logger.warning(f"HTF data fetch failed for {symbol}: {error}")
        
        return result
    
    def _process_single_symbol_with_diagnostics(self, symbol: str, current_data: List[MarketData], 
                                              htf_data: List[MarketData], settings: AlgorithmSettings,
                                              scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single symbol for signal generation with enhanced diagnostics.
        
        Args:
            symbol: Stock symbol
            current_data: Current timeframe market data
            htf_data: Higher timeframe market data
            settings: Algorithm settings
            scan_id: Scan ID for diagnostic tracking (optional)
            
        Returns:
            Dictionary with signals, rejection reasons, and partial criteria
        """
        try:
            if scan_id:
                self.diagnostic_service.record_symbol_processing_start(scan_id, symbol)
            
            rejection_reasons = []
            partial_criteria = []
            
            if not current_data:
                rejection_reasons.append("No current data available")
                logger.warning(f"No current data available for {symbol}")
                return {
                    'signals': [],
                    'rejection_reasons': rejection_reasons,
                    'partial_criteria': partial_criteria
                }
            
            # Need sufficient historical data for indicators
            if len(current_data) < 50:
                rejection_reasons.append("Insufficient data points")
                logger.warning(f"Insufficient data for {symbol}: {len(current_data)} points")
                return {
                    'signals': [],
                    'rejection_reasons': rejection_reasons,
                    'partial_criteria': partial_criteria
                }
            
            # Get most recent data point
            latest_data = current_data[-1]
            historical_data = current_data[:-1]
            
            # Get HTF data if available
            htf_latest = htf_data[-1] if htf_data else None
            htf_historical = htf_data[:-1] if htf_data and len(htf_data) > 1 else None
            
            if not htf_latest:
                rejection_reasons.append("No higher timeframe data")
            else:
                partial_criteria.append("HTF data available")
            
            # Generate signals using algorithm engine with enhanced feedback
            try:
                signals = self.algorithm_engine.generate_signals(
                    market_data=latest_data,
                    historical_data=historical_data,
                    htf_market_data=htf_latest,
                    htf_historical_data=htf_historical,
                    settings=settings
                )
                
                # Analyze why signals were or weren't generated
                if not signals:
                    # Try to determine rejection reasons by checking individual criteria
                    if hasattr(self.algorithm_engine, 'get_last_analysis'):
                        analysis = self.algorithm_engine.get_last_analysis()
                        if analysis:
                            rejection_reasons.extend(analysis.get('rejection_reasons', []))
                            partial_criteria.extend(analysis.get('partial_criteria', []))
                
                return {
                    'signals': signals,
                    'rejection_reasons': rejection_reasons,
                    'partial_criteria': partial_criteria
                }
                
            except Exception as e:
                rejection_reasons.append(f"Algorithm error: {str(e)}")
                return {
                    'signals': [],
                    'rejection_reasons': rejection_reasons,
                    'partial_criteria': partial_criteria
                }
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {str(e)}")
            return {
                'signals': [],
                'rejection_reasons': [f"Processing error: {str(e)}"],
                'partial_criteria': []
            }
    
    def _process_single_symbol(self, symbol: str, current_data: List[MarketData], 
                              htf_data: List[MarketData], settings: AlgorithmSettings) -> List[Signal]:
        """
        Process a single symbol for signal generation (legacy method).
        
        Args:
            symbol: Stock symbol
            current_data: Current timeframe market data
            htf_data: Higher timeframe market data
            settings: Algorithm settings
            
        Returns:
            List of generated signals
        """
        result = self._process_single_symbol_with_diagnostics(
            symbol, current_data, htf_data, settings, None
        )
        return result.get('signals', [])
    
    async def _save_scan_result(self, scan_result) -> None:
        """
        Save scan result to database.
        
        Args:
            scan_result: Scan result to save (ScanResult or EnhancedScanResult)
        """
        try:
            db = get_session()
            try:
                # Handle both legacy and enhanced scan results
                enhanced_diagnostics_data = None
                performance_metrics_data = None
                signal_analysis_data = None
                data_quality_score = None
                diagnostics_data = None
                
                if isinstance(scan_result, EnhancedScanResult):
                    # Enhanced scan result
                    if scan_result.enhanced_diagnostics:
                        enhanced_diagnostics_data = scan_result.enhanced_diagnostics.to_dict()
                        performance_metrics_data = scan_result.enhanced_diagnostics.performance_metrics.to_dict()
                        signal_analysis_data = scan_result.enhanced_diagnostics.signal_analysis.to_dict()
                    
                    data_quality_score = scan_result.data_quality_score
                    
                    # Create legacy diagnostics for compatibility
                    if scan_result.enhanced_diagnostics:
                        diagnostics_data = {
                            'symbols_with_data': scan_result.enhanced_diagnostics.symbols_with_data,
                            'symbols_without_data': scan_result.enhanced_diagnostics.symbols_without_data,
                            'symbols_with_errors': scan_result.enhanced_diagnostics.symbols_with_errors,
                            'data_fetch_time': scan_result.enhanced_diagnostics.data_fetch_time,
                            'algorithm_time': scan_result.enhanced_diagnostics.algorithm_time,
                            'total_data_points': scan_result.enhanced_diagnostics.total_data_points,
                            'error_summary': scan_result.enhanced_diagnostics.error_summary
                        }
                else:
                    # Legacy scan result
                    diagnostics_data = scan_result.diagnostics.to_dict() if scan_result.diagnostics else None
                
                # Convert to database model
                db_scan_result = ScanResultDB(
                    id=uuid.UUID(scan_result.id),
                    timestamp=scan_result.timestamp,
                    symbols_scanned=scan_result.symbols_scanned,
                    signals_found=[signal.to_dict() for signal in scan_result.signals_found],
                    settings_used=scan_result.settings_used.to_dict(),
                    execution_time=scan_result.execution_time,
                    diagnostics=diagnostics_data,
                    scan_status=scan_result.scan_status,
                    error_message=scan_result.error_message,
                    # Enhanced fields
                    enhanced_diagnostics=enhanced_diagnostics_data,
                    performance_metrics=performance_metrics_data,
                    signal_analysis=signal_analysis_data,
                    data_quality_score=data_quality_score
                )
                
                db.add(db_scan_result)
                db.commit()
                
                logger.info(f"Saved scan result {scan_result.id} to database with enhanced diagnostics")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving scan result {scan_result.id}: {str(e)}")
            raise
    
    async def get_scan_history(self, filters: Optional[ScanFilters] = None) -> List[EnhancedScanResult]:
        """
        Retrieve scan history with optional filtering.
        
        Args:
            filters: Optional filters for scan history
            
        Returns:
            List of scan results matching filters
        """
        if filters is None:
            filters = ScanFilters()
        
        try:
            db = get_session()
            try:
                # Build query with filters
                query = db.query(ScanResultDB)
                
                # Date range filter
                if filters.start_date:
                    query = query.filter(ScanResultDB.timestamp >= filters.start_date)
                if filters.end_date:
                    query = query.filter(ScanResultDB.timestamp <= filters.end_date)
                
                # Symbol filter (check if any scanned symbols match)
                if filters.symbols:
                    symbol_conditions = []
                    for symbol in filters.symbols:
                        symbol_conditions.append(
                            ScanResultDB.symbols_scanned.op('@>')([symbol])
                        )
                    query = query.filter(or_(*symbol_conditions))
                
                # Order by timestamp descending
                query = query.order_by(desc(ScanResultDB.timestamp))
                
                # Apply pagination
                if filters.offset:
                    query = query.offset(filters.offset)
                if filters.limit:
                    query = query.limit(filters.limit)
                
                # Execute query
                db_results = query.all()
                
                # Convert to domain models
                scan_results = []
                for db_result in db_results:
                    # Convert signals from dict to Signal objects
                    signals = [Signal.from_dict(signal_dict) for signal_dict in db_result.signals_found]
                    
                    # Apply additional filters that require domain model processing
                    filtered_signals = signals
                    
                    if filters.signal_types:
                        filtered_signals = [s for s in filtered_signals if s.signal_type in filters.signal_types]
                    
                    if filters.min_confidence is not None:
                        filtered_signals = [s for s in filtered_signals if s.confidence >= filters.min_confidence]
                    
                    # Create enhanced diagnostics if available
                    enhanced_diagnostics = None
                    if hasattr(db_result, 'enhanced_diagnostics') and db_result.enhanced_diagnostics:
                        try:
                            enhanced_diagnostics = EnhancedScanDiagnostics.from_dict(db_result.enhanced_diagnostics)
                        except Exception as e:
                            logger.warning(f"Failed to parse enhanced diagnostics for scan {db_result.id}: {e}")
                    
                    # Create enhanced scan result
                    scan_result = EnhancedScanResult(
                        id=str(db_result.id),
                        timestamp=db_result.timestamp,
                        symbols_scanned=db_result.symbols_scanned,
                        signals_found=filtered_signals,
                        settings_used=AlgorithmSettings.from_dict(db_result.settings_used),
                        execution_time=float(db_result.execution_time),
                        enhanced_diagnostics=enhanced_diagnostics,
                        scan_status=getattr(db_result, 'scan_status', 'completed'),
                        error_message=getattr(db_result, 'error_message', None),
                        data_quality_score=getattr(db_result, 'data_quality_score', None)
                    )
                    
                    scan_results.append(scan_result)
                
                logger.info(f"Retrieved {len(scan_results)} scan results from history")
                return scan_results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving scan history: {str(e)}")
            raise
    
    async def get_scan_by_id(self, scan_id: str) -> Optional[ScanResult]:
        """
        Retrieve a specific scan result by ID.
        
        Args:
            scan_id: Scan result ID
            
        Returns:
            Scan result if found, None otherwise
        """
        try:
            db = get_session()
            try:
                db_result = db.query(ScanResultDB).filter(
                    ScanResultDB.id == uuid.UUID(scan_id)
                ).first()
                
                if not db_result:
                    return None
                
                # Convert to domain model
                signals = [Signal.from_dict(signal_dict) for signal_dict in db_result.signals_found]
                
                scan_result = ScanResult(
                    id=str(db_result.id),
                    timestamp=db_result.timestamp,
                    symbols_scanned=db_result.symbols_scanned,
                    signals_found=signals,
                    settings_used=AlgorithmSettings.from_dict(db_result.settings_used),
                    execution_time=float(db_result.execution_time),
                    diagnostics=ScanDiagnostics.from_dict(db_result.diagnostics) if db_result.diagnostics else None,
                    scan_status=getattr(db_result, 'scan_status', 'completed'),
                    error_message=getattr(db_result, 'error_message', None)
                )
                
                return scan_result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving scan {scan_id}: {str(e)}")
            return None
    
    async def delete_scan(self, scan_id: str) -> bool:
        """
        Delete a scan result from the database.
        
        Args:
            scan_id: Scan result ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            db = get_session()
            try:
                result = db.query(ScanResultDB).filter(
                    ScanResultDB.id == uuid.UUID(scan_id)
                ).delete()
                
                db.commit()
                
                if result > 0:
                    logger.info(f"Deleted scan result {scan_id}")
                    return True
                else:
                    logger.warning(f"Scan result {scan_id} not found for deletion")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error deleting scan {scan_id}: {str(e)}")
            return False
    
    async def get_scan_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get scanning statistics for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with scan statistics
        """
        try:
            db = get_session()
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Get all scans in the time period
                scans = db.query(ScanResultDB).filter(
                    ScanResultDB.timestamp >= cutoff_date
                ).all()
                
                if not scans:
                    return {
                        "total_scans": 0,
                        "total_symbols_scanned": 0,
                        "total_signals_found": 0,
                        "average_execution_time": 0.0,
                        "signals_by_type": {},
                        "most_active_symbols": []
                    }
                
                # Calculate statistics
                total_scans = len(scans)
                total_symbols = sum(len(scan.symbols_scanned) for scan in scans)
                total_signals = sum(len(scan.signals_found) for scan in scans)
                avg_execution_time = sum(float(scan.execution_time) for scan in scans) / total_scans
                
                # Count signals by type
                signal_types = {}
                symbol_counts = {}
                
                for scan in scans:
                    for signal_dict in scan.signals_found:
                        signal_type = signal_dict.get('signal_type', 'unknown')
                        signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
                        
                        symbol = signal_dict.get('symbol', 'unknown')
                        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
                
                # Get most active symbols (top 10)
                most_active = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    "total_scans": total_scans,
                    "total_symbols_scanned": total_symbols,
                    "total_signals_found": total_signals,
                    "average_execution_time": round(avg_execution_time, 3),
                    "signals_by_type": signal_types,
                    "most_active_symbols": [{"symbol": symbol, "count": count} for symbol, count in most_active]
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting scan statistics: {str(e)}")
            return {}
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)