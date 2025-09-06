"""
Export service for generating downloadable scan data files.
Supports CSV, JSON, and Excel formats with comprehensive data inclusion.
"""

import logging
import os
import csv
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
from sqlalchemy.orm import Session

from ..database import get_session
from ..models.database_models import ScanResultDB
from ..models.enhanced_diagnostics import ExportRequest, EnhancedScanDiagnostics
from ..models.signals import Signal, AlgorithmSettings

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation."""
    file_path: str
    record_count: int
    file_size: int
    format: str


class ExportService:
    """Service for exporting scan data in various formats."""
    
    def __init__(self):
        """Initialize export service."""
        pass
    
    async def export_scan_data(self, export_request: ExportRequest) -> ExportResult:
        """
        Export scan data according to the specified request parameters.
        
        Args:
            export_request: Export configuration and filters
            
        Returns:
            ExportResult with file information
        """
        try:
            # Retrieve scan data
            scan_data = await self._retrieve_scan_data(export_request)
            
            if not scan_data:
                raise ValueError("No scan data found matching the export criteria")
            
            # Generate export file based on format
            if export_request.format == "csv":
                file_path = await self._export_to_csv(scan_data, export_request)
            elif export_request.format == "json":
                file_path = await self._export_to_json(scan_data, export_request)
            elif export_request.format == "excel":
                file_path = await self._export_to_excel(scan_data, export_request)
            else:
                raise ValueError(f"Unsupported export format: {export_request.format}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            result = ExportResult(
                file_path=file_path,
                record_count=len(scan_data),
                file_size=file_size,
                format=export_request.format
            )
            
            logger.info(f"Exported {len(scan_data)} scans to {export_request.format} format")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting scan data: {e}")
            raise
    
    async def _retrieve_scan_data(self, export_request: ExportRequest) -> List[Dict[str, Any]]:
        """Retrieve scan data for export based on request parameters."""
        try:
            db = get_session()
            try:
                # Build query
                query = db.query(ScanResultDB).filter(
                    ScanResultDB.id.in_(export_request.scan_ids)
                )
                
                # Apply date range filters if specified
                if export_request.date_range_start:
                    query = query.filter(ScanResultDB.timestamp >= export_request.date_range_start)
                if export_request.date_range_end:
                    query = query.filter(ScanResultDB.timestamp <= export_request.date_range_end)
                
                # Order by timestamp
                query = query.order_by(ScanResultDB.timestamp)
                
                # Execute query
                db_results = query.all()
                
                # Convert to export format
                export_data = []
                for db_result in db_results:
                    scan_record = await self._convert_scan_for_export(db_result, export_request)
                    export_data.append(scan_record)
                
                return export_data
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving scan data for export: {e}")
            raise
    
    async def _convert_scan_for_export(
        self, 
        db_result: ScanResultDB, 
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Convert database scan result to export format."""
        # Base scan information
        scan_record = {
            'scan_id': str(db_result.id),
            'timestamp': db_result.timestamp.isoformat(),
            'scan_status': db_result.scan_status,
            'execution_time': float(db_result.execution_time),
            'symbols_scanned_count': len(db_result.symbols_scanned) if db_result.symbols_scanned else 0,
            'signals_found_count': len(db_result.signals_found) if db_result.signals_found else 0,
            'data_quality_score': float(db_result.data_quality_score) if db_result.data_quality_score else None
        }
        
        # Add error message if present
        if db_result.error_message:
            scan_record['error_message'] = db_result.error_message
        
        # Include symbols if requested
        if export_request.include_symbols and db_result.symbols_scanned:
            scan_record['symbols_scanned'] = db_result.symbols_scanned
            
            # Add signals details
            if db_result.signals_found:
                signals_data = []
                for signal_dict in db_result.signals_found:
                    try:
                        signal = Signal.from_dict(signal_dict)
                        signals_data.append({
                            'symbol': signal.symbol,
                            'signal_type': signal.signal_type,
                            'confidence': signal.confidence,
                            'entry_price': signal.entry_price,
                            'timestamp': signal.timestamp.isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Error converting signal for export: {e}")
                        continue
                
                scan_record['signals_found'] = signals_data
        
        # Include algorithm settings
        if db_result.settings_used:
            try:
                settings = AlgorithmSettings.from_dict(db_result.settings_used)
                scan_record['algorithm_settings'] = {
                    'atr_multiplier': settings.atr_multiplier,
                    'ema5_rising_threshold': settings.ema5_rising_threshold,
                    'ema8_rising_threshold': settings.ema8_rising_threshold,
                    'ema21_rising_threshold': settings.ema21_rising_threshold,
                    'volatility_filter': settings.volatility_filter,
                    'fomo_filter': settings.fomo_filter,
                    'higher_timeframe': settings.higher_timeframe
                }
            except Exception as e:
                logger.warning(f"Error converting settings for export: {e}")
        
        # Include enhanced diagnostics if requested and available
        if export_request.include_diagnostics and db_result.enhanced_diagnostics:
            try:
                enhanced_diag = EnhancedScanDiagnostics.from_dict(db_result.enhanced_diagnostics)
                
                # Basic diagnostic info
                scan_record['diagnostics'] = {
                    'symbols_with_data_count': len(enhanced_diag.symbols_with_data),
                    'symbols_without_data_count': len(enhanced_diag.symbols_without_data),
                    'symbols_with_errors_count': len(enhanced_diag.symbols_with_errors),
                    'data_fetch_time': enhanced_diag.data_fetch_time,
                    'algorithm_time': enhanced_diag.algorithm_time,
                    'total_data_points': sum(enhanced_diag.total_data_points.values())
                }
                
                # Performance metrics
                if enhanced_diag.performance_metrics:
                    scan_record['performance_metrics'] = {
                        'memory_usage_mb': enhanced_diag.performance_metrics.memory_usage_mb,
                        'api_requests_made': enhanced_diag.performance_metrics.api_requests_made,
                        'api_rate_limit_remaining': enhanced_diag.performance_metrics.api_rate_limit_remaining,
                        'cache_hit_rate': enhanced_diag.performance_metrics.cache_hit_rate,
                        'concurrent_requests': enhanced_diag.performance_metrics.concurrent_requests,
                        'bottleneck_phase': enhanced_diag.performance_metrics.bottleneck_phase
                    }
                
                # Signal analysis
                if enhanced_diag.signal_analysis:
                    scan_record['signal_analysis'] = {
                        'signals_found': enhanced_diag.signal_analysis.signals_found,
                        'rejection_reasons_count': len(enhanced_diag.signal_analysis.rejection_reasons),
                        'partial_criteria_count': len(enhanced_diag.signal_analysis.symbols_meeting_partial_criteria)
                    }
                
                # Data quality metrics
                if enhanced_diag.data_quality_metrics:
                    scan_record['data_quality_metrics'] = {
                        'total_data_points': enhanced_diag.data_quality_metrics.total_data_points,
                        'success_rate': enhanced_diag.data_quality_metrics.success_rate,
                        'average_fetch_time': enhanced_diag.data_quality_metrics.average_fetch_time,
                        'data_completeness': enhanced_diag.data_quality_metrics.data_completeness,
                        'quality_score': enhanced_diag.data_quality_metrics.quality_score
                    }
                
            except Exception as e:
                logger.warning(f"Error converting enhanced diagnostics for export: {e}")
        
        # Include error details if requested
        if export_request.include_errors and db_result.enhanced_diagnostics:
            try:
                enhanced_diag = EnhancedScanDiagnostics.from_dict(db_result.enhanced_diagnostics)
                if enhanced_diag.symbols_with_errors:
                    scan_record['error_details'] = enhanced_diag.symbols_with_errors
                if enhanced_diag.error_summary:
                    scan_record['error_summary'] = enhanced_diag.error_summary
            except Exception as e:
                logger.warning(f"Error converting error details for export: {e}")
        
        return scan_record
    
    async def _export_to_csv(self, scan_data: List[Dict[str, Any]], export_request: ExportRequest) -> str:
        """Export scan data to CSV format."""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
        
        try:
            # Flatten nested data for CSV
            flattened_data = []
            for scan in scan_data:
                flat_record = self._flatten_dict(scan)
                flattened_data.append(flat_record)
            
            if not flattened_data:
                raise ValueError("No data to export")
            
            # Get all possible field names
            all_fields = set()
            for record in flattened_data:
                all_fields.update(record.keys())
            
            # Sort fields for consistent output
            fieldnames = sorted(all_fields)
            
            # Write CSV
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    async def _export_to_json(self, scan_data: List[Dict[str, Any]], export_request: ExportRequest) -> str:
        """Export scan data to JSON format."""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        try:
            # Create export structure
            export_structure = {
                'export_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'format': 'json',
                    'record_count': len(scan_data),
                    'include_diagnostics': export_request.include_diagnostics,
                    'include_symbols': export_request.include_symbols,
                    'include_errors': export_request.include_errors
                },
                'scans': scan_data
            }
            
            # Write JSON with proper formatting
            json.dump(export_structure, temp_file, indent=2, default=str)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    async def _export_to_excel(self, scan_data: List[Dict[str, Any]], export_request: ExportRequest) -> str:
        """Export scan data to Excel format with multiple sheets."""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.close()
        
        try:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                # Main scan summary sheet
                summary_data = []
                for scan in scan_data:
                    summary_record = {
                        'Scan ID': scan.get('scan_id'),
                        'Timestamp': scan.get('timestamp'),
                        'Status': scan.get('scan_status'),
                        'Execution Time (s)': scan.get('execution_time'),
                        'Symbols Count': scan.get('symbols_scanned_count'),
                        'Signals Found': scan.get('signals_found_count'),
                        'Quality Score': scan.get('data_quality_score')
                    }
                    summary_data.append(summary_record)
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Scan Summary', index=False)
                
                # Algorithm settings sheet
                if any('algorithm_settings' in scan for scan in scan_data):
                    settings_data = []
                    for scan in scan_data:
                        if 'algorithm_settings' in scan:
                            settings_record = {'Scan ID': scan.get('scan_id')}
                            settings_record.update(scan['algorithm_settings'])
                            settings_data.append(settings_record)
                    
                    if settings_data:
                        settings_df = pd.DataFrame(settings_data)
                        settings_df.to_excel(writer, sheet_name='Algorithm Settings', index=False)
                
                # Performance metrics sheet
                if export_request.include_diagnostics:
                    perf_data = []
                    for scan in scan_data:
                        if 'performance_metrics' in scan:
                            perf_record = {'Scan ID': scan.get('scan_id')}
                            perf_record.update(scan['performance_metrics'])
                            perf_data.append(perf_record)
                    
                    if perf_data:
                        perf_df = pd.DataFrame(perf_data)
                        perf_df.to_excel(writer, sheet_name='Performance Metrics', index=False)
                
                # Signals sheet
                if export_request.include_symbols:
                    signals_data = []
                    for scan in scan_data:
                        scan_id = scan.get('scan_id')
                        if 'signals_found' in scan:
                            for signal in scan['signals_found']:
                                signal_record = {'Scan ID': scan_id}
                                signal_record.update(signal)
                                signals_data.append(signal_record)
                    
                    if signals_data:
                        signals_df = pd.DataFrame(signals_data)
                        signals_df.to_excel(writer, sheet_name='Signals Found', index=False)
                
                # Error details sheet
                if export_request.include_errors:
                    error_data = []
                    for scan in scan_data:
                        scan_id = scan.get('scan_id')
                        if 'error_details' in scan:
                            for symbol, error_msg in scan['error_details'].items():
                                error_record = {
                                    'Scan ID': scan_id,
                                    'Symbol': symbol,
                                    'Error Message': error_msg
                                }
                                error_data.append(error_record)
                    
                    if error_data:
                        error_df = pd.DataFrame(error_data)
                        error_df.to_excel(writer, sheet_name='Error Details', index=False)
            
            return temp_file.name
            
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to comma-separated strings
                if v and isinstance(v[0], dict):
                    # For complex objects, just include count
                    items.append((f"{new_key}_count", len(v)))
                else:
                    # For simple lists, join as string
                    items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    async def cleanup_export_file(self, file_path: str) -> None:
        """Clean up temporary export file."""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up export file: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up export file {file_path}: {e}")