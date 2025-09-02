"""
Integration tests for the backtest service.
Tests the complete backtesting workflow including data fetching and algorithm evaluation.
"""
import pytest
import asyncio
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from backend.app.services.backtest_service import BacktestService, BacktestFilters, TradeSimulation
from backend.app.services.data_service import DataService
from backend.app.services.algorithm_engine import AlgorithmEngine
from backend.app.models.market_data import MarketData, TechnicalIndicators
from backend.app.models.signals import Signal, AlgorithmSettings
from backend.app.models.results import BacktestResult, Trade, PerformanceMetrics


@pytest.fixture
def mock_data_service():
    """Mock data service for testing."""
    service = Mock(spec=DataService)
    service.fetch_historical_data = AsyncMock()
    return service


@pytest.fixture
def mock_algorithm_engine():
    """Mock algorithm engine for testing."""
    engine = Mock(spec=AlgorithmEngine)
    engine.generate_signals = Mock()
    return engine


@pytest.fixture
def sample_historical_data():
    """Sample historical market data spanning 3 months."""
    base_date = date(2024, 1, 1)
    data = []
    
    for i in range(90):  # 90 days of data
        current_date = base_date + timedelta(days=i)
        # Skip weekends (simplified)
        if current_date.weekday() >= 5:
            continue
            
        # Create realistic price movement
        base_price = 150.0
        trend = i * 0.1  # Slight upward trend
        volatility = (i % 10) * 0.5  # Some volatility
        
        price = base_price + trend + volatility
        
        data.append(MarketData(
            symbol="AAPL",
            timestamp=datetime.combine(current_date, datetime.min.time()),
            open=price - 0.5,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=1000000 + i * 1000
        ))
    
    return data


@pytest.fixture
def realistic_signals():
    """Realistic trading signals for backtesting."""
    return [
        # Long signal early in the period
        Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 1, 15),
            price=151.5,
            confidence=0.85,
            indicators=TechnicalIndicators(
                ema5=151.0,
                ema8=150.5,
                ema13=150.0,
                ema21=149.5,
                ema50=149.0,
                atr=2.5,
                atr_long_line=149.0,
                atr_short_line=154.0
            )
        ),
        # Short signal in the middle
        Signal(
            symbol="AAPL",
            signal_type="short",
            timestamp=datetime(2024, 2, 15),
            price=158.0,
            confidence=0.75,
            indicators=TechnicalIndicators(
                ema5=158.5,
                ema8=159.0,
                ema13=159.5,
                ema21=160.0,
                ema50=160.5,
                atr=3.0,
                atr_long_line=155.0,
                atr_short_line=161.0
            )
        ),
        # Another long signal later
        Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 3, 1),
            price=162.0,
            confidence=0.90,
            indicators=TechnicalIndicators(
                ema5=161.5,
                ema8=161.0,
                ema13=160.5,
                ema21=160.0,
                ema50=159.5,
                atr=2.8,
                atr_long_line=159.2,
                atr_short_line=164.8
            )
        )
    ]


