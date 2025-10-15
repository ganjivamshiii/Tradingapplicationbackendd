from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import init_db

# Import routers
from .api.routes import market_data, strategies, backtesting, portfolio, trades, auth
from .api.routes.websockets import websocket_endpoint, websocket_portfolio_endpoint

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Algo Trading System with Live Data & Backtesting"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"🚀 {settings.APP_NAME} started successfully!")
    print(f"📊 Database initialized")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(backtesting.router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(trades.router, prefix="/api/trades", tags=["Trades"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Algo Trading System API",
        "version": settings.VERSION,
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket endpoints
@app.websocket("/ws/price/{symbol}")
async def websocket_price(websocket: WebSocket, symbol: str):
    """WebSocket for live price updates"""
    await websocket_endpoint(websocket, symbol)

@app.websocket("/ws/portfolio/{strategy}")
async def websocket_portfolio(websocket: WebSocket, strategy: str):
    """WebSocket for portfolio updates"""
    await websocket_portfolio_endpoint(websocket, strategy)

# C:\Users\vamsh\hftprojectassignment\.venv\Scripts\activate
