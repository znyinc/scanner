#!/usr/bin/env python3
"""
Test PostgreSQL connection for Stock Scanner.
Run this script to verify your database setup.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test the database connection."""
    print("🔍 Testing PostgreSQL connection...")
    print("-" * 50)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please check your .env file")
        return False
    
    print(f"📍 Database URL: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL!")
            print(f"   Version: {version}")
            
            # Test database access
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"   Database: {db_name}")
            
            # Test user permissions
            result = conn.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"   User: {user}")
            
            # Test UUID extension
            try:
                conn.execute(text("SELECT uuid_generate_v4()"))
                print("✅ UUID extension is available")
            except Exception as e:
                print(f"⚠️  UUID extension not available: {e}")
                print("   Run: CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            
            # Test table creation permissions
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_table (
                        id SERIAL PRIMARY KEY,
                        test_column VARCHAR(50)
                    )
                """))
                conn.execute(text("DROP TABLE IF EXISTS test_table"))
                print("✅ Table creation permissions OK")
            except Exception as e:
                print(f"❌ Table creation failed: {e}")
                return False
            
            conn.commit()
        
        print("-" * 50)
        print("🎉 Database connection test PASSED!")
        print("   You can now run the Stock Scanner application.")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("-" * 50)
        print("🔧 Troubleshooting tips:")
        print("   1. Check if PostgreSQL service is running")
        print("   2. Verify database credentials in .env file")
        print("   3. Ensure database and user exist")
        print("   4. Check firewall/network settings")
        print("   5. Review POSTGRES_SETUP_GUIDE.md for setup instructions")
        return False

def show_env_info():
    """Show current environment configuration."""
    print("📋 Current Environment Configuration:")
    print("-" * 50)
    
    env_vars = [
        'DATABASE_URL',
        'POSTGRES_USER', 
        'POSTGRES_PASSWORD',
        'POSTGRES_DB'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        if 'PASSWORD' in var and value != 'Not set':
            value = '*' * len(value)  # Hide password
        print(f"   {var}: {value}")
    
    print("-" * 50)

if __name__ == "__main__":
    print("🚀 Stock Scanner Database Connection Test")
    print("=" * 50)
    
    show_env_info()
    print()
    
    success = test_connection()
    
    if not success:
        print("\n📖 For setup instructions, see: POSTGRES_SETUP_GUIDE.md")
        sys.exit(1)
    else:
        print("\n🎯 Ready to initialize database schema!")
        print("   Next step: python app/init_db.py")
        sys.exit(0)