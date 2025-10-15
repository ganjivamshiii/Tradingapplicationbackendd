from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from ...services.data_feed import data_feed
from ...strategies.ma_crossover import MACrossover
from ...strategies.rsi_strategy import RSIStrategy
from ...strategies.bollinger_bands import BollingerBands
from ...schemas.strategy import StrategyInfo, StrategyListResponse
import numpy as np
router = APIRouter()

# Strategy factory
def get_strategy(strategy_name: str, parameters: Dict[str, Any] = None):
    """Factory function to create strategy instances"""
    parameters = parameters or {}
    
    if strategy_name.upper() == "MA_CROSSOVER":
        return MACrossover(
            short_window=parameters.get('short_window', 20),
            long_window=parameters.get('long_window', 50),
            ma_type=parameters.get('ma_type', 'SMA')
        )
    elif strategy_name.upper() == "RSI":
        return RSIStrategy(
            period=parameters.get('period', 14),
            oversold=parameters.get('oversold', 30),
            overbought=parameters.get('overbought', 70)
        )
    elif strategy_name.upper() == "BOLLINGER_BANDS":
        return BollingerBands(
            period=parameters.get('period', 20),
            std_dev=parameters.get('std_dev', 2)
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

@router.get("/list", response_model=StrategyListResponse)
async def list_strategies():
    """
    Get list of available trading strategies
    """
    strategies = [
        StrategyInfo(
            name="MA_CROSSOVER",
            description="Moving Average Crossover - Buy when short MA crosses above long MA, sell when it crosses below",
            parameters={
                "short_window": 20,
                "long_window": 50,
                "ma_type": "SMA"
            }
        ),
        StrategyInfo(
            name="RSI",
            description="RSI Momentum Strategy - Buy when RSI is oversold, sell when overbought",
            parameters={
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        ),
        StrategyInfo(
            name="BOLLINGER_BANDS",
            description="Mean Reversion Strategy - Buy at lower band, sell at upper band",
            parameters={
                "period": 20,
                "std_dev": 2
            }
        )
    ]
    
    return StrategyListResponse(strategies=strategies)

@router.get("/signals/{symbol}")
async def get_strategy_signals(
    symbol: str,
    strategy: str = Query(..., description="Strategy name"),
    period: str = Query(default="3mo", description="Data period"),
    interval: str = Query(default="1d", description="Data interval"),
    parameters: str = Query(default=None, description="JSON string of parameters")
):
    try:
        import json
        params = json.loads(parameters) if parameters else {}

        # Historical data
        data = data_feed.get_historical_data(symbol, period, interval)

        # Strategy instance
        strategy_instance = get_strategy(strategy, params)

        # Signals
        signals_df = strategy_instance.generate_signals(data)
        signals_summary = strategy_instance.get_signals_summary(data)

        # Replace NaN/inf in DataFrame
        signals_df = signals_df.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Clean signals_summary
        cleaned_summary = []
        for s in signals_summary:
            cleaned_s = {k: 0 if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else v
                         for k, v in s.items()}
            cleaned_summary.append(cleaned_s)

        return {
            "symbol": symbol,
            "strategy": strategy_instance.get_strategy_name(),
            "parameters": strategy_instance.get_parameters(),
            "signals_summary": cleaned_summary,
            "data": signals_df.to_dict('records'),
            "total_signals": len(cleaned_summary)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/analyze/{symbol}")
async def analyze_with_strategy(
    symbol: str,
    strategy: str,
    period: str = "3mo",
    interval: str = "1d"
):
    """
    Analyze a symbol with a specific strategy and return current recommendation
    
    - **symbol**: Stock ticker
    - **strategy**: Strategy name
    - **period**: Time period for analysis
    - **interval**: Data interval
    """
    try:
        # Get historical data
        data = data_feed.get_historical_data(symbol, period, interval)
        
        # Get strategy instance
        strategy_instance = get_strategy(strategy)
        
        # Generate signals
        signals_df = strategy_instance.generate_signals(data)
        
        # Get latest signal
        latest = signals_df.iloc[-1]
        latest_signal = latest.get('signal', 0)
        
        # Get current price
        current_price = data_feed.get_latest_price(symbol)
        
        recommendation = "HOLD"
        if latest_signal == 1:
            recommendation = "BUY"
        elif latest_signal == -1:
            recommendation = "SELL"
        
        return {
            "symbol": symbol,
            "strategy": strategy_instance.get_strategy_name(),
            "current_price": current_price,
            "recommendation": recommendation,
            "timestamp": latest['timestamp'],
            "analysis": {
                "signal": int(latest_signal),
                "indicators": {k: float(v) if isinstance(v, (int, float)) else str(v) 
                              for k, v in latest.items() 
                              if k not in ['timestamp', 'signal', 'position', 'crossover']}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))