-- PostgreSQL database initialization script for stock scanner
-- This script creates the database schema with PostgreSQL-specific features

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scan results table
CREATE TABLE IF NOT EXISTS scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    symbols_scanned JSONB NOT NULL,
    signals_found JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    execution_time DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backtest results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    symbols JSONB NOT NULL,
    trades JSONB NOT NULL,
    performance JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual trades table (for detailed analysis and indexing)
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_date TIMESTAMPTZ,
    exit_price DECIMAL(12,4),
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('long', 'short')),
    pnl DECIMAL(12,4),
    pnl_percent DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scan_results_timestamp ON scan_results(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_timestamp ON backtest_results(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_date_range ON backtest_results(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_trades_backtest_id ON trades(backtest_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_entry_date ON trades(entry_date);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_scan_results_updated_at BEFORE UPDATE ON scan_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_backtest_results_updated_at BEFORE UPDATE ON backtest_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();