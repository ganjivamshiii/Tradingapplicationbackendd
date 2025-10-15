from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...services.portfolio_manager import PortfolioManager
from ...schemas.trade import TradeExecute, TradeResponse
from ...core.security import get_current_user
from ...models.trade import Trade, OrderType , OrderStatus
from ...models.user import User

router=APIRouter()

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(trade_request: TradeExecute, db: Session = Depends(get_db), current_user: User = Depends(get_current_user) ):
    """
    Execute a trade (paper trading)
    """
    portfolio_manager = PortfolioManager(db, trade_request.strategy)
    try:
        trade = portfolio_manager.execute_trade(
            symbol=trade_request.symbol,
            order_type=trade_request.order_type,
            quantity=trade_request.quantity
        )
        return trade

    except ValueError as e:
        # Likely insufficient cash or positions
        print("ValueError:", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Any unexpected error
        print("Unexpected error in execute_trade route:", e)
        raise HTTPException(status_code=500, detail=str(e))

     
@router.get("/history/symbol/{symbol}", response_model=List[TradeResponse])
async def get_symbol_trades(
    symbol: str,
    strategy: Optional[str] = None,
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """
    Get trades for a specific symbol.
    - **symbol**: Stock ticker
    - **strategy**: Optional strategy filter
    - **limit**: Maximum number of trades
    """
    try:
        query = db.query(Trade).filter(Trade.symbol == symbol)
        if strategy:
            query = query.filter(Trade.strategy == strategy)
        trades = query.limit(limit).all()
        return trades  # Must return a list, even if empty
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 2: Get trade statistics for a strategy
@router.get("/stats/{strategy}")
async def get_trade_stats(strategy: str, db: Session = Depends(get_db)):
    """
    Get trading statistics for a strategy.
    - **strategy**: Strategy name
    """
    try:
        trades = db.query(Trade).filter(Trade.strategy == strategy).all()
        if not trades:
            return {
                "strategy": strategy,
                "total_trades": 0,
                "message": "No trades found"
            }

        buy_trades = [t for t in trades if t.order_type == OrderType.BUY]
        sell_trades = [t for t in trades if t.order_type == OrderType.SELL]

        total_pnl = sum(t.pnl for t in sell_trades)
        winning_trades = len([t for t in sell_trades if t.pnl > 0])
        losing_trades = len([t for t in sell_trades if t.pnl < 0])

        avg_win = sum(t.pnl for t in sell_trades if t.pnl > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t.pnl for t in sell_trades if t.pnl < 0) / losing_trades if losing_trades > 0 else 0

        return {
            "strategy": strategy,
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_pnl": total_pnl,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / len(sell_trades) * 100) if sell_trades else 0,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_commission": sum(t.commission for t in trades) / len(trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id, db=Depends(get_db)):
    """
    Get a specific trade by ID
    
    - **trade_id**: Trade ID
    """
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{trade_id}")
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    """
    Delete a trade (for testing purposes)
    
    - **trade_id**: Trade ID
    """
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        db.delete(trade)
        db.commit()
        
        return {"message": f"Trade {trade_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))