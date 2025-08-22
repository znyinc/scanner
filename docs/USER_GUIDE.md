# Stock Scanner User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Algorithm Overview](#algorithm-overview)
3. [Getting Started](#getting-started)
4. [Using the Scanner](#using-the-scanner)
5. [Running Backtests](#running-backtests)
6. [Understanding Results](#understanding-results)
7. [Configuration Settings](#configuration-settings)
8. [Troubleshooting](#troubleshooting)

## Introduction

The Stock Scanner is a sophisticated web-based application that identifies potential trading opportunities using a custom EMA-ATR algorithm with higher timeframe confirmation. The system analyzes real-time market data to find stocks that meet specific technical criteria for both long and short positions.

### Key Features
- **Real-time Stock Scanning**: Analyze multiple stocks simultaneously for trading signals
- **Historical Backtesting**: Test the algorithm's performance on historical data
- **Customizable Parameters**: Adjust algorithm settings for different market conditions
- **Comprehensive History**: Track all scans and backtests for performance analysis
- **Responsive Web Interface**: Access from any device with a modern web browser

## Algorithm Overview

### Core Components

The algorithm combines multiple technical indicators to identify high-probability trading setups:

#### 1. Exponential Moving Averages (EMAs)
- **EMA 5**: Short-term trend indicator
- **EMA 8**: Primary signal line
- **EMA 13**: Medium-term trend
- **EMA 21**: Intermediate trend
- **EMA 50**: Long-term trend

#### 2. Average True Range (ATR)
- **ATR Period**: 14 (default)
- **ATR Multiplier**: 2.0 (configurable)
- **ATR Long Line**: EMA21 - (ATR × Multiplier)
- **ATR Short Line**: EMA21 + (ATR × Multiplier)

#### 3. Higher Timeframe Confirmation
- Uses 15-minute timeframe data (configurable)
- Confirms signals with higher timeframe trend alignment

### Signal Generation Logic

#### Long Signal Conditions
A long signal is generated when ALL of the following conditions are met:

1. **Polar Formation (Bullish)**:
   - Current close > current open
   - Current close > EMA8
   - Current close > EMA21

2. **EMA Positioning**:
   - EMA5 is below the ATR Long Line

3. **Rising EMAs**:
   - EMA5 is rising (above threshold)
   - EMA8 is rising (above threshold)
   - EMA21 is rising (above threshold)

4. **FOMO Filter**:
   - Price hasn't moved too far too fast
   - Prevents entering overextended moves

5. **Higher Timeframe Confirmation**:
   - HTF EMA5 > HTF EMA8
   - Current close > HTF close
   - Current close > HTF open

#### Short Signal Conditions
A short signal is generated when ALL of the following conditions are met:

1. **Polar Formation (Bearish)**:
   - Current close < current open
   - Current close < EMA8
   - Current close < EMA21

2. **EMA Positioning**:
   - EMA5 is above the ATR Short Line

3. **Falling EMAs**:
   - EMA5 is falling (below threshold)
   - EMA8 is falling (below threshold)
   - EMA21 is falling (below threshold)

4. **FOMO Filter**:
   - Price hasn't moved too far too fast
   - Prevents entering overextended moves

5. **Higher Timeframe Confirmation**:
   - HTF EMA5 < HTF EMA8
   - Current close < HTF close
   - Current close < HTF open

## Getting Started

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for real-time data
- No additional software installation required

### Accessing the Application
1. Open your web browser
2. Navigate to the application URL
3. The dashboard will load automatically

### Interface Overview
The main interface consists of four primary sections:

1. **Scanner Dashboard**: Initiate scans and view real-time results
2. **Backtest Interface**: Run historical analysis
3. **History Viewer**: Review past scans and backtests
4. **Settings Panel**: Configure algorithm parameters

## Using the Scanner

### Running a Basic Scan

1. **Navigate to Scanner Dashboard**
   - Click on the "Scanner" tab in the main navigation

2. **Enter Stock Symbols**
   - Type stock symbols separated by commas (e.g., "AAPL, GOOGL, MSFT")
   - Or use the symbol picker for popular stocks

3. **Start the Scan**
   - Click the "Start Scan" button
   - The system will begin analyzing each stock

4. **Monitor Progress**
   - A progress bar shows scan completion
   - Real-time updates display as stocks are processed

5. **Review Results**
   - Signals appear in the results table
   - Each signal shows stock symbol, signal type, price, and key indicators

### Understanding Scan Results

Each scan result displays:

- **Symbol**: Stock ticker symbol
- **Signal Type**: "LONG" or "SHORT"
- **Price**: Current stock price
- **EMA Values**: Current EMA5, EMA8, EMA21 values
- **ATR Level**: Current ATR and threshold lines
- **Confidence**: Algorithm confidence score (0-100)
- **Timestamp**: When the signal was generated

### Filtering and Sorting Results

- **Filter by Signal Type**: Show only long or short signals
- **Sort by Confidence**: Order results by confidence score
- **Sort by Symbol**: Alphabetical ordering
- **Filter by Price Range**: Show stocks within specific price ranges

## Running Backtests

### Setting Up a Backtest

1. **Navigate to Backtest Interface**
   - Click on the "Backtest" tab

2. **Select Date Range**
   - Choose start date (how far back to test)
   - Choose end date (when to stop testing)
   - Recommended: At least 30 days for meaningful results

3. **Choose Stock Symbols**
   - Enter symbols to test (same format as scanning)
   - Consider testing on liquid, well-known stocks first

4. **Configure Settings** (Optional)
   - Use default settings or customize parameters
   - See [Configuration Settings](#configuration-settings) for details

5. **Start Backtest**
   - Click "Run Backtest"
   - Processing time depends on date range and number of stocks

### Interpreting Backtest Results

#### Performance Metrics

- **Total Trades**: Number of completed trades
- **Winning Trades**: Number of profitable trades
- **Win Rate**: Percentage of profitable trades
- **Total Return**: Overall profit/loss percentage
- **Average Return**: Average return per trade
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure

#### Trade Details

Each trade shows:
- **Entry Date/Time**: When position was opened
- **Entry Price**: Price at entry
- **Exit Date/Time**: When position was closed
- **Exit Price**: Price at exit
- **P&L**: Profit or loss amount
- **P&L %**: Percentage return
- **Duration**: How long the trade lasted

#### Performance Charts

- **Equity Curve**: Shows account value over time
- **Drawdown Chart**: Visualizes drawdown periods
- **Monthly Returns**: Breakdown by month
- **Trade Distribution**: Histogram of trade returns

## Understanding Results

### Signal Quality Indicators

#### Confidence Score
The confidence score (0-100) indicates how strongly the signal meets all criteria:
- **90-100**: Excellent signal, all conditions strongly met
- **70-89**: Good signal, most conditions well met
- **50-69**: Moderate signal, conditions marginally met
- **Below 50**: Weak signal, consider avoiding

#### Market Context
Consider these factors when evaluating signals:
- **Market Trend**: Signals align better with overall market direction
- **Volume**: Higher volume increases signal reliability
- **Volatility**: Extreme volatility may produce false signals
- **News Events**: Major news can override technical signals

### Risk Management Guidelines

#### Position Sizing
- Never risk more than 1-2% of account per trade
- Use smaller position sizes when learning the system
- Consider signal confidence when sizing positions

#### Stop Losses
- Long positions: Consider stops below ATR Long Line
- Short positions: Consider stops above ATR Short Line
- Adjust stops based on volatility and timeframe

#### Take Profits
- Scale out of positions as they move in your favor
- Consider taking partial profits at key resistance/support levels
- Trail stops to protect profits on winning trades

## Configuration Settings

### Algorithm Parameters

#### ATR Multiplier (Default: 2.0)
- Controls distance of ATR lines from EMA21
- Higher values = wider bands, fewer signals
- Lower values = tighter bands, more signals
- Range: 1.0 - 4.0

#### EMA Rising Thresholds
- **EMA5 Threshold (Default: 0.02)**: Minimum slope for EMA5 to be considered "rising"
- **EMA8 Threshold (Default: 0.01)**: Minimum slope for EMA8 to be considered "rising"
- **EMA21 Threshold (Default: 0.005)**: Minimum slope for EMA21 to be considered "rising"

#### Volatility Filter (Default: 1.5)
- Filters out stocks with excessive volatility
- Higher values = allow more volatile stocks
- Lower values = only stable stocks
- Range: 1.0 - 3.0

#### FOMO Filter (Default: 1.0)
- Prevents entering overextended moves
- Higher values = allow larger moves
- Lower values = stricter entry requirements
- Range: 0.5 - 2.0

#### Higher Timeframe (Default: 15m)
- Timeframe for confirmation signals
- Options: 5m, 15m, 30m, 1h
- Higher timeframes = stronger confirmation, fewer signals

### Customizing Settings

1. **Access Settings Panel**
   - Click on "Settings" tab

2. **Modify Parameters**
   - Adjust sliders or enter values directly
   - Real-time validation prevents invalid inputs

3. **Test Changes**
   - Use "Test Settings" to see impact on recent data
   - Compare results with different parameter sets

4. **Save Configuration**
   - Click "Save Settings" to persist changes
   - Settings apply to all future scans and backtests

5. **Reset to Defaults**
   - Use "Reset to Defaults" to restore original values

## Troubleshooting

### Common Issues

#### No Signals Found
**Possible Causes:**
- Market conditions don't meet algorithm criteria
- Settings too restrictive
- Stocks selected don't have sufficient volatility

**Solutions:**
- Try different stock symbols
- Adjust ATR multiplier or EMA thresholds
- Check if market is trending or ranging

#### Slow Performance
**Possible Causes:**
- Too many stocks in scan list
- Network connectivity issues
- High market volatility causing data delays

**Solutions:**
- Reduce number of stocks per scan
- Check internet connection
- Try scanning during off-peak hours

#### Backtest Errors
**Possible Causes:**
- Insufficient historical data
- Date range too large
- Invalid stock symbols

**Solutions:**
- Use shorter date ranges
- Verify stock symbols are correct
- Ensure stocks were trading during selected period

#### Data Issues
**Possible Causes:**
- Market closed
- Data provider issues
- Stock delisted or suspended

**Solutions:**
- Check market hours
- Try different stocks
- Wait and retry later

### Getting Help

#### Error Messages
The system provides detailed error messages with suggested solutions:
- Read error messages carefully
- Follow suggested remediation steps
- Check system status if problems persist

#### Performance Tips
- Start with small stock lists (5-10 symbols)
- Use default settings initially
- Run backtests on shorter periods first
- Monitor system performance during scans

#### Best Practices
- Keep scan lists manageable (under 50 stocks)
- Regular review and adjustment of settings
- Maintain trading journal with scan results
- Combine with fundamental analysis for best results

### Support Resources

- **Documentation**: Complete technical documentation available
- **Examples**: Sample configurations and use cases
- **Community**: User forums and discussion groups
- **Updates**: Regular system updates and improvements

---

*This user guide is regularly updated. Check for the latest version to ensure you have current information about features and functionality.*