#!/usr/bin/env python3
"""
Database migration to add enhanced diagnostics columns to scan_results table.
"""

import logging
import sys
import os
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_session, engine

logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in the specified table."""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False


def add_enhanced_diagnostics_columns():
    """Add enhanced diagnostics columns to scan_results table."""
    db = get_session()
    
    try:
        # Check if enhanced diagnostics columns already exist
        columns_to_add = [
            ('enhanced_diagnostics', 'JSONB'),
            ('performance_metrics', 'JSONB'),
            ('signal_analysis', 'JSONB'),
            ('data_quality_score', 'NUMERIC(5,2)')  # 0.00 to 100.00
        ]
        
        columns_added = []
        
        for column_name, column_type in columns_to_add:
            if not check_column_exists('scan_results', column_name):
                try:
                    sql = f"ALTER TABLE scan_results ADD COLUMN {column_name} {column_type}"
                    db.execute(text(sql))
                    columns_added.append(column_name)
                    logger.info(f"Added column: {column_name}")
                except SQLAlchemyError as e:
                    logger.error(f"Error adding column {column_name}: {e}")
                    raise
            else:
                logger.info(f"Column {column_name} already exists, skipping")
        
        # Add indexes for better query performance
        indexes_to_add = [
            ('idx_scan_results_quality_score', 'data_quality_score'),
            ('idx_scan_results_enhanced_diagnostics', 'enhanced_diagnostics USING GIN'),
            ('idx_scan_results_performance_metrics', 'performance_metrics USING GIN'),
            ('idx_scan_results_signal_analysis', 'signal_analysis USING GIN')
        ]
        
        for index_name, index_definition in indexes_to_add:
            try:
                # Check if index already exists
                inspector = inspect(engine)
                existing_indexes = inspector.get_indexes('scan_results')
                index_exists = any(idx['name'] == index_name for idx in existing_indexes)
                
                if not index_exists:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON scan_results ({index_definition})"
                    db.execute(text(sql))
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index {index_name} already exists, skipping")
                    
            except SQLAlchemyError as e:
                logger.warning(f"Error creating index {index_name}: {e}")
                # Don't fail the migration for index creation errors
        
        # Commit all changes
        db.commit()
        
        if columns_added:
            logger.info(f"Successfully added enhanced diagnostics columns: {', '.join(columns_added)}")
        else:
            logger.info("All enhanced diagnostics columns already exist")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


def verify_migration():
    """Verify that the migration was successful."""
    try:
        required_columns = [
            'enhanced_diagnostics',
            'performance_metrics', 
            'signal_analysis',
            'data_quality_score'
        ]
        
        missing_columns = []
        for column in required_columns:
            if not check_column_exists('scan_results', column):
                missing_columns.append(column)
        
        if missing_columns:
            logger.error(f"Migration verification failed. Missing columns: {missing_columns}")
            return False
        
        logger.info("Migration verification successful. All enhanced diagnostics columns are present.")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration verification: {e}")
        return False


def main():
    """Main migration function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting enhanced diagnostics migration...")
    
    try:
        # Run the migration
        success = add_enhanced_diagnostics_columns()
        
        if success:
            # Verify the migration
            if verify_migration():
                logger.info("Enhanced diagnostics migration completed successfully!")
                return 0
            else:
                logger.error("Migration verification failed!")
                return 1
        else:
            logger.error("Migration failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)