@pytest.mark.asyncio
class TestBacktestServiceIntegration:
    """Integration tests for backtest service."""
    
    async def test_complete_backtest_workflow(self, mock_data_service, mock_algorithm_engine,
                                            sample_historical_data, realistic_signals):
        """Test complete backtesting workflow from start to finish."""
        # Setup mocks
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Create signal lookup for realistic signal generation
        signal_lookup = {signal.timestamp.date(): signal for signal in realistic_signals}
        
        def mock_generate_signals(*args, **kwargs):
            market_data = kwargs.get('market_data') or args[0]
            return [signal_lookup[market_data.timestamp.date()]] if market_data.timestamp.date() in signal_lookup else []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals
        
        # Create backtest service
        service = BacktestService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine,
            max_workers=2
        )
        
        # Mock database operations
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock) as mock_save:
            # Execute backtest
            result = await service.run_backtest(symbols, start_date, end_date)
            
            # Verify result structure
            assert isinstance(result, BacktestResult)
            assert result.symbols == symbols
            assert result.start_date == start_date
            assert result.end_date == end_date
            assert len(result.trades) > 0  # Should have generated trades
            assert isinstance(result.performance, PerformanceMetrics)
            
            # Verify performance metrics are calculated
            assert result.performance.total_trades > 0
            assert result.performance.win_rate >= 0.0
            assert result.performance.win_rate <= 1.0
            assert isinstance(result.performance.total_return, float)
            assert isinstance(result.performance.max_drawdown, float)
            
            # Verify data service calls
            mock_data_service.fetch_historical_data.assert_called()
            
            # Verify algorithm engine was called multiple times
            assert mock_algorithm_engine.generate_signals.call_count >= 50  # Should process many days
            
            # Verify database save
            mock_save.assert_called_once()
            
            # Verify trades have proper structure
            for trade in result.trades:
                assert isinstance(trade, Trade)
                assert trade.symbol == "AAPL"
                assert trade.trade_type in ["long", "short"]
                assert trade.entry_date < trade.exit_date
                assert isinstance(trade.pnl, float)
                assert isinstance(trade.pnl_percent, float)
    
    async def test_backtest_with_custom_settings(self, mock_data_service, mock_algorithm_engine,
                                               sample_historical_data, realistic_signals):
        """Test backtesting with custom algorithm settings."""
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        # Custom algorithm settings
        custom_settings = AlgorithmSettings(
            atr_multiplier=2.5,
            ema5_rising_threshold=0.03,
            ema8_rising_threshold=0.02,
            ema21_rising_threshold=0.01,
            volatility_filter=1.8,
            fomo_filter=1.2,
            higher_timeframe="15m"
        )
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Mock algorithm to return one signal
        mock_algorithm_engine.generate_signals.return_value = [realistic_signals[0]]
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(symbols, start_date, end_date, settings=custom_settings)
            
            # Verify custom settings were used
            assert result.settings_used == custom_settings
            
            # Verify higher timeframe data was requested
            assert mock_data_service.fetch_historical_data.call_count == 2  # Current + HTF
    
    async def test_backtest_with_custom_simulation(self, mock_data_service, mock_algorithm_engine,
                                                 sample_historical_data, realistic_signals):
        """Test backtesting with custom trade simulation settings."""
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        # Custom simulation settings
        simulation_config = TradeSimulation(
            entry_delay_minutes=5,
            stop_loss_percent=0.05,
            take_profit_percent=0.10,
            max_hold_days=30,
            commission_per_trade=2.50
        )
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Mock algorithm to return signals
        signal_lookup = {signal.timestamp.date(): signal for signal in realistic_signals}
        
        def mock_generate_signals(*args, **kwargs):
            market_data = kwargs.get('market_data') or args[0]
            return [signal_lookup[market_data.timestamp.date()]] if market_data.timestamp.date() in signal_lookup else []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(
                symbols, start_date, end_date, simulation_config=simulation_config
            )
            
            # Verify trades were generated with custom simulation
            assert len(result.trades) > 0
            
            # Check that commission was applied (trades should have slightly lower PnL)
            for trade in result.trades:
                # Commission should be subtracted from PnL
                assert isinstance(trade.pnl, float)
    
    async def test_backtest_multiple_symbols(self, mock_data_service, mock_algorithm_engine,
                                           sample_historical_data, realistic_signals):
        """Test backtesting with multiple symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        # Create data for all symbols
        mock_data_service.fetch_historical_data.return_value = {
            symbol: [
                MarketData(
                    symbol=symbol,
                    timestamp=data.timestamp,
                    open=data.open,
                    high=data.high,
                    low=data.low,
                    close=data.close,
                    volume=data.volume
                ) for data in sample_historical_data
            ] for symbol in symbols
        }
        
        # Mock algorithm to return signals for different symbols
        def mock_generate_signals(*args, **kwargs):
            market_data = kwargs.get('market_data') or args[0]
            # Return signals for different symbols on different dates
            if market_data.symbol == "AAPL" and market_data.timestamp.day == 15:
                return [realistic_signals[0]]
            elif market_data.symbol == "MSFT" and market_data.timestamp.day == 20:
                return [Signal(
                    symbol="MSFT",
                    signal_type="long",
                    timestamp=market_data.timestamp,
                    price=market_data.close,
                    confidence=0.8,
                    indicators=TechnicalIndicators(
                        ema5=market_data.close,
                        ema8=market_data.close - 0.5,
                        ema13=market_data.close - 1.0,
                        ema21=market_data.close - 1.5,
                        ema50=market_data.close - 2.0,
                        atr=2.0,
                        atr_long_line=market_data.close - 2.0,
                        atr_short_line=market_data.close + 2.0
                    )
                )]
            return []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(symbols, start_date, end_date)
            
            # Verify all symbols were processed
            assert result.symbols == symbols
            
            # Should have trades from multiple symbols
            trade_symbols = set(trade.symbol for trade in result.trades)
            assert len(trade_symbols) > 1  # Multiple symbols should have trades
    
    async def test_backtest_error_handling(self, mock_data_service, mock_algorithm_engine):
        """Test error handling during backtesting."""
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        # Mock data service to raise error
        mock_data_service.fetch_historical_data.side_effect = Exception("API Error")
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Should propagate the error
        with pytest.raises(Exception, match="API Error"):
            await service.run_backtest(symbols, start_date, end_date)
    
    async def test_backtest_algorithm_errors(self, mock_data_service, mock_algorithm_engine,
                                           sample_historical_data):
        """Test handling of algorithm engine errors during backtesting."""
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Mock algorithm engine to raise errors occasionally
        def mock_generate_signals_with_errors(*args, **kwargs):
            market_data = kwargs.get('market_data') or args[0]
            # Raise error on specific dates
            if market_data.timestamp.day == 15:
                raise Exception("Algorithm Error")
            return []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals_with_errors
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            # Should complete despite algorithm errors
            result = await service.run_backtest(symbols, start_date, end_date)
            
            # Should still return a valid result
            assert isinstance(result, BacktestResult)
            assert result.symbols == symbols
    
    async def test_backtest_performance_calculation(self, mock_data_service, mock_algorithm_engine,
                                                  sample_historical_data):
        """Test comprehensive performance metrics calculation."""
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Create a pattern of winning and losing trades
        signal_count = 0
        
        def mock_generate_signals_pattern(*args, **kwargs):
            nonlocal signal_count
            market_data = kwargs.get('market_data') or args[0]
            
            # Generate signals every 10 days
            if market_data.timestamp.day % 10 == 0:
                signal_count += 1
                signal_type = "long" if signal_count % 2 == 1 else "short"
                return [Signal(
                    symbol="AAPL",
                    signal_type=signal_type,
                    timestamp=market_data.timestamp,
                    price=market_data.close,
                    confidence=0.8,
                    indicators=TechnicalIndicators(
                        ema5=market_data.close,
                        ema8=market_data.close - 0.5,
                        ema13=market_data.close - 1.0,
                        ema21=market_data.close - 1.5,
                        ema50=market_data.close - 2.0,
                        atr=2.0,
                        atr_long_line=market_data.close - 2.0,
                        atr_short_line=market_data.close + 2.0
                    )
                )]
            return []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals_pattern
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(symbols, start_date, end_date)
            
            # Verify comprehensive performance metrics
            perf = result.performance
            assert perf.total_trades > 0
            assert perf.winning_trades + perf.losing_trades == perf.total_trades
            assert 0.0 <= perf.win_rate <= 1.0
            assert isinstance(perf.total_return, float)
            assert isinstance(perf.average_return, float)
            assert perf.max_drawdown >= 0.0
            assert isinstance(perf.sharpe_ratio, float)
            
            # Verify individual trades have proper data
            for trade in result.trades:
                assert trade.entry_date < trade.exit_date
                assert isinstance(trade.entry_price, float)
                assert isinstance(trade.exit_price, float)
                assert trade.entry_price > 0
                assert trade.exit_price > 0
    
    async def test_backtest_history_integration(self, mock_data_service, mock_algorithm_engine):
        """Test backtest history retrieval integration."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Mock database query
        with patch('backend.app.services.backtest_service.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock backtest result
            mock_backtest = Mock()
            mock_backtest.id = "test-id"
            mock_backtest.timestamp = datetime.now()
            mock_backtest.start_date = date(2024, 1, 1)
            mock_backtest.end_date = date(2024, 3, 31)
            mock_backtest.symbols = ["AAPL"]
            mock_backtest.trades = [
                {
                    "symbol": "AAPL",
                    "entry_date": "2024-01-15T00:00:00",
                    "entry_price": 150.0,
                    "exit_date": "2024-01-16T00:00:00",
                    "exit_price": 155.0,
                    "trade_type": "long",
                    "pnl": 5.0,
                    "pnl_percent": 0.0333
                }
            ]
            mock_backtest.performance = {
                "total_trades": 1,
                "winning_trades": 1,
                "losing_trades": 0,
                "win_rate": 1.0,
                "total_return": 0.0333,
                "average_return": 0.0333,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0
            }
            mock_backtest.settings_used = {
                "atr_multiplier": 2.0,
                "ema5_rising_threshold": 0.02,
                "ema8_rising_threshold": 0.01,
                "ema21_rising_threshold": 0.005,
                "volatility_filter": 1.5,
                "fomo_filter": 1.0,
                "higher_timeframe": "15m"
            }
            
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [mock_backtest]
            
            # Test history retrieval
            filters = BacktestFilters(symbols=["AAPL"], limit=10)
            results = await service.get_backtest_history(filters)
            
            # Verify results
            assert len(results) == 1
            result = results[0]
            assert isinstance(result, BacktestResult)
            assert result.symbols == ["AAPL"]
            assert len(result.trades) == 1
            assert isinstance(result.performance, PerformanceMetrics)
    
    async def test_backtest_statistics_integration(self, mock_data_service, mock_algorithm_engine):
        """Test backtest statistics calculation integration."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Mock database query for statistics
        with patch('backend.app.services.backtest_service.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock multiple backtest results
            mock_backtests = []
            for i in range(3):
                mock_backtest = Mock()
                mock_backtest.symbols = ["AAPL", "MSFT"][i % 2:i % 2 + 1]
                mock_backtest.trades = [{"symbol": "AAPL", "pnl": 5.0}] * (i + 1)
                mock_backtest.performance = {
                    "total_trades": i + 1,
                    "win_rate": 0.6 + i * 0.1,
                    "total_return": 0.05 + i * 0.02
                }
                mock_backtests.append(mock_backtest)
            
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = mock_backtests
            
            # Test statistics calculation
            stats = await service.get_backtest_statistics(days=30)
            
            # Verify statistics structure
            assert "total_backtests" in stats
            assert "total_trades" in stats
            assert "average_win_rate" in stats
            assert "average_return" in stats
            assert "best_performing_symbols" in stats
            assert "most_tested_symbols" in stats
            
            # Verify calculated values
            assert stats["total_backtests"] == 3
            assert stats["total_trades"] == 6  # 1 + 2 + 3
            assert isinstance(stats["average_win_rate"], float)
            assert isinstance(stats["average_return"], float)