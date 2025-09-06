"""
Comparison service for analyzing differences between multiple scans.
Provides side-by-side comparison of settings, performance, and outcomes.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Set
from collections import defaultdict
from sqlalchemy.orm import Session

from ..database import get_session
from ..models.database_models import ScanResultDB
from ..models.enhanced_diagnostics import ScanComparison, EnhancedScanDiagnostics
from ..models.signals import AlgorithmSettings

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing multiple scans and identifying differences."""
    
    def __init__(self):
        """Initialize comparison service."""
        pass
    
    async def compare_scans(self, scan_ids: List[str]) -> Optional[ScanComparison]:
        """
        Compare multiple scans to identify differences and trends.
        
        Args:
            scan_ids: List of scan IDs to compare
            
        Returns:
            ScanComparison with detailed analysis or None if insufficient data
        """
        try:
            db = get_session()
            try:
                # Retrieve scan results
                db_results = db.query(ScanResultDB).filter(
                    ScanResultDB.id.in_(scan_ids)
                ).order_by(ScanResultDB.timestamp).all()
                
                if len(db_results) < 2:
                    logger.warning(f"Insufficient scans found for comparison: {len(db_results)}")
                    return None
                
                # Convert to enhanced diagnostics
                scan_data = {}
                for db_result in db_results:
                    scan_id = str(db_result.id)
                    
                    # Parse settings
                    settings = AlgorithmSettings()
                    if db_result.settings_used:
                        settings = AlgorithmSettings.from_dict(db_result.settings_used)
                    
                    # Parse enhanced diagnostics
                    enhanced_diagnostics = None
                    if db_result.enhanced_diagnostics:
                        enhanced_diagnostics = EnhancedScanDiagnostics.from_dict(
                            db_result.enhanced_diagnostics
                        )
                    
                    scan_data[scan_id] = {
                        'timestamp': db_result.timestamp,
                        'settings': settings,
                        'enhanced_diagnostics': enhanced_diagnostics,
                        'execution_time': float(db_result.execution_time),
                        'data_quality_score': float(db_result.data_quality_score) if db_result.data_quality_score else None,
                        'symbols_scanned': db_result.symbols_scanned or [],
                        'scan_status': db_result.scan_status,
                        'signals_found': len(db_result.signals_found) if db_result.signals_found else 0
                    }
                
                # Perform comparison analysis
                settings_differences = self._analyze_settings_differences(scan_data)
                performance_trends = self._analyze_performance_trends(scan_data)
                symbol_status_changes = self._analyze_symbol_status_changes(scan_data)
                insights = self._generate_insights(scan_data, settings_differences, performance_trends)
                
                comparison = ScanComparison(
                    scan_ids=list(scan_data.keys()),
                    settings_differences=settings_differences,
                    performance_trends=performance_trends,
                    symbol_status_changes=symbol_status_changes,
                    insights=insights
                )
                
                logger.info(f"Generated comparison for {len(scan_ids)} scans")
                return comparison
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error comparing scans: {e}")
            raise
    
    def _analyze_settings_differences(self, scan_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze differences in algorithm settings between scans."""
        settings_differences = {}
        
        # Get baseline settings (first scan)
        scan_ids = list(scan_data.keys())
        baseline_scan_id = scan_ids[0]
        baseline_settings = scan_data[baseline_scan_id]['settings']
        
        for scan_id in scan_ids:
            current_settings = scan_data[scan_id]['settings']
            differences = {}
            
            # Compare each setting
            setting_fields = [
                'atr_multiplier', 'ema5_rising_threshold', 'ema8_rising_threshold',
                'ema21_rising_threshold', 'volatility_filter', 'fomo_filter',
                'higher_timeframe'
            ]
            
            for field in setting_fields:
                baseline_value = getattr(baseline_settings, field, None)
                current_value = getattr(current_settings, field, None)
                
                if baseline_value != current_value:
                    differences[field] = {
                        'baseline': baseline_value,
                        'current': current_value,
                        'change': self._calculate_change(baseline_value, current_value)
                    }
            
            if differences:
                settings_differences[scan_id] = differences
        
        return settings_differences
    
    def _analyze_performance_trends(self, scan_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Analyze performance trends across scans."""
        trends = {
            'execution_time': [],
            'data_quality_score': [],
            'symbols_scanned_count': [],
            'signals_found_count': [],
            'success_rate': [],
            'memory_usage': [],
            'api_requests': []
        }
        
        # Sort scans by timestamp
        sorted_scans = sorted(
            scan_data.items(), 
            key=lambda x: x[1]['timestamp']
        )
        
        for scan_id, data in sorted_scans:
            trends['execution_time'].append(data['execution_time'])
            trends['data_quality_score'].append(data['data_quality_score'] or 0.0)
            trends['symbols_scanned_count'].append(len(data['symbols_scanned']))
            trends['signals_found_count'].append(data['signals_found'])
            
            # Calculate success rate from enhanced diagnostics
            success_rate = 0.0
            if data['enhanced_diagnostics']:
                total_symbols = len(data['symbols_scanned'])
                successful_symbols = len(data['enhanced_diagnostics'].symbols_with_data)
                success_rate = successful_symbols / total_symbols if total_symbols > 0 else 0.0
            
            trends['success_rate'].append(success_rate)
            
            # Extract performance metrics if available
            if data['enhanced_diagnostics'] and data['enhanced_diagnostics'].performance_metrics:
                perf_metrics = data['enhanced_diagnostics'].performance_metrics
                trends['memory_usage'].append(perf_metrics.memory_usage_mb)
                trends['api_requests'].append(perf_metrics.api_requests_made)
            else:
                trends['memory_usage'].append(0.0)
                trends['api_requests'].append(0)
        
        return trends
    
    def _analyze_symbol_status_changes(self, scan_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Analyze how symbol processing status changed between scans."""
        symbol_status_changes = {}
        
        # Collect all symbols across all scans
        all_symbols: Set[str] = set()
        for data in scan_data.values():
            all_symbols.update(data['symbols_scanned'])
        
        # Track status for each symbol across scans
        for symbol in all_symbols:
            symbol_statuses = {}
            
            for scan_id, data in scan_data.items():
                if symbol in data['symbols_scanned']:
                    # Determine status from enhanced diagnostics
                    status = "unknown"
                    if data['enhanced_diagnostics'] and data['enhanced_diagnostics'].symbol_details:
                        symbol_detail = data['enhanced_diagnostics'].symbol_details.get(symbol)
                        if symbol_detail:
                            status = symbol_detail.status
                    elif data['enhanced_diagnostics']:
                        # Fallback to legacy diagnostic format
                        if symbol in data['enhanced_diagnostics'].symbols_with_data:
                            status = "success"
                        elif symbol in data['enhanced_diagnostics'].symbols_without_data:
                            status = "no_data"
                        elif symbol in data['enhanced_diagnostics'].symbols_with_errors:
                            status = "error"
                    
                    symbol_statuses[scan_id] = status
                else:
                    symbol_statuses[scan_id] = "not_scanned"
            
            # Only include symbols that had status changes
            unique_statuses = set(symbol_statuses.values())
            if len(unique_statuses) > 1:
                symbol_status_changes[symbol] = symbol_statuses
        
        return symbol_status_changes
    
    def _generate_insights(
        self, 
        scan_data: Dict[str, Any], 
        settings_differences: Dict[str, Dict[str, Any]],
        performance_trends: Dict[str, List[float]]
    ) -> List[str]:
        """Generate insights about significant differences and trends."""
        insights = []
        
        # Analyze execution time trends
        execution_times = performance_trends['execution_time']
        if len(execution_times) >= 2:
            time_change = ((execution_times[-1] - execution_times[0]) / execution_times[0]) * 100
            if abs(time_change) > 20:  # More than 20% change
                direction = "increased" if time_change > 0 else "decreased"
                insights.append(
                    f"Execution time {direction} by {abs(time_change):.1f}% "
                    f"from {execution_times[0]:.2f}s to {execution_times[-1]:.2f}s"
                )
        
        # Analyze quality score trends
        quality_scores = [score for score in performance_trends['data_quality_score'] if score > 0]
        if len(quality_scores) >= 2:
            quality_change = ((quality_scores[-1] - quality_scores[0]) / quality_scores[0]) * 100
            if abs(quality_change) > 10:  # More than 10% change
                direction = "improved" if quality_change > 0 else "degraded"
                insights.append(
                    f"Data quality {direction} by {abs(quality_change):.1f}% "
                    f"from {quality_scores[0]:.2f} to {quality_scores[-1]:.2f}"
                )
        
        # Analyze settings impact
        if settings_differences:
            changed_settings = set()
            for scan_diffs in settings_differences.values():
                changed_settings.update(scan_diffs.keys())
            
            if changed_settings:
                insights.append(
                    f"Algorithm settings changed: {', '.join(changed_settings)}"
                )
        
        # Analyze signal generation trends
        signals_counts = performance_trends['signals_found_count']
        if len(signals_counts) >= 2:
            if signals_counts[-1] > signals_counts[0] * 1.5:
                insights.append(
                    f"Signal generation increased significantly from {signals_counts[0]} to {signals_counts[-1]}"
                )
            elif signals_counts[-1] < signals_counts[0] * 0.5:
                insights.append(
                    f"Signal generation decreased significantly from {signals_counts[0]} to {signals_counts[-1]}"
                )
        
        # Analyze success rate trends
        success_rates = performance_trends['success_rate']
        if len(success_rates) >= 2:
            success_change = (success_rates[-1] - success_rates[0]) * 100
            if abs(success_change) > 15:  # More than 15% change
                direction = "improved" if success_change > 0 else "degraded"
                insights.append(
                    f"Symbol processing success rate {direction} by {abs(success_change):.1f}% "
                    f"from {success_rates[0]:.1%} to {success_rates[-1]:.1%}"
                )
        
        # Analyze memory usage trends
        memory_usage = [mem for mem in performance_trends['memory_usage'] if mem > 0]
        if len(memory_usage) >= 2:
            memory_change = ((memory_usage[-1] - memory_usage[0]) / memory_usage[0]) * 100
            if abs(memory_change) > 30:  # More than 30% change
                direction = "increased" if memory_change > 0 else "decreased"
                insights.append(
                    f"Memory usage {direction} by {abs(memory_change):.1f}% "
                    f"from {memory_usage[0]:.1f}MB to {memory_usage[-1]:.1f}MB"
                )
        
        # Add general insights if no specific trends found
        if not insights:
            insights.append("No significant trends or changes detected between scans")
        
        return insights
    
    def _calculate_change(self, baseline_value: Any, current_value: Any) -> Optional[str]:
        """Calculate the change between two values."""
        if baseline_value is None or current_value is None:
            return None
        
        if isinstance(baseline_value, (int, float)) and isinstance(current_value, (int, float)):
            if baseline_value == 0:
                return "new_value" if current_value != 0 else "no_change"
            
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
            if abs(change_percent) < 0.01:  # Less than 0.01% change
                return "no_change"
            
            direction = "+" if change_percent > 0 else ""
            return f"{direction}{change_percent:.2f}%"
        
        elif baseline_value != current_value:
            return f"changed_from_{baseline_value}_to_{current_value}"
        
        return "no_change"