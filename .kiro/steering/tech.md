# Technology Stack

## Architecture
Full-stack application with React frontend, FastAPI backend, and PostgreSQL database.

## Frontend Stack
- **React 18** with TypeScript
- **Material-UI (MUI)** for components and styling
- **Recharts** for data visualizations
- **Axios** for API communication
- **React Router** for navigation

## Backend Stack
- **FastAPI** with Python 3.9+
- **SQLAlchemy** for database ORM
- **Pandas** for data processing
- **yfinance** for market data (primary)
- **AlphaVantage** for market data (fallback)
- **Pydantic v2** for data validation
- **Uvicorn** ASGI server

## Database
- **PostgreSQL 15** with JSONB support
- Optimized indexes for performance
- Connection pooling

## Development Tools
- **pytest** for backend testing
- **Jest** for frontend testing
- **Docker** for containerization
- **ESLint** for code linting

## Common Commands

### Backend Development
```bash
# Setup virtual environment
cd backend
python -m venv venv

# Windows activation
venv\Scripts\activate.bat
# or PowerShell
.\venv\Scripts\Activate.ps1

# Linux/macOS activation
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python run_server.py
# or use convenience script (Windows)
start_backend.bat
```

### Frontend Development
```bash
cd frontend
npm install
npm start          # Development server
npm test           # Run tests
npm run build      # Production build
```

### Database Setup
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Initialize database
cd backend
python app/init_db.py
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test -- --coverage
```

### Docker Deployment
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Build images
docker-compose -f docker-compose.prod.yml build
```

## Environment Configuration
- Backend uses `.env` files for configuration
- Frontend uses `.env.local` for React environment variables
- Database credentials configured via environment variables
- AlphaVantage API key for fallback data source