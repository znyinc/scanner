#!/usr/bin/env python3
"""
Database migration to add diagnostics fields to scan_results table.
"""
import sys
import os
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_engine
from app.config import get_settings

def run_migration():
    """Add new columns to scan_results table."""
    settings = get_settings()
    engine = get_engine()
    
    print("Adding diagnostics fields to scan_results table...")
    
    try:
        with engine.connect() as conn:
            # Add new columns
            migration_sql = """
            -- Add diagnostics column (JSONB for detailed scan information)
            ALTER TABLE scan_results 
            ADD COLUMN IF NOT EXISTS diagnostics JSONB;
            
            -- Add scan_status column (completed, failed, partial)
            ALTER TABLE scan_results 
            ADD COLUMN IF NOT EXISTS scan_status VARCHAR(20) DEFAULT 'completed';
            
            -- Add error_message column (for storing error details)
            ALTER TABLE scan_results 
            ADD COLUMN IF NOT EXISTS error_message TEXT;
            
            -- Update existing records to have completed status
            UPDATE scan_results 
            SET scan_status = 'completed' 
            WHERE scan_status IS NULL;
            """
            
            conn.execute(text(migration_sql))
            conn.commit()
            
            print("✅ Migration completed successfully!")
            print("✅ Added diagnostics column (JSONB)")
            print("✅ Added scan_status column (VARCHAR)")
            print("✅ Added error_message column (TEXT)")
            print("✅ Updated existing records")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

def verify_migration():
    """Verify that the migration was successful."""
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'scan_results' 
                AND column_name IN ('diagnostics', 'scan_status', 'error_message')
                ORDER BY column_name;
            """))
            
            columns = result.fetchall()
            
            print(f"\n📊 Verification Results:")
            for column in columns:
                print(f"   ✅ {column[0]} ({column[1]})")
            
            if len(columns) == 3:
                print(f"\n✅ All 3 new columns added successfully!")
                return True
            else:
                print(f"\n❌ Expected 3 columns, found {len(columns)}")
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Run the migration and verification."""
    print("Scan Diagnostics Migration")
    print("=" * 40)
    
    # Run migration
    if run_migration():
        # Verify migration
        if verify_migration():
            print(f"\n🎉 Migration completed successfully!")
            print(f"🎉 Scan results will now include detailed diagnostics")
        else:
            print(f"\n⚠️  Migration completed but verification failed")
    else:
        print(f"\n❌ Migration failed")

if __name__ == "__main__":
    main()