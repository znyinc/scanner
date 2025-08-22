"""
Unit tests for the backtest service.
"""
import pytest
import asyncio
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from backend.app.services.backtest_service import BacktestService, BacktestFilters, TradeSimulation
from backend.app.services.data_service import DataService
from backend.app.services.algorithm_engine import AlgorithmEngine
from backend.app.models.market_data import MarketData
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
    """Sample historical market data for testing."""
    base_date = date(2024, 1, 1)
    return [
        MarketData(
            symbol="AAPL",
            timestamp=datetime.combine(base_date + timedelta(days=i), datetime.min.time()),
            open=150.0 + i * 0.5,
            high=152.0 + i * 0.5,
            low=149.0 + i * 0.5,
            close=151.0 + i * 0.5,
            volume=1000000 + i * 1000
        ) for i in range(100)  # 100 days of data
    ]


@pytest.fixture
def sample_signals():
    """Sample trading signals for testing."""
    return [
        Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime(2024, 1, 60),  # Day 60
            price=180.0,
            confidence=0.85,
            indicators={
                "ema_5": 179.5,
                "ema_8": 179.0,
                "atr": 3.0
            },
            conditions_met=["polar_formation", "ema_alignment"]
        ),
        Signal(
            symbol="AAPL",
            signal_type="short",
            timestamp=datetime(2024, 1, 80),  # Day 80
            price=190.0,
            confidence=0.75,
            indicators={
                "ema_5": 190.5,
                "ema_8": 191.0,
                "atr": 3.5
            },
            conditions_met=["polar_formation", "ema_alignment"]
        )
    ]


