# Project Structure

## Root Directory Layout
```
├── backend/           # FastAPI Python backend
├── frontend/          # React TypeScript frontend
├── docs/             # Project documentation
├── scripts/          # Deployment and utility scripts
├── nginx/            # Nginx configuration
├── .kiro/            # Kiro AI assistant configuration
├── docker-compose.yml # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
└── Makefile          # Build and deployment commands
```

## Backend Structure (`backend/`)
```
backend/
├── app/              # Main application package
│   ├── main.py       # FastAPI application entry point
│   ├── config.py     # Configuration settings
│   ├── models/       # SQLAlchemy database models
│   ├── routers/      # API route handlers
│   ├── services/     # Business logic services
│   └── utils/        # Utility functions
├── database/         # Database initialization and migrations
├── tests/            # Test files (pytest)
├── logs/             # Application logs
├── requirements.txt  # Python dependencies
├── run_server.py     # Development server script
├── start_backend.bat # Windows startup script
└── .env              # Environment configuration
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── components/   # Reusable React components
│   ├── pages/        # Page-level components
│   ├── services/     # API service functions
│   ├── hooks/        # Custom React hooks
│   ├── types/        # TypeScript type definitions
│   ├── utils/        # Utility functions
│   └── App.tsx       # Main application component
├── public/           # Static assets
├── package.json      # Node.js dependencies and scripts
└── .env.local        # Frontend environment variables
```

## Key Configuration Files

### Environment Files
- `backend/.env` - Backend configuration (database, API keys)
- `frontend/.env.local` - Frontend configuration (API URLs)
- `.env.example` - Template for environment setup

### Docker Files
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `backend/Dockerfile` - Backend container definition
- `frontend/Dockerfile` - Frontend container definition

### Database Files
- `backend/database/init.sql` - Database initialization
- `setup_postgres.sql` - PostgreSQL setup script
- `backend/stock_scanner.db` - SQLite fallback database

## Documentation Structure (`docs/`)
- `API_DOCUMENTATION.md` - REST API reference
- `CODE_DOCUMENTATION.md` - Technical architecture
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `USER_GUIDE.md` - End-user documentation

## Naming Conventions

### Python (Backend)
- **Files**: snake_case (e.g., `stock_scanner.py`)
- **Classes**: PascalCase (e.g., `StockScanner`)
- **Functions/Variables**: snake_case (e.g., `get_stock_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

### TypeScript (Frontend)
- **Files**: camelCase or PascalCase for components (e.g., `StockScanner.tsx`)
- **Components**: PascalCase (e.g., `StockScanner`)
- **Functions/Variables**: camelCase (e.g., `getStockData`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

### Database
- **Tables**: snake_case (e.g., `scan_results`)
- **Columns**: snake_case (e.g., `created_at`)

## Import Organization

### Python
```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
import pandas as pd
from fastapi import FastAPI

# Local imports
from app.models import StockData
from app.services import ScannerService
```

### TypeScript
```typescript
// React imports
import React from 'react';
import { useState, useEffect } from 'react';

// Third-party imports
import { Button } from '@mui/material';
import axios from 'axios';

// Local imports
import { StockData } from '../types';
import { stockService } from '../services';
```

## Testing Structure
- Backend tests in `backend/tests/` mirror the `app/` structure
- Frontend tests co-located with components (`.test.tsx` files)
- Integration tests in dedicated directories
- Test coverage requirements: Backend 80%+, Frontend 70%+