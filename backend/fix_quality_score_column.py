#!/usr/bin/env python3
"""
Fix the data_quality_score column to support values 0-100.
"""

import logging
import sys
import os
from sqlalchemy import text

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_session

logger = logging.getLogger(__name__)


def fix_quality_score_column():
    """Fix the data_quality_score column precision."""
    db = get_session()
    
    try:
        # Alter the column to support 0.00 to 100.00
        sql = "ALTER TABLE scan_results ALTER COLUMN data_quality_score TYPE NUMERIC(5,2)"
        db.execute(text(sql))
        db.commit()
        
        logger.info("Successfully updated data_quality_score column to NUMERIC(5,2)")
        return True
        
    except Exception as e:
        logger.error(f"Error updating column: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = fix_quality_score_column()
    sys.exit(0 if success else 1)