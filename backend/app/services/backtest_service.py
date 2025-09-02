"""
Backtest service for historical analysis of trading algorithms.
Implements backtesting engine with trade simulation and performance metrics calculation.
"""

import logging
import time
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from ..database import get_session
from ..models.database_models import BacktestResultDB, TradeDB
from ..models.results import BacktestResult, Trade, PerformanceMetrics
from ..models.signals import Signal, AlgorithmSettings
from ..models.market_data import MarketData
from .data_service import DataService
from .algorithm_engine import AlgorithmEngine

logger = logging.getLogger(__name__)


@dataclass
class BacktestFilters:
    """Filters for backtest history retrieval."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    symbols: Optional[List[str]] = None
    min_trades: Optional[int] = None
    min_win_rate: Optional[float] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


@dataclass
class TradeSimulation:
    """Configuration for trade simulation."""
    entry_delay_minutes: int = 1  # Delay after signal before entry
    exit_strategy: str = "next_opposite_signal"  # or "fixed_time", "stop_loss"
    stop_loss_percent: Optional[float] = None
    take_profit_percent: Optional[float] = None
    max_hold_days: Optional[int] = None
    commission_per_trade: float = 0.0  # Commission cost per trade


class BacktestService:
    """Service for running historical backtests and performance analysis."""
    
    def __init__(self, data_service: Optional[DataService] = None, 
                 algorithm_engine: Optional[AlgorithmEngine] = None,
                 max_workers: int = 3):
        """
        Initialize backtest service.
        
        Args:
            data_service: Data service instance (creates new if None)
            algorithm_engine: Algorithm engine instance (creates new if None)
            max_workers: Maximum number of worker threads
        """
        self.data_service = data_service or DataService()
        self.algorithm_engine = algorithm_engine or AlgorithmEngine()
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_backtest(self, symbols: List[str], start_date: date, end_date: date,
                          settings: Optional[AlgorithmSettings] = None,
                          simulation_config: Optional[TradeSimulation] = None) -> BacktestResult:
        """
        Run a backtest on historical data.
        
        Args:
            symbols: List of stock symbols to backtest
            start_date: Start date for backtest period
            end_date: End date for backtest period
            settings: Algorithm settings (uses defaults if None)
            simulation_config: Trade simulation configuration
            
        Returns:
            BacktestResult with trades and performance metrics
        """
        if not symbols:
            raise ValueError("No symbols provided for backtesting")
        
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        if settings is None:
            settings = AlgorithmSettings()
        
        if simulation_config is None:
            simulation_config = TradeSimulation()
        
        start_time = time.time()
        backtest_id = str(uuid.uuid4())
        
        logger.info(f"Starting backtest {backtest_id} for {len(symbols)} symbols "
                   f"from {start_date} to {end_date}")
        
        # Clean and validate symbols
        valid_symbols = [s.strip().upper() for s in symbols if s and s.strip()]
        if not valid_symbols:
            raise ValueError("No valid symbols provided")
        
        all_trades = []
        
        try:
            # Fetch historical data for all symbols
            logger.info("Fetching historical data...")
            historical_data = await self.data_service.fetch_historical_data(
                valid_symbols, start_date, end_date, interval="1d"
            )
            
            # Also fetch higher timeframe data if needed
            htf_data = {}
            if settings.higher_timeframe != "1d":
                htf_data = await self.data_service.fetch_historical_data(
                    valid_symbols, start_date, end_date, interval=settings.higher_timeframe
                )
            
            # Run backtest for each symbol
            for symbol in valid_symbols:
                symbol_data = historical_data.get(symbol, [])
                symbol_htf_data = htf_data.get(symbol, [])
                
                if symbol_data is None or (hasattr(symbol_data, 'empty') and symbol_data.empty):
                    logger.warning(f"No historical data available for {symbol}")
                    continue
                
                if len(symbol_data) < 50:
                    logger.warning(f"Insufficient data for {symbol}: {len(symbol_data)} points")
                    continue
                
                # Run backtest for this symbol
                symbol_trades = await self._backtest_symbol(
                    symbol, symbol_data, symbol_htf_data, settings, simulation_config
                )
                
                all_trades.extend(symbol_trades)
                logger.info(f"Generated {len(symbol_trades)} trades for {symbol}")
            
            # Calculate performance metrics
            performance = self.calculate_performance_metrics(all_trades)
            
            execution_time = time.time() - start_time
            
            logger.info(f"Backtest completed: {len(all_trades)} total trades, "
                       f"win rate: {performance.win_rate:.2%}, "
                       f"total return: {performance.total_return:.2%} "
                       f"in {execution_time:.2f}s")
            
            # Create backtest result
            backtest_result = BacktestResult(
                id=backtest_id,
                timestamp=datetime.now(),
                start_date=start_date,
                end_date=end_date,
                symbols=valid_symbols,
                trades=all_trades,
                performance=performance,
                settings_used=settings
            )
            
            # Persist backtest result to database
            await self._save_backtest_result(backtest_result)
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"Error during backtest {backtest_id}: {str(e)}")
            raise e
    
    async def _backtest_symbol(self, symbol: str, historical_data: List[MarketData],
                              htf_data: List[MarketData], settings: AlgorithmSettings,
                              simulation_config: TradeSimulation) -> List[Trade]:
        """
        Run backtest for a single symbol.
        
        Args:
            symbol: Stock symbol
            historical_data: Historical market data
            htf_data: Higher timeframe data
            settings: Algorithm settings
            simulation_config: Trade simulation configuration
            
        Returns:
            List of trades generated for this symbol
        """
        trades = []
        current_position = None  # Track open position
        
        # Create HTF data lookup for faster access
        htf_lookup = {data.timestamp.date(): data for data in htf_data} if htf_data else {}
        
        # Process each day in historical data
        for i in range(50, len(historical_data)):  # Start after enough data for indicators
            current_data = historical_data[i]
            historical_slice = historical_data[:i]
            
            # Get corresponding HTF data
            htf_current = htf_lookup.get(current_data.timestamp.date())
            htf_historical = [data for data in htf_data 
                            if data.timestamp.date() < current_data.timestamp.date()] if htf_data else []
            
            try:
                # Generate signals for current data point
                signals = self.algorithm_engine.generate_signals(
                    market_data=current_data,
                    historical_data=historical_slice,
                    htf_market_data=htf_current,
                    htf_historical_data=htf_historical,
                    settings=settings
                )
                
                # Process signals
                for signal in signals:
                    # Check if we should close existing position
                    if current_position:
                        should_close = self._should_close_position(
                            current_position, signal, current_data, simulation_config
                        )
                        
                        if should_close:
                            # Close position
                            trade = self._close_position(
                                current_position, current_data, simulation_config
                            )
                            trades.append(trade)
                            current_position = None
                    
                    # Check if we should open new position
                    if not current_position and self._should_open_position(signal, current_data):
                        current_position = self._open_position(signal, current_data, simulation_config)
                
                # Check for position timeout or stop loss
                if current_position:
                    should_close_timeout = self._should_close_position_timeout(
                        current_position, current_data, simulation_config
                    )
                    
                    if should_close_timeout:
                        trade = self._close_position(current_position, current_data, simulation_config)
                        trades.append(trade)
                        current_position = None
                        
            except Exception as e:
                logger.error(f"Error processing {symbol} on {current_data.timestamp}: {e}")
                continue
        
        # Close any remaining open position at the end
        if current_position:
            final_data = historical_data[-1]
            trade = self._close_position(current_position, final_data, simulation_config)
            trades.append(trade)
        
        return trades
    
    def _should_open_position(self, signal: Signal, current_data: MarketData) -> bool:
        """
        Determine if we should open a new position based on signal.
        
        Args:
            signal: Trading signal
            current_data: Current market data
            
        Returns:
            True if position should be opened
        """
        # Basic validation - signal should be for current symbol and have good confidence
        return (signal.symbol == current_data.symbol and 
                signal.confidence >= 0.5 and
                signal.signal_type in ['long', 'short'])
    
    def _should_close_position(self, position: Dict[str, Any], signal: Signal, 
                              current_data: MarketData, simulation_config: TradeSimulation) -> bool:
        """
        Determine if we should close current position based on new signal.
        
        Args:
            position: Current open position
            signal: New trading signal
            current_data: Current market data
            simulation_config: Trade simulation configuration
            
        Returns:
            True if position should be closed
        """
        # Close on opposite signal
        if (position['trade_type'] == 'long' and signal.signal_type == 'short') or \
           (position['trade_type'] == 'short' and signal.signal_type == 'long'):
            return True
        
        # Check stop loss
        if simulation_config.stop_loss_percent:
            current_price = current_data.close
            entry_price = position['entry_price']
            
            if position['trade_type'] == 'long':
                loss_percent = (entry_price - current_price) / entry_price
                if loss_percent >= simulation_config.stop_loss_percent:
                    return True
            else:  # short
                loss_percent = (current_price - entry_price) / entry_price
                if loss_percent >= simulation_config.stop_loss_percent:
                    return True
        
        # Check take profit
        if simulation_config.take_profit_percent:
            current_price = current_data.close
            entry_price = position['entry_price']
            
            if position['trade_type'] == 'long':
                profit_percent = (current_price - entry_price) / entry_price
                if profit_percent >= simulation_config.take_profit_percent:
                    return True
            else:  # short
                profit_percent = (entry_price - current_price) / entry_price
                if profit_percent >= simulation_config.take_profit_percent:
                    return True
        
        return False
    
    def _should_close_position_timeout(self, position: Dict[str, Any], current_data: MarketData,
                                     simulation_config: TradeSimulation) -> bool:
        """
        Check if position should be closed due to timeout.
        
        Args:
            position: Current open position
            current_data: Current market data
            simulation_config: Trade simulation configuration
            
        Returns:
            True if position should be closed due to timeout
        """
        if not simulation_config.max_hold_days:
            return False
        
        entry_date = position['entry_date']
        days_held = (current_data.timestamp - entry_date).days
        
        return days_held >= simulation_config.max_hold_days
    
    def _open_position(self, signal: Signal, current_data: MarketData,
                      simulation_config: TradeSimulation) -> Dict[str, Any]:
        """
        Open a new trading position.
        
        Args:
            signal: Trading signal
            current_data: Current market data
            simulation_config: Trade simulation configuration
            
        Returns:
            Position dictionary
        """
        # Simulate entry delay
        entry_time = current_data.timestamp + timedelta(minutes=simulation_config.entry_delay_minutes)
        
        return {
            'symbol': signal.symbol,
            'trade_type': signal.signal_type,
            'entry_date': entry_time,
            'entry_price': current_data.close,  # Simplified - use close price
            'signal_confidence': signal.confidence
        }
    
    def _close_position(self, position: Dict[str, Any], current_data: MarketData,
                       simulation_config: TradeSimulation) -> Trade:
        """
        Close an open trading position.
        
        Args:
            position: Open position to close
            current_data: Current market data
            simulation_config: Trade simulation configuration
            
        Returns:
            Completed Trade object
        """
        exit_price = current_data.close
        entry_price = position['entry_price']
        
        # Calculate P&L
        if position['trade_type'] == 'long':
            pnl = exit_price - entry_price
            pnl_percent = (exit_price - entry_price) / entry_price
        else:  # short
            pnl = entry_price - exit_price
            pnl_percent = (entry_price - exit_price) / entry_price
        
        # Subtract commission
        pnl -= simulation_config.commission_per_trade
        
        return Trade(
            symbol=position['symbol'],
            entry_date=position['entry_date'],
            entry_price=entry_price,
            exit_date=current_data.timestamp,
            exit_price=exit_price,
            trade_type=position['trade_type'],
            pnl=pnl,
            pnl_percent=pnl_percent
        )   

    def calculate_performance_metrics(self, trades: List[Trade]) -> PerformanceMetrics:
        """
        Calculate performance metrics from a list of trades.
        
        Args:
            trades: List of completed trades
            
        Returns:
            PerformanceMetrics object with calculated statistics
        """
        if not trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_return=0.0,
                average_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0
            )
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl <= 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate returns
        returns = [t.pnl_percent for t in trades]
        total_return = sum(returns)
        average_return = total_return / total_trades if total_trades > 0 else 0.0
        
        # Calculate maximum drawdown
        max_drawdown = self._calculate_max_drawdown(trades)
        
        # Calculate Sharpe ratio (simplified - assumes risk-free rate of 0)
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            average_return=average_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio
        )
    
    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """
        Calculate maximum drawdown from trades.
        
        Args:
            trades: List of trades sorted by date
            
        Returns:
            Maximum drawdown as a percentage
        """
        if not trades:
            return 0.0
        
        # Sort trades by exit date
        sorted_trades = sorted(trades, key=lambda t: t.exit_date)
        
        # Calculate cumulative returns
        cumulative_return = 0.0
        peak_return = 0.0
        max_drawdown = 0.0
        
        for trade in sorted_trades:
            cumulative_return += trade.pnl_percent
            
            # Update peak
            if cumulative_return > peak_return:
                peak_return = cumulative_return
            
            # Calculate current drawdown
            current_drawdown = peak_return - cumulative_return
            
            # Update max drawdown
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """
        Calculate Sharpe ratio from returns.
        
        Args:
            returns: List of trade returns
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        import statistics
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0.0
        
        # Simplified Sharpe ratio (assuming risk-free rate = 0)
        return mean_return / std_return
    
    async def _save_backtest_result(self, backtest_result: BacktestResult) -> None:
        """
        Save backtest result to database.
        
        Args:
            backtest_result: Backtest result to save
        """
        try:
            db = get_session()
            try:
                # Convert to database model
                db_backtest_result = BacktestResultDB(
                    id=uuid.UUID(backtest_result.id),
                    timestamp=backtest_result.timestamp,
                    start_date=backtest_result.start_date,
                    end_date=backtest_result.end_date,
                    symbols=backtest_result.symbols,
                    trades=[trade.to_dict() for trade in backtest_result.trades],
                    performance=backtest_result.performance.to_dict(),
                    settings_used=backtest_result.settings_used.to_dict()
                )
                
                db.add(db_backtest_result)
                
                # Also save individual trades for detailed analysis
                for trade in backtest_result.trades:
                    db_trade = TradeDB(
                        backtest_id=uuid.UUID(backtest_result.id),
                        symbol=trade.symbol,
                        entry_date=trade.entry_date,
                        entry_price=float(trade.entry_price),
                        exit_date=trade.exit_date,
                        exit_price=float(trade.exit_price),
                        trade_type=trade.trade_type,
                        pnl=float(trade.pnl),
                        pnl_percent=float(trade.pnl_percent)
                    )
                    db.add(db_trade)
                
                db.commit()
                
                logger.info(f"Saved backtest result {backtest_result.id} with {len(backtest_result.trades)} trades")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving backtest result {backtest_result.id}: {str(e)}")
            raise
    
    async def get_backtest_history(self, filters: Optional[BacktestFilters] = None) -> List[BacktestResult]:
        """
        Retrieve backtest history with optional filtering.
        
        Args:
            filters: Optional filters for backtest history
            
        Returns:
            List of backtest results matching filters
        """
        if filters is None:
            filters = BacktestFilters()
        
        try:
            db = get_session()
            try:
                # Build query with filters
                query = db.query(BacktestResultDB)
                
                # Date range filter
                if filters.start_date:
                    query = query.filter(BacktestResultDB.start_date >= filters.start_date)
                if filters.end_date:
                    query = query.filter(BacktestResultDB.end_date <= filters.end_date)
                
                # Symbol filter
                if filters.symbols:
                    symbol_conditions = []
                    for symbol in filters.symbols:
                        symbol_conditions.append(
                            BacktestResultDB.symbols.op('@>')([symbol])
                        )
                    query = query.filter(or_(*symbol_conditions))
                
                # Order by timestamp descending
                query = query.order_by(desc(BacktestResultDB.timestamp))
                
                # Apply pagination
                if filters.offset:
                    query = query.offset(filters.offset)
                if filters.limit:
                    query = query.limit(filters.limit)
                
                # Execute query
                db_results = query.all()
                
                # Convert to domain models
                backtest_results = []
                for db_result in db_results:
                    # Convert trades from dict to Trade objects
                    trades = [Trade.from_dict(trade_dict) for trade_dict in db_result.trades]
                    
                    # Apply additional filters that require domain model processing
                    if filters.min_trades and len(trades) < filters.min_trades:
                        continue
                    
                    # Calculate performance for filtering
                    performance = PerformanceMetrics.from_dict(db_result.performance)
                    
                    if filters.min_win_rate and performance.win_rate < filters.min_win_rate:
                        continue
                    
                    # Create backtest result
                    backtest_result = BacktestResult(
                        id=str(db_result.id),
                        timestamp=db_result.timestamp,
                        start_date=db_result.start_date,
                        end_date=db_result.end_date,
                        symbols=db_result.symbols,
                        trades=trades,
                        performance=performance,
                        settings_used=AlgorithmSettings.from_dict(db_result.settings_used)
                    )
                    
                    backtest_results.append(backtest_result)
                
                logger.info(f"Retrieved {len(backtest_results)} backtest results from history")
                return backtest_results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving backtest history: {str(e)}")
            raise
    
    async def get_backtest_by_id(self, backtest_id: str) -> Optional[BacktestResult]:
        """
        Retrieve a specific backtest result by ID.
        
        Args:
            backtest_id: Backtest result ID
            
        Returns:
            Backtest result if found, None otherwise
        """
        try:
            db = get_session()
            try:
                db_result = db.query(BacktestResultDB).filter(
                    BacktestResultDB.id == uuid.UUID(backtest_id)
                ).first()
                
                if not db_result:
                    return None
                
                # Convert to domain model
                trades = [Trade.from_dict(trade_dict) for trade_dict in db_result.trades]
                performance = PerformanceMetrics.from_dict(db_result.performance)
                
                backtest_result = BacktestResult(
                    id=str(db_result.id),
                    timestamp=db_result.timestamp,
                    start_date=db_result.start_date,
                    end_date=db_result.end_date,
                    symbols=db_result.symbols,
                    trades=trades,
                    performance=performance,
                    settings_used=AlgorithmSettings.from_dict(db_result.settings_used)
                )
                
                return backtest_result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving backtest {backtest_id}: {str(e)}")
            return None
    
    async def delete_backtest(self, backtest_id: str) -> bool:
        """
        Delete a backtest result from the database.
        
        Args:
            backtest_id: Backtest result ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            db = get_session()
            try:
                result = db.query(BacktestResultDB).filter(
                    BacktestResultDB.id == uuid.UUID(backtest_id)
                ).delete()
                
                db.commit()
                
                if result > 0:
                    logger.info(f"Deleted backtest result {backtest_id}")
                    return True
                else:
                    logger.warning(f"Backtest result {backtest_id} not found for deletion")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error deleting backtest {backtest_id}: {str(e)}")
            return False
    
    async def get_backtest_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get backtesting statistics for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with backtest statistics
        """
        try:
            db = get_session()
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Get all backtests in the time period
                backtests = db.query(BacktestResultDB).filter(
                    BacktestResultDB.timestamp >= cutoff_date
                ).all()
                
                if not backtests:
                    return {
                        "total_backtests": 0,
                        "total_trades": 0,
                        "average_win_rate": 0.0,
                        "average_return": 0.0,
                        "best_performing_symbols": [],
                        "most_tested_symbols": []
                    }
                
                # Calculate statistics
                total_backtests = len(backtests)
                total_trades = sum(len(bt.trades) for bt in backtests)
                
                # Calculate average metrics
                win_rates = []
                returns = []
                symbol_counts = {}
                symbol_performance = {}
                
                for backtest in backtests:
                    try:
                        performance = PerformanceMetrics.from_dict(backtest.performance)
                        win_rates.append(performance.win_rate)
                        returns.append(performance.total_return)
                    except Exception as e:
                        logger.warning(f"Error parsing performance data for backtest {backtest.id}: {str(e)}")
                        # Skip this backtest if performance data is invalid
                        continue
                    
                    # Count symbol usage
                    for symbol in backtest.symbols:
                        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
                        
                        # Track symbol performance
                        if symbol not in symbol_performance:
                            symbol_performance[symbol] = []
                        symbol_performance[symbol].append(performance.total_return)
                
                avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
                avg_return = sum(returns) / len(returns) if returns else 0.0
                
                # Get most tested symbols (top 10)
                most_tested = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Get best performing symbols (top 10 by average return)
                best_performing = []
                for symbol, performances in symbol_performance.items():
                    avg_perf = sum(performances) / len(performances)
                    best_performing.append((symbol, avg_perf, len(performances)))
                
                best_performing = sorted(best_performing, key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    "total_backtests": total_backtests,
                    "total_trades": total_trades,
                    "average_win_rate": round(avg_win_rate, 4),
                    "average_return": round(avg_return, 4),
                    "best_performing_symbols": [
                        {"symbol": symbol, "avg_return": round(perf, 4), "tests": count}
                        for symbol, perf, count in best_performing
                    ],
                    "most_tested_symbols": [
                        {"symbol": symbol, "count": count}
                        for symbol, count in most_tested
                    ]
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting backtest statistics: {str(e)}")
            return {}
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)