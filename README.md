# Stock Scanner

A sophisticated stock scanner application that uses EMA-ATR algorithm with higher timeframe confirmation to identify trading opportunities.

## 🚀 Features

- **Real-time Stock Scanning**: Analyze multiple stocks simultaneously using advanced technical indicators
- **Historical Backtesting**: Test algorithm performance on historical data with comprehensive metrics
- **Web-based Interface**: Modern React frontend with responsive design
- **FastAPI Backend**: High-performance Python backend with async support
- **PostgreSQL Database**: Robust data storage with optimized queries
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Docker Support**: Easy deployment with Docker containers
- **Algorithm Customization**: Configurable parameters for different market conditions

## 📊 Current Status

**✅ FULLY OPERATIONAL** - All components are working and tested (Last updated: August 23, 2025)

| Component | Status | Details |
|-----------|--------|---------|
| 🐳 **Database** | ✅ Running | PostgreSQL 13 in Docker on port 5433 |
| 🔧 **Backend API** | ✅ Running | FastAPI server on http://localhost:8000 |
| 🌐 **Frontend** | ✅ Running | React app on http://localhost:3000 |
| 🔍 **Health Check** | ✅ Working | `/health` endpoint responding (200 OK) |
| ⚙️ **Settings API** | ✅ Working | `/settings` endpoint fixed and working |
| 🔗 **API Integration** | ✅ Working | Frontend successfully connecting to backend |
| 📈 **Stock Scanning** | ✅ Ready | EMA-ATR algorithm implemented and tested |
| 📊 **Backtesting** | ✅ Ready | Historical analysis functionality working |

**Quick Start Commands:**
```bash
# Start everything with one command
./start_stock_scanner.bat

# Or manually:
docker start stock-scanner-db  # Database
cd backend && python run_server.py  # Backend
cd frontend && npm start  # Frontend
```

**Access Points:**
- **Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📊 Algorithm Overview

The stock scanner uses a sophisticated EMA-ATR algorithm that combines:

- **Multiple EMAs**: 5, 8, 13, 21, 50 period exponential moving averages
- **ATR Filters**: Average True Range for volatility-based filtering
- **Polar Formation**: Candlestick pattern recognition
- **Higher Timeframe Confirmation**: 15-minute timeframe validation
- **FOMO and Volatility Filters**: Risk management components

### Signal Generation Logic

**Long Signals** require ALL conditions:
1. **Bullish Polar Formation**: close > open, close > EMA8, close > EMA21
2. **EMA Positioning**: EMA5 below ATR long line
3. **Rising EMAs**: EMA5, EMA8, EMA21 trending upward
4. **FOMO Filter**: Price not overextended
5. **Higher Timeframe Confirmation**: HTF trend alignment

**Short Signals** require ALL conditions:
1. **Bearish Polar Formation**: close < open, close < EMA8, close < EMA21
2. **EMA Positioning**: EMA5 above ATR short line
3. **Falling EMAs**: EMA5, EMA8, EMA21 trending downward
4. **FOMO Filter**: Price not overextended
5. **Higher Timeframe Confirmation**: HTF trend alignment

## 🛠️ Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **PostgreSQL**: 13.0 or higher
- **Git**: Latest version

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/znyinc/scanner.git
cd scanner
```

2. **Set up the backend:**
```bash
cd backend
python -m venv venv

# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Set up the database:**
```bash
# Create PostgreSQL database
createdb stock_scanner

# Initialize schema
python app/init_db.py
```

5. **Set up the frontend:**
```bash
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local if needed
```

6. **Start the application:**
```bash
# Terminal 1 - Backend
cd backend
python run_server.py

# Terminal 2 - Frontend
cd frontend
npm start
```

The application will be available at `http://localhost:3000`.

## 📱 Usage

### Running a Stock Scan

1. **Navigate to Scanner Dashboard**
   - Open the application in your browser
   - Click on the "Scanner" tab

2. **Enter Stock Symbols**
   - Type stock symbols separated by commas (e.g., "AAPL, GOOGL, MSFT")
   - Use the symbol picker for popular stocks

3. **Configure Settings** (Optional)
   - Click "Settings" to adjust algorithm parameters
   - Modify ATR multiplier, EMA thresholds, etc.

4. **Start the Scan**
   - Click "Start Scan" button
   - Monitor progress bar for completion

5. **Review Results**
   - View signals in the results table
   - Sort by confidence, symbol, or signal type
   - Click on signals for detailed information

### Running a Backtest

1. **Navigate to Backtest Interface**
   - Click on the "Backtest" tab

2. **Configure Parameters**
   - Select start and end dates
   - Enter stock symbols to test
   - Adjust algorithm settings if needed

3. **Execute Backtest**
   - Click "Run Backtest"
   - Wait for processing to complete

4. **Analyze Results**
   - Review performance metrics (win rate, returns, drawdown)
   - Examine individual trades
   - View equity curve and performance charts

### Viewing History

1. **Access History Tab**
   - Click on "History" in the navigation

2. **Filter Results**
   - Filter by date range, symbol, or result type
   - Use search functionality for specific results

3. **View Details**
   - Click on any historical result for full details
   - Export results for external analysis

## ⚙️ Configuration

### Algorithm Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| ATR Multiplier | 2.0 | Controls ATR line distance from EMA21 |
| EMA5 Rising Threshold | 0.02 | Minimum slope for EMA5 to be "rising" |
| EMA8 Rising Threshold | 0.01 | Minimum slope for EMA8 to be "rising" |
| EMA21 Rising Threshold | 0.005 | Minimum slope for EMA21 to be "rising" |
| Volatility Filter | 1.5 | Filters stocks with excessive volatility |
| FOMO Filter | 1.0 | Prevents entering overextended moves |
| Higher Timeframe | 15m | Timeframe for confirmation signals |

