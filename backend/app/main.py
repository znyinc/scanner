from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import scan, backtest, settings

app = FastAPI(
    title="Stock Scanner API",
    version="1.0.0",
    description="EMA-ATR based stock scanner with backtesting capabilities"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(scan.router)
app.include_router(backtest.router)
app.include_router(settings.router)

@app.get("/")
async def root():
    return {"message": "Stock Scanner API", "version": "1.0.0"}