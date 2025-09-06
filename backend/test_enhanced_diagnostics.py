#!/usr/bin/env python3
"""
Test script for enhanced diagnostic collection functionality.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scanner_service import ScannerService
from app.services.diagnostic_service import DiagnosticService
from app.models.signals import AlgorithmSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_enhanced_diagnostics():
    """Test enhanced diagnostic collection during scan execution."""
    
    logger.info("Starting enhanced diagnostics test...")
    
    try:
        # Create scanner service with enhanced diagnostics
        scanner_service = ScannerService()
        
        # Test symbols (mix of valid and invalid for comprehensive testing)
        test_symbols = ["AAPL", "MSFT", "INVALID_SYMBOL", "GOOGL"]
        
        # Create test settings
        settings = AlgorithmSettings(
            atr_multiplier=2.0,
            ema5_rising_threshold=0.001,
            ema8_rising_threshold=0.001,
            ema21_rising_threshold=0.001,
            fomo_filter=3.0,
            volatility_filter=1.5,
            higher_timeframe="4h"
        )
        
        logger.info(f"Testing scan with symbols: {test_symbols}")
        
        # Run scan with enhanced diagnostics enabled
        scan_result = await scanner_service.scan_stocks(
            symbols=test_symbols,
            settings=settings,
            enable_enhanced_diagnostics=True
        )
        
        logger.info(f"Scan completed with ID: {scan_result.id}")
        logger.info(f"Scan status: {scan_result.scan_status}")
        logger.info(f"Symbols processed: {len(scan_result.symbols_scanned)}")
        logger.info(f"Signals found: {len(scan_result.signals_found)}")
        logger.info(f"Execution time: {scan_result.execution_time:.2f}s")
        
        # Check if enhanced diagnostics are present
        if hasattr(scan_result, 'enhanced_diagnostics') and scan_result.enhanced_diagnostics:
            enhanced_diag = scan_result.enhanced_diagnostics
            logger.info("Enhanced diagnostics collected successfully!")
            
            # Display key diagnostic metrics
            logger.info(f"Data quality score: {enhanced_diag.data_quality_metrics.quality_score}")
            logger.info(f"Success rate: {enhanced_diag.data_quality_metrics.success_rate:.2%}")
            logger.info(f"Average fetch time: {enhanced_diag.data_quality_metrics.average_fetch_time:.3f}s")
            logger.info(f"Memory usage: {enhanced_diag.performance_metrics.memory_usage_mb:.1f} MB")
            logger.info(f"API requests made: {enhanced_diag.performance_metrics.api_requests_made}")
            logger.info(f"Cache hit rate: {enhanced_diag.performance_metrics.cache_hit_rate:.2%}")
            
            # Display symbol-level diagnostics
            logger.info("\nSymbol-level diagnostics:")
            for symbol, diag in enhanced_diag.symbol_details.items():
                logger.info(f"  {symbol}: {diag.status} - "
                           f"{diag.data_points_1m} 1m points, "
                           f"{diag.data_points_15m} 15m points, "
                           f"fetch: {diag.fetch_time:.3f}s, "
                           f"processing: {diag.processing_time:.3f}s")
                if diag.error_message:
                    logger.info(f"    Error: {diag.error_message}")
            
            # Display signal analysis
            signal_analysis = enhanced_diag.signal_analysis
            logger.info(f"\nSignal analysis:")
            logger.info(f"  Signals found: {signal_analysis.signals_found}")
            logger.info(f"  Confidence distribution: {signal_analysis.confidence_distribution}")
            
            if signal_analysis.rejection_reasons:
                logger.info("  Rejection reasons:")
                for reason, symbols in signal_analysis.rejection_reasons.items():
                    logger.info(f"    {reason}: {symbols}")
            
            if signal_analysis.symbols_meeting_partial_criteria:
                logger.info("  Partial criteria met:")
                for symbol, criteria in signal_analysis.symbols_meeting_partial_criteria.items():
                    logger.info(f"    {symbol}: {criteria}")
            
            # Display error summary
            if enhanced_diag.error_summary:
                logger.info(f"\nError summary: {enhanced_diag.error_summary}")
            
            logger.info("\n✅ Enhanced diagnostics test completed successfully!")
            return True
            
        else:
            logger.warning("Enhanced diagnostics not found in scan result")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_enhanced_diagnostics()
    
    if success:
        logger.info("All tests passed! ✅")
        return 0
    else:
        logger.error("Tests failed! ❌")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)