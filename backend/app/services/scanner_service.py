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
from ..models.results import ScanResult
from ..models.signals import Signal, AlgorithmSettings
from ..models.market_data import MarketData
from .data_service import DataService
from .algorithm_engine import AlgorithmEngine

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
                 max_workers: int = 5):
        """
        Initialize scanner service.
        
        Args:
            data_service: Data service instance (creates new if None)
            algorithm_engine: Algorithm engine instance (creates new if None)
            max_workers: Maximum number of worker threads for batch processing
        """
        self.data_service = data_service or DataService()
        self.algorithm_engine = algorithm_engine or AlgorithmEngine()
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def scan_stocks(self, symbols: List[str], 
                         settings: Optional[AlgorithmSettings] = None) -> ScanResult:
        """
        Scan multiple stocks for trading signals.
        
        Args:
            symbols: List of stock symbols to scan
            settings: Algorithm settings (uses defaults if None)
            
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
        
        try:
            # Fetch current market data for all symbols
            data_fetch_start = time.time()
            current_data = await self.data_service.fetch_current_data(
                valid_symbols, period="5d", interval="1m"
            )
            
            # Fetch higher timeframe data
            htf_data = await self.data_service.fetch_higher_timeframe_data(
                valid_symbols, timeframe=settings.higher_timeframe, period="5d"
            )
            
            stats.data_fetch_time = time.time() - data_fetch_start
            logger.info(f"Data fetch completed in {stats.data_fetch_time:.2f}s")
            
            # Process symbols in batches for algorithm evaluation
            algorithm_start = time.time()
            
            # Use thread pool for CPU-intensive algorithm processing
            futures = []
            for symbol in valid_symbols:
                future = self._executor.submit(
                    self._process_single_symbol,
                    symbol,
                    current_data.get(symbol, []),
                    htf_data.get(symbol, []),
                    settings
                )
                futures.append((symbol, future))
            
            # Collect results as they complete
            for symbol, future in futures:
                try:
                    signals = future.result(timeout=30)  # 30 second timeout per symbol
                    if signals:
                        all_signals.extend(signals)
                        stats.signals_found += len(signals)
                        logger.debug(f"Found {len(signals)} signals for {symbol}")
                    
                    stats.symbols_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                    stats.symbols_failed += 1
            
            stats.algorithm_time = time.time() - algorithm_start
            stats.execution_time = time.time() - start_time
            
            logger.info(f"Scan completed: {stats.symbols_processed}/{stats.total_symbols} symbols processed, "
                       f"{stats.signals_found} signals found in {stats.execution_time:.2f}s")
            
            # Create scan result
            scan_result = ScanResult(
                id=scan_id,
                timestamp=datetime.now(),
                symbols_scanned=valid_symbols,
                signals_found=all_signals,
                settings_used=settings,
                execution_time=stats.execution_time
            )
            
            # Persist scan result to database
            await self._save_scan_result(scan_result)
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error during scan {scan_id}: {str(e)}")
            stats.execution_time = time.time() - start_time
            
            # Create scan result even for failed scans
            scan_result = ScanResult(
                id=scan_id,
                timestamp=datetime.now(),
                symbols_scanned=valid_symbols,
                signals_found=all_signals,
                settings_used=settings,
                execution_time=stats.execution_time
            )
            
            # Try to save partial results
            try:
                await self._save_scan_result(scan_result)
            except Exception as save_error:
                logger.error(f"Failed to save scan result: {str(save_error)}")
            
            raise e
    
    def _process_single_symbol(self, symbol: str, current_data: List[MarketData], 
                              htf_data: List[MarketData], settings: AlgorithmSettings) -> List[Signal]:
        """
        Process a single symbol for signal generation.
        
        Args:
            symbol: Stock symbol
            current_data: Current timeframe market data
            htf_data: Higher timeframe market data
            settings: Algorithm settings
            
        Returns:
            List of generated signals
        """
        try:
            if not current_data:
                logger.warning(f"No current data available for {symbol}")
                return []
            
            # Need sufficient historical data for indicators
            if len(current_data) < 50:
                logger.warning(f"Insufficient data for {symbol}: {len(current_data)} points")
                return []
            
            # Get most recent data point
            latest_data = current_data[-1]
            historical_data = current_data[:-1]
            
            # Get HTF data if available
            htf_latest = htf_data[-1] if htf_data else None
            htf_historical = htf_data[:-1] if htf_data and len(htf_data) > 1 else None
            
            # Generate signals using algorithm engine
            signals = self.algorithm_engine.generate_signals(
                market_data=latest_data,
                historical_data=historical_data,
                htf_market_data=htf_latest,
                htf_historical_data=htf_historical,
                settings=settings
            )
            
            return signals
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {str(e)}")
            return []
    
    async def _save_scan_result(self, scan_result: ScanResult) -> None:
        """
        Save scan result to database.
        
        Args:
            scan_result: Scan result to save
        """
        try:
            db = get_session()
            try:
                # Convert to database model
                db_scan_result = ScanResultDB(
                    id=uuid.UUID(scan_result.id),
                    timestamp=scan_result.timestamp,
                    symbols_scanned=scan_result.symbols_scanned,
                    signals_found=[signal.to_dict() for signal in scan_result.signals_found],
                    settings_used=scan_result.settings_used.to_dict(),
                    execution_time=scan_result.execution_time
                )
                
                db.add(db_scan_result)
                db.commit()
                
                logger.info(f"Saved scan result {scan_result.id} to database")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving scan result {scan_result.id}: {str(e)}")
            raise
    
    async def get_scan_history(self, filters: Optional[ScanFilters] = None) -> List[ScanResult]:
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
                    
                    # Create scan result
                    scan_result = ScanResult(
                        id=str(db_result.id),
                        timestamp=db_result.timestamp,
                        symbols_scanned=db_result.symbols_scanned,
                        signals_found=filtered_signals,
                        settings_used=AlgorithmSettings.from_dict(db_result.settings_used),
                        execution_time=float(db_result.execution_time)
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
                    execution_time=float(db_result.execution_time)
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