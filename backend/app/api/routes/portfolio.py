from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...services.portfolio_manager import PortfolioManager
from ...schemas.portfolio import PortfolioResponse, PortfolioSummary
from ...models.portfolio import Portfolio

router = APIRouter()

@router.get("/{strategy}", response_model=PortfolioSummary)
async def get_portfolio(strategy: str, db: Session = Depends(get_db)):
    """
    Get portfolio summary for a strategy
    
    - **strategy**: Strategy name
    """
    try:
        portfolio_manager = PortfolioManager(db, strategy)
        summary = portfolio_manager.get_portfolio_summary()
        
        return PortfolioSummary(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def list_portfolios(db: Session = Depends(get_db)):
    """
    List all portfolios
    """
    try:
        portfolios = db.query(Portfolio).all()
        
        result = []
        for portfolio in portfolios:
            result.append({
                "strategy": portfolio.strategy,
                "cash": portfolio.cash,
                "equity": portfolio.equity,
                "total_pnl": portfolio.total_pnl,
                "total_trades": portfolio.total_trades,
                "win_rate": portfolio.win_rate
            })
        
        return {"portfolios": result, "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create/{strategy}")
async def create_portfolio(
    strategy: str, 
    initial_capital: float = 100000,
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio for a strategy
    
    - **strategy**: Strategy name
    - **initial_capital**: Starting capital
    """
    try:
        # Check if portfolio already exists
        existing = db.query(Portfolio).filter(Portfolio.strategy == strategy).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Portfolio for {strategy} already exists"
            )
        
        portfolio_manager = PortfolioManager(db, strategy, initial_capital)
        summary = portfolio_manager.get_portfolio_summary()
        
        return {
            "message": f"Portfolio created for {strategy}",
            "portfolio": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{strategy}")
async def delete_portfolio(strategy: str, db: Session = Depends(get_db)):
    """
    Delete a portfolio
    
    - **strategy**: Strategy name
    """
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.strategy == strategy).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio {strategy} not found")
        
        db.delete(portfolio)
        db.commit()
        
        return {"message": f"Portfolio {strategy} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy}/positions")
async def get_positions(strategy: str, db: Session = Depends(get_db)):
    """
    Get current positions for a portfolio
    
    - **strategy**: Strategy name
    """
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.strategy == strategy).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio {strategy} not found")
        
        return {
            "strategy": strategy,
            "positions": portfolio.positions or {},
            "cash": portfolio.cash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))