### Environment Configuration

**Backend (.env):**
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/stock_scanner
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=stock_scanner
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# External APIs
YFINANCE_TIMEOUT=30
YFINANCE_RETRY_COUNT=3

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env.local):**
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
```

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd backend
python -m pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test -- --coverage
```

### Specific Test Types
```bash
# Unit tests only
python -m pytest tests/ -v -m "not integration"

# Integration tests
python -m pytest tests/ -v -m integration

# Performance tests
python -m pytest tests/test_performance.py -v -m performance
```

### Test Coverage
- **Backend**: 80%+ code coverage required
- **Frontend**: 70%+ code coverage required
- **Integration**: End-to-end workflow testing
- **Performance**: Load and stress testing

## 🐳 Docker Deployment

### Quick Start with Docker
```bash
# Clone and start with Docker Compose
git clone https://github.com/znyinc/scanner.git
cd scanner
docker-compose up -d
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Azure Cloud Deployment

The Stock Scanner supports multiple Azure deployment options with built-in scaling capabilities:

### Azure Deployment Options

| Option | Use Case | Scaling | Complexity | Cost |
|--------|----------|---------|------------|------|
| **Container Instances** | Dev/Test, Simple deployments | Manual | Low | $ |
| **App Service** | Production web apps | Automatic | Medium | $$ |
| **Kubernetes (AKS)** | Enterprise, Microservices | Advanced | High | $$$ |

### Quick Azure Deployment

```bash
# Deploy to Azure App Service (Recommended)
az login
git clone https://github.com/znyinc/scanner.git
cd scanner/terraform
terraform init
terraform apply -var-file="terraform.tfvars.prod"
```

### Azure Auto-scaling Features

- **App Service Auto-scaling**: Based on CPU, memory, and HTTP queue length
- **AKS Horizontal Pod Autoscaler**: Kubernetes-native scaling
- **Azure Database Scaling**: Automatic storage and compute scaling
- **Load Balancing**: Azure Application Gateway and Front Door
- **Global Distribution**: Multi-region deployment support

For detailed Azure deployment instructions, see [Azure Deployment Guide](docs/AZURE_DEPLOYMENT_GUIDE.md).

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete user documentation with algorithm explanation |
| [API Documentation](docs/API_DOCUMENTATION.md) | REST API reference and examples |
| [Code Documentation](docs/CODE_DOCUMENTATION.md) | Technical architecture and code documentation |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Production deployment and setup instructions |
| [Azure Deployment Guide](docs/AZURE_DEPLOYMENT_GUIDE.md) | Azure cloud deployment with scaling capabilities |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   PostgreSQL    │
│                 │    │                 │    │    Database     │
│  - Components   │◄──►│  - REST API     │◄──►│                 │
│  - Services     │    │  - Business     │    │  - Scan Results │
│  - State Mgmt   │    │    Logic        │    │  - Backtests    │
│  - UI/UX        │    │  - Data Access  │    │  - Settings     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  yfinance API   │
                       │  Market Data    │
                       └─────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Material-UI for components
- Chart.js for visualizations
- Axios for API communication

**Backend:**
- FastAPI with Python 3.9+
- SQLAlchemy for database ORM
- Pandas for data processing
- yfinance for market data

**Database:**
- PostgreSQL 13+ with JSONB support
- Optimized indexes for performance
- Connection pooling

**DevOps:**
- Docker containers
- GitHub Actions CI/CD
- Automated testing pipeline
- Performance monitoring

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Commit your changes**
   ```bash
   git commit -m 'feat: add amazing feature'
   ```

5. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Provide clear description
   - Include test results
   - Reference any related issues

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint for TypeScript
- **Testing**: Maintain 80%+ test coverage
- **Documentation**: Update docs for any API changes
- **Performance**: Consider performance impact of changes

## 📈 Performance

### Benchmarks
- **Scan Performance**: 100 stocks in <30 seconds
- **Backtest Performance**: 20 stocks, 35 days in <60 seconds
- **API Response Time**: <5 seconds for typical requests
- **Memory Usage**: <500MB for large scans

### Optimization Features
- **Caching**: Redis caching for market data
- **Connection Pooling**: Database connection optimization
- **Async Processing**: Non-blocking I/O operations
- **Query Optimization**: Indexed database queries

## 🔒 Security

- **Input Validation**: All user inputs validated
- **SQL Injection Protection**: Parameterized queries
- **CORS Configuration**: Proper cross-origin settings
- **Rate Limiting**: API rate limiting implemented
- **Error Handling**: Secure error messages

## 📊 Monitoring

- **Application Logs**: Structured logging with rotation
- **Performance Metrics**: Response time and throughput monitoring
- **Error Tracking**: Comprehensive error logging
- **Health Checks**: Automated health monitoring

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/znyinc/scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/znyinc/scanner/discussions)
- **Documentation**: Check the [docs](docs/) directory
- **Email**: Contact the development team

## 🙏 Acknowledgments

- **yfinance**: For providing market data API
- **FastAPI**: For the excellent web framework
- **React**: For the powerful frontend framework
- **PostgreSQL**: For robust data storage
- **Contributors**: Thanks to all contributors who help improve this project

---

**⭐ Star this repository if you find it useful!**