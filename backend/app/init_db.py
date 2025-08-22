"""
Database initialization script using SQLAlchemy.
This script creates all tables and indexes programmatically.
"""
from sqlalchemy import text
from .database import engine, create_tables
from .models.database_models import Base


def init_database():
    """Initialize the database with all tables and indexes."""
    print("Creating database tables...")
    
    # Create all tables defined in SQLAlchemy models
    create_tables()
    
    # Create additional indexes and constraints using raw SQL
    with engine.connect() as conn:
        # Enable UUID extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scan_results_timestamp ON scan_results(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_timestamp ON backtest_results(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_date_range ON backtest_results(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_trades_backtest_id ON trades(backtest_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_entry_date ON trades(entry_date)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                print(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"Index creation failed or already exists: {e}")
        
        # Create function for updating timestamps
        update_function = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
        
        try:
            conn.execute(text(update_function))
            print("Created update_updated_at_column function")
        except Exception as e:
            print(f"Function creation failed: {e}")
        
        # Create triggers
        triggers = [
            """CREATE TRIGGER update_scan_results_updated_at BEFORE UPDATE ON scan_results
               FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()""",
            """CREATE TRIGGER update_backtest_results_updated_at BEFORE UPDATE ON backtest_results
               FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"""
        ]
        
        for trigger_sql in triggers:
            try:
                conn.execute(text(trigger_sql))
                trigger_name = trigger_sql.split()[2]
                print(f"Created trigger: {trigger_name}")
            except Exception as e:
                print(f"Trigger creation failed or already exists: {e}")
        
        conn.commit()
    
    print("Database initialization completed successfully!")


if __name__ == "__main__":
    init_database()