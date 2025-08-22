"""
SQLAlchemy database models for PostgreSQL storage.
"""
from sqlalchemy import Column, String, DateTime, Date, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


class ScanResultDB(Base):
    """Database model for scan results."""
    __tablename__ = "scan_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    symbols_scanned = Column(JSONB, nullable=False)
    signals_found = Column(JSONB, nullable=False)
    settings_used = Column(JSONB, nullable=False)
    execution_time = Column(Numeric(10, 3), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ScanResult(id={self.id}, timestamp={self.timestamp})>"


class BacktestResultDB(Base):
    """Database model for backtest results."""
    __tablename__ = "backtest_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    symbols = Column(JSONB, nullable=False)
    trades = Column(JSONB, nullable=False)
    performance = Column(JSONB, nullable=False)
    settings_used = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to individual trades
    trade_records = relationship("TradeDB", back_populates="backtest", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BacktestResult(id={self.id}, start_date={self.start_date}, end_date={self.end_date})>"


class TradeDB(Base):
    """Database model for individual trades."""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_results.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Numeric(12, 4), nullable=False)
    exit_date = Column(DateTime(timezone=True))
    exit_price = Column(Numeric(12, 4))
    trade_type = Column(String(10), nullable=False)
    pnl = Column(Numeric(12, 4))
    pnl_percent = Column(Numeric(8, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to backtest result
    backtest = relationship("BacktestResultDB", back_populates="trade_records")

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, type={self.trade_type})>"