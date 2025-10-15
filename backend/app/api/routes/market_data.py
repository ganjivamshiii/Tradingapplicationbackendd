from fastapi import APIRouter, Body, HTTPException, Query
from typing import List, Optional
from ...services.data_feed import data_feed
from ...schemas.market_data import(
    MarketDataRequest,
    MarketDataResponse,
    OHLCV
)
router = APIRouter()

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = Query(default="1mo", description="1d, 5d, 1mo, 3mo, 6mo,1y, 2y,5y"),
    interval: str = Query(default="1d", description="1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk")
):
    """
    Get historical market data for a symbol
    - **symbol**: Stock ticker (e.g., AAPL, GOOGL, TSLA)
    - **period**: Time period for data
    - **interval**: Data interval/frequency
    """
    try:
        # Fixed typo in method name
        data = data_feed.get_historical_data(symbol, period, interval)
        ohlcv_data = []
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
            
        for _, row in data.iterrows():
            ohlcv_data.append(OHLCV(
                timestamp=row['timestamp'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),  # Fixed typo
                close=float(row['close']),
                volume=int(row['volume'])  # Fixed typo
            ))
        return {
            "symbol": symbol,  # Fixed typo
            "period": period,
            "interval": interval,
            "data": ohlcv_data,
            "count": len(ohlcv_data)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/live/{symbol}")
async def get_live_data(symbol: str):  # Fixed parameter name typo
    """
    Get real-time data for a symbol
    """
    try:
        data = data_feed.get_realtime_data(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/price/{symbol}")  # Added missing slash
async def get_latest_price(symbol: str):
    """
    Get the latest price for a symbol
    """
    try:
        price = data_feed.get_latest_price(symbol)
        return {
            "symbol": symbol,
            "latest_price": price
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/multiple")
async def get_multiple_historical_data(
    symbols: List[str] = Body(..., example=["AAPL","MSFT","GOOG"]),
    period: str = Body("1mo", example="1mo"),
    interval: str = Body("1d", example="1d")
):
    """
    Get historical data for multiple symbols
    
    - **symbols**: List of stock tickers
    - **period**: Time period
    - **interval**: Data interval
    """
    try:
        result = data_feed.get_multiple_symbols(symbols, period, interval)
        response = {}
        for symbol, data in result.items():
            if data is not None and not data.empty:
                ohlcv_data = []
                for _, row in data.iterrows():
                    ohlcv_data.append(OHLCV(
                        timestamp=row['timestamp'],
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume'])
                    ))
                response[symbol] = ohlcv_data
            else:
                response[symbol] = None
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))