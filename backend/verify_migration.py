"""
Verify that the enhanced diagnostics migration was successful.
"""
import sys
import os
from sqlalchemy import create_engine, text

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_database_url


def verify_migration():
    """Verify that the migration was successful."""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # Check for new columns
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'scan_results' 
                AND column_name IN ('enhanced_diagnostics', 'performance_metrics', 'signal_analysis', 'data_quality_score')
                ORDER BY column_name;
            """)).fetchall()
            
            print("✅ Enhanced diagnostics columns found:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
            
            # Check for indexes
            index_result = connection.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'scan_results' 
                AND indexname LIKE 'idx_scan_results_%diagnostics%' 
                OR indexname LIKE 'idx_scan_results_%quality%'
                OR indexname LIKE 'idx_scan_results_%performance%'
                OR indexname LIKE 'idx_scan_results_%signal%'
                ORDER BY indexname;
            """)).fetchall()
            
            print("\n✅ Enhanced diagnostics indexes found:")
            for row in index_result:
                print(f"  - {row[0]}")
            
            if len(result) == 4:
                print("\n🎉 Migration verification successful! All enhanced diagnostic columns are present.")
            else:
                print(f"\n❌ Migration verification failed! Expected 4 columns, found {len(result)}.")
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verify_migration()