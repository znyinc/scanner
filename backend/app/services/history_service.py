"""
History service for enhanced scan history management.
Provides comprehensive scan history retrieval with filtering, diagnostics, and statistics.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, text
from sqlalchemy.dialects.postgresql import aggregate_order_by

from ..database import get_session
from ..models.database_models import ScanResultDB
from ..models.enhanced_diagnostics import (
    EnhancedScanResult, EnhancedScanDiagnostics, HistoryFilters
)
from ..models.signals import Signal, AlgorithmSettings

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing enhanced scan history operations."""
    
    def __init__(self):
        """Initialize history service."""
        pass
    
    async def get_enhanced_scan_history(
        self, 
        filters: Optional[HistoryFilters] = None,
        include_diagnostics: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[EnhancedScanResult], int]:
        """
        Retrieve enhanced scan history with comprehensive filtering.
        
        Args:
            filters: Optional filters for scan history
            include_diagnostics: Whether to include enhanced diagnostic data
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Tuple of (scan results, total count)
        """
        try:
            db = get_session()
            try:
                # Build base query
                query = db.query(ScanResultDB)
                count_query = db.query(func.count(ScanResultDB.id))
                
                # Apply filters
                if filters:
                    query, count_query = self._apply_filters(query, count_query, filters)
                
                # Get total count before pagination
                total_count = count_query.scalar()
                
                # Apply ordering and pagination
                query = query.order_by(desc(ScanResultDB.timestamp))
                query = query.offset(offset).limit(limit)
                
                # Execute query
                db_results = query.all()
                
                # Convert to domain models
                scan_results = []
                for db_result in db_results:
                    enhanced_result = await self._convert_to_enhanced_scan_result(
                        db_result, include_diagnostics
                    )
                    scan_results.append(enhanced_result)
                
                logger.info(f"Retrieved {len(scan_results)} scan results (total: {total_count})")
                return scan_results, total_count
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving enhanced scan history: {e}")
            raise
    
    async def get_scan_diagnostics(self, scan_id: str) -> Optional[EnhancedScanResult]:
        """
        Get detailed diagnostic information for a specific scan.
        
        Args:
            scan_id: Unique scan identifier
            
        Returns:
            EnhancedScanResult with full diagnostic data or None if not found
        """
        try:
            db = get_session()
            try:
                # Query for specific scan
                db_result = db.query(ScanResultDB).filter(
                    ScanResultDB.id == scan_id
                ).first()
                
                if not db_result:
                    logger.warning(f"Scan {scan_id} not found")
                    return None
                
                # Convert to enhanced scan result with full diagnostics
                enhanced_result = await self._convert_to_enhanced_scan_result(
                    db_result, include_diagnostics=True
                )
                
                logger.info(f"Retrieved detailed diagnostics for scan {scan_id}")
                return enhanced_result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving scan diagnostics for {scan_id}: {e}")
            raise
    
    async def get_scan_statistics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics for scan history.
        
        Args:
            start_date: Optional start date for statistics
            end_date: Optional end date for statistics
            
        Returns:
            Dictionary with comprehensive scan statistics
        """
        try:
            db = get_session()
            try:
                # Build base query for statistics
                query = db.query(ScanResultDB)
                
                # Apply date filters
                if start_date:
                    query = query.filter(ScanResultDB.timestamp >= start_date)
                if end_date:
                    query = query.filter(ScanResultDB.timestamp <= end_date)
                
                # Get basic counts and averages
                basic_stats = query.with_entities(
                    func.count(ScanResultDB.id).label('total_scans'),
                    func.count(func.nullif(ScanResultDB.scan_status, 'failed')).label('successful_scans'),
                    func.avg(ScanResultDB.execution_time).label('avg_execution_time'),
                    func.avg(ScanResultDB.data_quality_score).label('avg_quality_score'),
                    func.min(ScanResultDB.timestamp).label('earliest_scan'),
                    func.max(ScanResultDB.timestamp).label('latest_scan')
                ).first()
                
                # Get status distribution
                status_stats = db.query(
                    ScanResultDB.scan_status,
                    func.count(ScanResultDB.id).label('count')
                ).filter(
                    ScanResultDB.timestamp >= start_date if start_date else True,
                    ScanResultDB.timestamp <= end_date if end_date else True
                ).group_by(ScanResultDB.scan_status).all()
                
                # Get quality score distribution
                quality_distribution = db.query(
                    func.width_bucket(
                        ScanResultDB.data_quality_score, 0, 1, 10
                    ).label('bucket'),
                    func.count(ScanResultDB.id).label('count')
                ).filter(
                    ScanResultDB.data_quality_score.isnot(None),
                    ScanResultDB.timestamp >= start_date if start_date else True,
                    ScanResultDB.timestamp <= end_date if end_date else True
                ).group_by('bucket').all()
                
                # Get execution time trends (daily averages)
                time_trends = db.query(
                    func.date_trunc('day', ScanResultDB.timestamp).label('date'),
                    func.avg(ScanResultDB.execution_time).label('avg_execution_time'),
                    func.avg(ScanResultDB.data_quality_score).label('avg_quality_score'),
                    func.count(ScanResultDB.id).label('scan_count')
                ).filter(
                    ScanResultDB.timestamp >= start_date if start_date else True,
                    ScanResultDB.timestamp <= end_date if end_date else True
                ).group_by(func.date_trunc('day', ScanResultDB.timestamp)).order_by('date').all()
                
                # Calculate success rate
                success_rate = 0.0
                if basic_stats.total_scans and basic_stats.total_scans > 0:
                    success_rate = (basic_stats.successful_scans or 0) / basic_stats.total_scans
                
                # Build statistics response
                statistics = {
                    'summary': {
                        'total_scans': basic_stats.total_scans or 0,
                        'successful_scans': basic_stats.successful_scans or 0,
                        'success_rate': round(success_rate, 4),
                        'avg_execution_time': round(float(basic_stats.avg_execution_time or 0), 3),
                        'avg_quality_score': round(float(basic_stats.avg_quality_score or 0), 3),
                        'earliest_scan': basic_stats.earliest_scan.isoformat() if basic_stats.earliest_scan else None,
                        'latest_scan': basic_stats.latest_scan.isoformat() if basic_stats.latest_scan else None
                    },
                    'status_distribution': {
                        status: count for status, count in status_stats
                    },
                    'quality_score_distribution': {
                        f"bucket_{bucket}": count for bucket, count in quality_distribution
                    },
                    'daily_trends': [
                        {
                            'date': trend.date.isoformat(),
                            'avg_execution_time': round(float(trend.avg_execution_time or 0), 3),
                            'avg_quality_score': round(float(trend.avg_quality_score or 0), 3),
                            'scan_count': trend.scan_count
                        }
                        for trend in time_trends
                    ]
                }
                
                logger.info(f"Generated statistics for {basic_stats.total_scans or 0} scans")
                return statistics
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error generating scan statistics: {e}")
            raise
    
    def _apply_filters(self, query, count_query, filters: HistoryFilters):
        """Apply filters to scan history queries."""
        conditions = []
        
        # Date range filters
        if filters.date_range_start:
            conditions.append(ScanResultDB.timestamp >= filters.date_range_start)
        if filters.date_range_end:
            conditions.append(ScanResultDB.timestamp <= filters.date_range_end)
        
        # Status filter
        if filters.scan_status:
            conditions.append(ScanResultDB.scan_status == filters.scan_status)
        
        # Symbol count filters
        if filters.min_symbols is not None:
            conditions.append(
                func.jsonb_array_length(ScanResultDB.symbols_scanned) >= filters.min_symbols
            )
        if filters.max_symbols is not None:
            conditions.append(
                func.jsonb_array_length(ScanResultDB.symbols_scanned) <= filters.max_symbols
            )
        
        # Execution time filters
        if filters.min_execution_time is not None:
            conditions.append(ScanResultDB.execution_time >= filters.min_execution_time)
        if filters.max_execution_time is not None:
            conditions.append(ScanResultDB.execution_time <= filters.max_execution_time)
        
        # Quality score filters
        if filters.min_quality_score is not None:
            conditions.append(ScanResultDB.data_quality_score >= filters.min_quality_score)
        if filters.max_quality_score is not None:
            conditions.append(ScanResultDB.data_quality_score <= filters.max_quality_score)
        
        # Search text filter (search in symbols, error messages, and settings)
        if filters.search_text:
            search_term = f"%{filters.search_text.lower()}%"
            search_conditions = [
                # Search in symbols
                func.lower(ScanResultDB.symbols_scanned.astext).like(search_term),
                # Search in error messages
                func.lower(ScanResultDB.error_message).like(search_term),
                # Search in settings (convert JSONB to text and search)
                func.lower(ScanResultDB.settings_used.astext).like(search_term)
            ]
            
            # Search in enhanced diagnostics if available
            search_conditions.extend([
                func.lower(ScanResultDB.enhanced_diagnostics.astext).like(search_term)
            ])
            
            conditions.append(or_(*search_conditions))
        
        # Apply all conditions
        if conditions:
            filter_condition = and_(*conditions)
            query = query.filter(filter_condition)
            count_query = count_query.filter(filter_condition)
        
        return query, count_query
    
    async def _convert_to_enhanced_scan_result(
        self, 
        db_result: ScanResultDB, 
        include_diagnostics: bool = True
    ) -> EnhancedScanResult:
        """
        Convert database model to enhanced scan result domain model.
        
        Args:
            db_result: Database scan result
            include_diagnostics: Whether to include enhanced diagnostics
            
        Returns:
            EnhancedScanResult domain model
        """
        try:
            # Convert signals from dict to Signal objects
            signals = []
            if db_result.signals_found:
                for signal_dict in db_result.signals_found:
                    try:
                        signal = Signal.from_dict(signal_dict)
                        signals.append(signal)
                    except Exception as e:
                        logger.warning(f"Error converting signal: {e}")
                        continue
            
            # Convert settings
            settings = AlgorithmSettings()
            if db_result.settings_used:
                try:
                    settings = AlgorithmSettings.from_dict(db_result.settings_used)
                except Exception as e:
                    logger.warning(f"Error converting settings: {e}")
            
            # Convert enhanced diagnostics if available and requested
            enhanced_diagnostics = None
            if include_diagnostics and db_result.enhanced_diagnostics:
                try:
                    # Normalize quality score in the raw data before conversion
                    diag_data = db_result.enhanced_diagnostics.copy()
                    if 'data_quality_metrics' in diag_data and diag_data['data_quality_metrics']:
                        quality_metrics = diag_data['data_quality_metrics']
                        if 'quality_score' in quality_metrics and quality_metrics['quality_score'] is not None:
                            if quality_metrics['quality_score'] > 1.0:
                                quality_metrics['quality_score'] = quality_metrics['quality_score'] / 100.0
                    
                    enhanced_diagnostics = EnhancedScanDiagnostics.from_dict(diag_data)
                except Exception as e:
                    logger.warning(f"Error converting enhanced diagnostics: {e}")
            
            # Create enhanced scan result
            enhanced_result = EnhancedScanResult(
                id=str(db_result.id),
                timestamp=db_result.timestamp,
                symbols_scanned=db_result.symbols_scanned or [],
                signals_found=signals,
                settings_used=settings,
                execution_time=float(db_result.execution_time),
                enhanced_diagnostics=enhanced_diagnostics,
                scan_status=db_result.scan_status or "completed",
                error_message=db_result.error_message,
                data_quality_score=float(db_result.data_quality_score) if db_result.data_quality_score else None
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error converting scan result {db_result.id}: {e}")
            raise