class TestBacktestService:
    """Unit tests for BacktestService."""
    
    def test_init(self):
        """Test service initialization."""
        service = BacktestService()
        assert service.data_service is not None
        assert service.algorithm_engine is not None
        assert service.max_workers == 3
    
    def test_init_with_dependencies(self, mock_data_service, mock_algorithm_engine):
        """Test service initialization with injected dependencies."""
        service = BacktestService(
            data_service=mock_data_service,
            algorithm_engine=mock_algorithm_engine,
            max_workers=5
        )
        assert service.data_service == mock_data_service
        assert service.algorithm_engine == mock_algorithm_engine
        assert service.max_workers == 5
    
    @pytest.mark.asyncio
    async def test_run_backtest_empty_symbols(self, mock_data_service, mock_algorithm_engine):
        """Test backtest with empty symbol list."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with pytest.raises(ValueError, match="No symbols provided"):
            await service.run_backtest([], date(2024, 1, 1), date(2024, 1, 31))
    
    @pytest.mark.asyncio
    async def test_run_backtest_invalid_date_range(self, mock_data_service, mock_algorithm_engine):
        """Test backtest with invalid date range."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with pytest.raises(ValueError, match="Start date must be before end date"):
            await service.run_backtest(["AAPL"], date(2024, 1, 31), date(2024, 1, 1))
    
    @pytest.mark.asyncio
    async def test_run_backtest_success(self, mock_data_service, mock_algorithm_engine, 
                                      sample_historical_data, sample_signals):
        """Test successful backtest execution."""
        # Setup mocks
        symbols = ["AAPL"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_data_service.fetch_historical_data.return_value = {
            "AAPL": sample_historical_data
        }
        
        # Mock algorithm engine to return signals at specific points
        def mock_generate_signals(*args, **kwargs):
            market_data = kwargs.get('market_data') or args[0]
            # Return long signal on day 60, short signal on day 80
            if market_data.timestamp.day == 60:
                return [sample_signals[0]]
            elif market_data.timestamp.day == 80:
                return [sample_signals[1]]
            return []
        
        mock_algorithm_engine.generate_signals.side_effect = mock_generate_signals
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Mock database operations
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock) as mock_save:
            result = await service.run_backtest(symbols, start_date, end_date)
            
            # Verify result
            assert isinstance(result, BacktestResult)
            assert result.symbols == symbols
            assert result.start_date == start_date
            assert result.end_date == end_date
            assert len(result.trades) > 0  # Should have generated some trades
            assert isinstance(result.performance, PerformanceMetrics)
            
            # Verify data service was called
            mock_data_service.fetch_historical_data.assert_called()
            
            # Verify database save
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_backtest_insufficient_data(self, mock_data_service, mock_algorithm_engine):
        """Test backtest with insufficient historical data."""
        # Return very limited data (less than 50 points)
        limited_data = [
            MarketData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1),
                open=150.0,
                high=151.0,
                low=149.0,
                close=150.5,
                volume=1000000
            )
        ]
        
        mock_data_service.fetch_historical_data.return_value = {"AAPL": limited_data}
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(["AAPL"], date(2024, 1, 1), date(2024, 1, 31))
            
            # Should complete but generate no trades due to insufficient data
            assert len(result.trades) == 0
            assert result.performance.total_trades == 0
    
    @pytest.mark.asyncio
    async def test_run_backtest_no_data(self, mock_data_service, mock_algorithm_engine):
        """Test backtest with no historical data."""
        mock_data_service.fetch_historical_data.return_value = {"AAPL": []}
        
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        with patch.object(service, '_save_backtest_result', new_callable=AsyncMock):
            result = await service.run_backtest(["AAPL"], date(2024, 1, 1), date(2024, 1, 31))
            
            # Should complete but generate no trades
            assert len(result.trades) == 0
            assert result.performance.total_trades == 0
    
    def test_calculate_performance_metrics_empty_trades(self, mock_data_service, mock_algorithm_engine):
        """Test performance metrics calculation with no trades."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        metrics = service.calculate_performance_metrics([])
        
        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.total_return == 0.0
        assert metrics.average_return == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio == 0.0
    
    def test_calculate_performance_metrics_with_trades(self, mock_data_service, mock_algorithm_engine):
        """Test performance metrics calculation with sample trades."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Create sample trades
        trades = [
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 1),
                entry_price=100.0,
                exit_date=datetime(2024, 1, 2),
                exit_price=105.0,
                trade_type="long",
                pnl=5.0,
                pnl_percent=0.05
            ),
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 3),
                entry_price=105.0,
                exit_date=datetime(2024, 1, 4),
                exit_price=102.0,
                trade_type="long",
                pnl=-3.0,
                pnl_percent=-0.0286
            ),
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 5),
                entry_price=102.0,
                exit_date=datetime(2024, 1, 6),
                exit_price=108.0,
                trade_type="long",
                pnl=6.0,
                pnl_percent=0.0588
            )
        ]
        
        metrics = service.calculate_performance_metrics(trades)
        
        assert metrics.total_trades == 3
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 1
        assert abs(metrics.win_rate - 0.6667) < 0.001  # 2/3
        assert abs(metrics.total_return - 0.0902) < 0.001  # Sum of pnl_percent
        assert abs(metrics.average_return - 0.0301) < 0.001  # Average pnl_percent
        assert metrics.max_drawdown >= 0.0
        assert metrics.sharpe_ratio != 0.0
    
    def test_calculate_max_drawdown(self, mock_data_service, mock_algorithm_engine):
        """Test maximum drawdown calculation."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Create trades with known drawdown pattern
        trades = [
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 1),
                entry_price=100.0,
                exit_date=datetime(2024, 1, 2),
                exit_price=110.0,
                trade_type="long",
                pnl=10.0,
                pnl_percent=0.10  # +10%
            ),
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 3),
                entry_price=110.0,
                exit_date=datetime(2024, 1, 4),
                exit_price=99.0,
                trade_type="long",
                pnl=-11.0,
                pnl_percent=-0.10  # -10%
            ),
            Trade(
                symbol="AAPL",
                entry_date=datetime(2024, 1, 5),
                entry_price=99.0,
                exit_date=datetime(2024, 1, 6),
                exit_price=89.1,
                trade_type="long",
                pnl=-9.9,
                pnl_percent=-0.10  # -10%
            )
        ]
        
        max_drawdown = service._calculate_max_drawdown(trades)
        
        # Peak at +10%, then down to -10%, drawdown = 20%
        assert abs(max_drawdown - 0.20) < 0.001
    
    def test_calculate_sharpe_ratio(self, mock_data_service, mock_algorithm_engine):
        """Test Sharpe ratio calculation."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Test with consistent positive returns
        returns = [0.05, 0.03, 0.07, 0.02, 0.06]
        sharpe = service._calculate_sharpe_ratio(returns)
        assert sharpe > 0
        
        # Test with empty returns
        sharpe_empty = service._calculate_sharpe_ratio([])
        assert sharpe_empty == 0.0
        
        # Test with single return
        sharpe_single = service._calculate_sharpe_ratio([0.05])
        assert sharpe_single == 0.0
        
        # Test with zero standard deviation
        sharpe_zero_std = service._calculate_sharpe_ratio([0.05, 0.05, 0.05])
        assert sharpe_zero_std == 0.0
    
    def test_should_open_position(self, mock_data_service, mock_algorithm_engine):
        """Test position opening logic."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime.now(),
            price=150.0,
            confidence=0.8,
            indicators={},
            conditions_met=[]
        )
        
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=150.0,
            high=151.0,
            low=149.0,
            close=150.5,
            volume=1000000
        )
        
        # Should open position with good signal
        assert service._should_open_position(signal, market_data) == True
        
        # Should not open with low confidence
        signal.confidence = 0.3
        assert service._should_open_position(signal, market_data) == False
        
        # Should not open with wrong symbol
        signal.confidence = 0.8
        signal.symbol = "MSFT"
        assert service._should_open_position(signal, market_data) == False
    
    def test_should_close_position_opposite_signal(self, mock_data_service, mock_algorithm_engine):
        """Test position closing on opposite signal."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Long position
        long_position = {
            'trade_type': 'long',
            'entry_price': 150.0,
            'entry_date': datetime.now()
        }
        
        # Short signal should close long position
        short_signal = Signal(
            symbol="AAPL",
            signal_type="short",
            timestamp=datetime.now(),
            price=155.0,
            confidence=0.8,
            indicators={},
            conditions_met=[]
        )
        
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=155.0,
            high=156.0,
            low=154.0,
            close=155.5,
            volume=1000000
        )
        
        simulation_config = TradeSimulation()
        
        assert service._should_close_position(long_position, short_signal, market_data, simulation_config) == True
    
    def test_should_close_position_stop_loss(self, mock_data_service, mock_algorithm_engine):
        """Test position closing on stop loss."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Long position
        long_position = {
            'trade_type': 'long',
            'entry_price': 150.0,
            'entry_date': datetime.now()
        }
        
        # Neutral signal (no close signal)
        neutral_signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime.now(),
            price=140.0,
            confidence=0.5,
            indicators={},
            conditions_met=[]
        )
        
        # Market data showing loss
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=140.0,
            high=141.0,
            low=139.0,
            close=140.0,  # 6.67% loss from entry
            volume=1000000
        )
        
        # Configure 5% stop loss
        simulation_config = TradeSimulation(stop_loss_percent=0.05)
        
        # Should close due to stop loss
        assert service._should_close_position(long_position, neutral_signal, market_data, simulation_config) == True
        
        # Should not close with higher stop loss
        simulation_config.stop_loss_percent = 0.10
        assert service._should_close_position(long_position, neutral_signal, market_data, simulation_config) == False
    
    def test_should_close_position_timeout(self, mock_data_service, mock_algorithm_engine):
        """Test position closing on timeout."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Position opened 10 days ago
        old_position = {
            'trade_type': 'long',
            'entry_price': 150.0,
            'entry_date': datetime.now() - timedelta(days=10)
        }
        
        current_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=155.0,
            high=156.0,
            low=154.0,
            close=155.0,
            volume=1000000
        )
        
        # Configure 5-day max hold
        simulation_config = TradeSimulation(max_hold_days=5)
        
        # Should close due to timeout
        assert service._should_close_position_timeout(old_position, current_data, simulation_config) == True
        
        # Should not close with longer max hold
        simulation_config.max_hold_days = 15
        assert service._should_close_position_timeout(old_position, current_data, simulation_config) == False
    
    def test_open_position(self, mock_data_service, mock_algorithm_engine):
        """Test opening a new position."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        signal = Signal(
            symbol="AAPL",
            signal_type="long",
            timestamp=datetime.now(),
            price=150.0,
            confidence=0.8,
            indicators={},
            conditions_met=[]
        )
        
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=150.0,
            high=151.0,
            low=149.0,
            close=150.5,
            volume=1000000
        )
        
        simulation_config = TradeSimulation(entry_delay_minutes=5)
        
        position = service._open_position(signal, market_data, simulation_config)
        
        assert position['symbol'] == "AAPL"
        assert position['trade_type'] == "long"
        assert position['entry_price'] == 150.5
        assert position['signal_confidence'] == 0.8
        assert position['entry_date'] == market_data.timestamp + timedelta(minutes=5)
    
    def test_close_position(self, mock_data_service, mock_algorithm_engine):
        """Test closing a position."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Long position
        position = {
            'symbol': 'AAPL',
            'trade_type': 'long',
            'entry_date': datetime(2024, 1, 1),
            'entry_price': 150.0,
            'signal_confidence': 0.8
        }
        
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 2),
            open=155.0,
            high=156.0,
            low=154.0,
            close=155.0,
            volume=1000000
        )
        
        simulation_config = TradeSimulation(commission_per_trade=1.0)
        
        trade = service._close_position(position, market_data, simulation_config)
        
        assert isinstance(trade, Trade)
        assert trade.symbol == "AAPL"
        assert trade.trade_type == "long"
        assert trade.entry_price == 150.0
        assert trade.exit_price == 155.0
        assert trade.pnl == 4.0  # 5.0 profit - 1.0 commission
        assert abs(trade.pnl_percent - 0.0333) < 0.001  # 5/150
    
    @pytest.mark.asyncio
    async def test_backtest_history_retrieval(self, mock_data_service, mock_algorithm_engine):
        """Test backtest history retrieval."""
        service = BacktestService(mock_data_service, mock_algorithm_engine)
        
        # Mock database query
        with patch('backend.app.services.backtest_service.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock query result
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Test with filters
            filters = BacktestFilters(
                start_date=date(2024, 1, 1),
                symbols=["AAPL"],
                min_trades=5,
                limit=10
            )
            
            results = await service.get_backtest_history(filters)
            
            # Verify database interaction
            assert isinstance(results, list)
            mock_db.query.assert_called_once()
            mock_query.filter.assert_called()
            mock_query.limit.assert_called_with(10)


class TestTradeSimulation:
    """Test TradeSimulation configuration."""
    
    def test_default_config(self):
        """Test default simulation configuration."""
        config = TradeSimulation()
        
        assert config.entry_delay_minutes == 1
        assert config.exit_strategy == "next_opposite_signal"
        assert config.stop_loss_percent is None
        assert config.take_profit_percent is None
        assert config.max_hold_days is None
        assert config.commission_per_trade == 0.0
    
    def test_custom_config(self):
        """Test custom simulation configuration."""
        config = TradeSimulation(
            entry_delay_minutes=5,
            exit_strategy="stop_loss",
            stop_loss_percent=0.05,
            take_profit_percent=0.10,
            max_hold_days=30,
            commission_per_trade=2.50
        )
        
        assert config.entry_delay_minutes == 5
        assert config.exit_strategy == "stop_loss"
        assert config.stop_loss_percent == 0.05
        assert config.take_profit_percent == 0.10
        assert config.max_hold_days == 30
        assert config.commission_per_trade == 2.50


class TestBacktestFilters:
    """Test BacktestFilters configuration."""
    
    def test_default_filters(self):
        """Test default filter configuration."""
        filters = BacktestFilters()
        
        assert filters.start_date is None
        assert filters.end_date is None
        assert filters.symbols is None
        assert filters.min_trades is None
        assert filters.min_win_rate is None
        assert filters.limit == 100
        assert filters.offset == 0
    
    def test_custom_filters(self):
        """Test custom filter configuration."""
        filters = BacktestFilters(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            symbols=["AAPL", "MSFT"],
            min_trades=10,
            min_win_rate=0.6,
            limit=50,
            offset=25
        )
        
        assert filters.start_date == date(2024, 1, 1)
        assert filters.end_date == date(2024, 12, 31)
        assert filters.symbols == ["AAPL", "MSFT"]
        assert filters.min_trades == 10
        assert filters.min_win_rate == 0.6
        assert filters.limit == 50
        assert filters.offset == 25