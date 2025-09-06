# AlphaVantage API Setup Guide

## Why AlphaVantage?

AlphaVantage serves as a reliable fallback when yfinance experiences rate limiting or outages. This ensures your stock scanner continues working even when the primary data source fails.

## Getting Your Free API Key

1. **Visit AlphaVantage**: Go to https://www.alphavantage.co/support/#api-key

2. **Sign Up**: 
   - Enter your email address
   - Choose a password
   - Click "GET FREE API KEY"

3. **Verify Email**: Check your email and click the verification link

4. **Get Your Key**: Your API key will be displayed on the dashboard

## Configure Your Application

1. **Update .env file**:
   ```env
   # Replace 'demo' with your actual API key
   ALPHAVANTAGE_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   ```

2. **Restart the application**:
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart
   python run_server.py
   ```

## API Limits

### Free Tier:
- **5 API calls per minute**
- **500 API calls per day**
- **Intraday data**: Last 100 data points
- **Daily data**: Last 100 data points

### Premium Tiers:
- Higher rate limits
- More historical data
- Real-time data
- Additional features

## Testing Your Setup

Run the test script to verify everything is working:

```bash
python test_alphavantage_fallback.py
```

You should see:
- ✅ AlphaVantage client initialized with API key
- ✅ Data fetching from AlphaVantage when yfinance fails

## Troubleshooting

### "Demo API key" Error
- **Problem**: Still using the demo key
- **Solution**: Replace `ALPHAVANTAGE_API_KEY=demo` with your actual key

### "API call frequency" Error
- **Problem**: Exceeded 5 calls per minute
- **Solution**: Wait 1 minute, the app automatically handles rate limiting

### "Invalid API key" Error
- **Problem**: Incorrect API key format
- **Solution**: Copy the key exactly from AlphaVantage dashboard

### No Data Returned
- **Problem**: Symbol not found or API limit reached
- **Solution**: Check symbol spelling, verify daily limit not exceeded

## How the Fallback Works

1. **Primary**: yfinance attempts (3 retries with exponential backoff)
2. **Fallback**: AlphaVantage attempts if yfinance fails
3. **Rate Limiting**: Automatic 12-second delays between AlphaVantage calls
4. **Caching**: Results cached to minimize API usage

## Benefits

- **Reliability**: Multiple data sources ensure uptime
- **Automatic**: No manual intervention required
- **Cost-effective**: Free tier sufficient for most use cases
- **Transparent**: Logs show which data source was used

## Next Steps

1. Get your free API key: https://www.alphavantage.co/support/#api-key
2. Update your .env file
3. Restart the application
4. Run the test script to verify
5. Enjoy improved data reliability!