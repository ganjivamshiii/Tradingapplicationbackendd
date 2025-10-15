from fastapi import APIRouter, HTTPException
from ...services.data_feed import data_feed
from ...services.backtesting_engine import BacktestingEngine
from ...api.routes.strategies import get_strategy
from ...schemas.strategy import BacktestRequest, BacktestResponse

router = APIRouter()

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on historical data
    
    - **symbol**: Stock ticker to backtest
    - **strategy**: Strategy name (MA_CROSSOVER, RSI, BOLLINGER_BANDS)
    - **period**: Historical period (1mo, 3mo, 6mo, 1y, 2y, 5y)
    - **interval**: Data interval (1d, 1h, etc.)
    - **initial_capital**: Starting capital for backtest
    - **parameters**: Strategy-specific parameters
    """
    try:
        # Get historical data
        data = data_feed.get_historical_data(
            request.symbol, 
            request.period, 
            request.interval
        )
        
        if data.empty:
            raise HTTPException(
                status_code=400, 
                detail=f"No data available for {request.symbol}"
            )
        
        # Get strategy instance
        strategy = get_strategy(request.strategy, request.parameters)
        
        # Create backtesting engine
        backtest_engine = BacktestingEngine(
            strategy=strategy,
            initial_capital=request.initial_capital
        )
        
        # Run backtest
        results = backtest_engine.run(data)
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@router.get("/compare/{symbol}")
async def compare_strategies(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    initial_capital: float = 100000
):
    """
    Compare all available strategies on the same data
    
    - **symbol**: Stock ticker
    - **period**: Historical period
    - **interval**: Data interval
    - **initial_capital**: Starting capital
    """
    try:
        # Get historical data
        data = data_feed.get_historical_data(symbol, period, interval)
        
        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No data available for {symbol}"
            )
        
        # List of strategies to compare
        strategies_to_test = [
            ("MA_CROSSOVER", {}),
            ("RSI", {}),
            ("BOLLINGER_BANDS", {})
        ]
        
        results = []
        
        for strategy_name, params in strategies_to_test:
            try:
                strategy = get_strategy(strategy_name, params)
                backtest_engine = BacktestingEngine(
                    strategy=strategy,
                    initial_capital=initial_capital
                )
                result = backtest_engine.run(data)
                
                # Add summary for comparison
                results.append({
                    "strategy": result['strategy'],
                    "total_return": result['total_return'],
                    "total_return_percent": result['total_return_percent'],
                    "win_rate": result['win_rate'],
                    "sharpe_ratio": result['sharpe_ratio'],
                    "max_drawdown": result['max_drawdown'],
                    "total_trades": result['total_trades']
                })
                
            except Exception as e:
                print(f"Error backtesting {strategy_name}: {str(e)}")
                continue
        
        # Sort by total return
        results.sort(key=lambda x: x['total_return_percent'], reverse=True)
        
        return {
            "symbol": symbol,
            "period": period,
            "initial_capital": initial_capital,
            "strategies": results,
            "best_strategy": results[0] if results else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{symbol}")
async def get_backtest_metrics(
    symbol: str,
    strategy: str,
    period: str = "1y"
):
    """
    Get detailed metrics for a strategy backtest
    
    - **symbol**: Stock ticker
    - **strategy**: Strategy name
    - **period**: Historical period
    """
    try:
        data = data_feed.get_historical_data(symbol, period, "1d")
        
        strategy_instance = get_strategy(strategy)
        backtest_engine = BacktestingEngine(strategy=strategy_instance)
        
        results = backtest_engine.run(data)
        
        return {
            "symbol": symbol,
            "strategy": results['strategy'],
            "metrics": results['metrics'],
            "summary": {
                "initial_capital": results['initial_capital'],
                "final_value": results['final_portfolio_value'],
                "total_return": results['total_return'],
                "total_return_percent": results['total_return_percent'],
                "total_trades": results['total_trades'],
                "winning_trades": results['winning_trades'],
                "losing_trades": results['losing_trades']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))