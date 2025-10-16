from fastapi import APIRouter, Body, HTTPException, Query
from typing import List, Optional
from ...services.data_feed import data_feed
from ...schemas.market_data import(
    MarketDataRequest,
    MarketDataResponse,
    OHLCV
)
import traceback
import pandas as pd

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
        print(f"📊 [Route] Fetching {symbol}, period={period}, interval={interval}")
        
        # Get data from service
        data = data_feed.get_historical_data(symbol, period, interval)
        
        # Check if data is empty
        if data is None or data.empty:
            print(f"⚠️ [Route] No data returned for {symbol}")
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for symbol {symbol}"
            )
        
        print(f"✅ [Route] Data received: {len(data)} rows")
        print(f"📋 [Route] Columns: {data.columns.tolist()}")
        
        ohlcv_data = []
        
        for idx, row in data.iterrows():
            try:
                # Handle timestamp conversion
                timestamp = row['timestamp']
                if pd.isna(timestamp):
                    print(f"⚠️ [Route] Skipping row {idx}: timestamp is NaN")
                    continue
                
                # Convert timestamp to string if needed
                if hasattr(timestamp, 'isoformat'):
                    timestamp_str = timestamp.isoformat()
                else:
                    timestamp_str = str(timestamp)
                
                # Check for NaN values and skip invalid rows
                if any(pd.isna(row[col]) for col in ['open', 'high', 'low', 'close', 'volume']):
                    print(f"⚠️ [Route] Skipping row {idx}: contains NaN values")
                    continue
                
                ohlcv_data.append(OHLCV(
                    timestamp=timestamp_str,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                ))
            except Exception as row_error:
                print(f"❌ [Route] Error processing row {idx}: {str(row_error)}")
                print(f"📋 [Route] Row data: {row.to_dict()}")
                continue
        
        if not ohlcv_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No valid data could be processed for {symbol}"
            )
        
        print(f"✅ [Route] Successfully processed {len(ohlcv_data)} data points")
        
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": ohlcv_data,
            "count": len(ohlcv_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ [Route] ERROR: {error_msg}")
        print(f"📋 [Route] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=400, 
            detail=f"Error fetching data: {error_msg}"
        )


@router.get("/live/{symbol}")
async def get_live_data(symbol: str):
    """
    Get real-time data for a symbol
    """
    try:
        print(f"📡 [Route] Fetching live data for {symbol}")
        data = data_feed.get_realtime_data(symbol)
        
        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No real-time data available for {symbol}"
            )
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Route] Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/price/{symbol}")
async def get_latest_price(symbol: str):
    """
    Get the latest price for a symbol
    """
    try:
        print(f"💰 [Route] Fetching price for {symbol}")
        price = data_feed.get_latest_price(symbol)
        
        if price is None:
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for {symbol}"
            )
        
        return {
            "symbol": symbol,
            "latest_price": price
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Route] Error: {str(e)}")
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
        print(f"📊 [Route] Fetching multiple symbols: {symbols}")
        result = data_feed.get_multiple_symbols(symbols, period, interval)
        response = {}
        
        for symbol, data in result.items():
            if data is not None and not data.empty:
                ohlcv_data = []
                for idx, row in data.iterrows():
                    try:
                        # Skip rows with NaN values
                        if any(pd.isna(row[col]) for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']):
                            continue
                        
                        timestamp = row['timestamp']
                        if hasattr(timestamp, 'isoformat'):
                            timestamp_str = timestamp.isoformat()
                        else:
                            timestamp_str = str(timestamp)
                        
                        ohlcv_data.append(OHLCV(
                            timestamp=timestamp_str,
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close']),
                            volume=int(row['volume'])
                        ))
                    except Exception as row_error:
                        print(f"⚠️ [Route] Skipping row for {symbol}: {str(row_error)}")
                        continue
                
                response[symbol] = ohlcv_data if ohlcv_data else None
            else:
                response[symbol] = None
        
        return response
        
    except Exception as e:
        print(f"❌ [Route] Error: {str(e)}")
        print(f"📋 [Route] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))