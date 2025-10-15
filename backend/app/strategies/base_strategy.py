from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Tuple

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.signals = []
        self.parameters = {}
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on the strategy
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional 'signal' column (1=BUY, -1=SELL, 0=HOLD)
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the strategy name"""
        pass
    
    def get_parameters(self) -> Dict:
        """Return strategy parameters"""
        return self.parameters
    
    def set_parameters(self, params: Dict):
        """Set strategy parameters"""
        self.parameters.update(params)
    
    def calculate_positions(self, signals: pd.Series) -> pd.Series:
        """
        Convert signals to positions
        1 = Long position, 0 = No position, -1 = Short position
        """
        positions = signals.copy()
        # Forward fill to maintain positions
        positions = positions.replace(0, pd.NA).fillna(method='ffill').fillna(0)
        return positions
    
    def get_signal_description(self, signal: int) -> str:
        """Get human-readable signal description"""
        if signal == 1:
            return "BUY"
        elif signal == -1:
            return "SELL"
        else:
            return "HOLD"
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate if data has required columns"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)