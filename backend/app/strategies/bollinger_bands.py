import pandas as pd
from .base_strategy import BaseStrategy
from ..utils.indicators import calculate_bollinger_bands

class BollingerBands(BaseStrategy):
    """
    Bollinger Bands Mean Reversion Strategy
    
    Buy Signal: Price crosses below lower band (oversold)
    Sell Signal: Price crosses above upper band (overbought)
    """
    
    def __init__(self, period: int = 20, std_dev: int = 2):
        super().__init__("BOLLINGER_BANDS")
        self.period = period
        self.std_dev = std_dev
        
        self.parameters = {
            'period': period,
            'std_dev': std_dev
        }
    
    def get_strategy_name(self) -> str:
        return f"BB_{self.period}_{self.std_dev}"
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Bollinger Bands
        
        Returns:
            DataFrame with additional columns: bb_upper, bb_lower, bb_middle, signal, position
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
        
        df = data.copy()
        
        # Calculate Bollinger Bands
        bb = calculate_bollinger_bands(df['close'], self.period, self.std_dev)
        df['bb_middle'] = bb['sma']
        df['bb_upper'] = bb['upper_band']
        df['bb_lower'] = bb['lower_band']
        
        # Calculate bandwidth for additional info
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate signals
        # Buy signal: Price touches or crosses below lower band
        df.loc[df['close'] <= df['bb_lower'], 'signal'] = 1
        
        # Sell signal: Price touches or crosses above upper band
        df.loc[df['close'] >= df['bb_upper'], 'signal'] = -1
        
        # Exit positions when price returns to middle band
        df.loc[(df['close'] >= df['bb_middle']) & (df['signal'].shift(1) == 1), 'signal'] = 0
        df.loc[(df['close'] <= df['bb_middle']) & (df['signal'].shift(1) == -1), 'signal'] = 0
        
        # Detect signal changes
        df['prev_signal'] = df['signal'].shift(1)
        df['position'] = 0
        
        # Mark entry points
        df.loc[(df['signal'] == 1) & (df['prev_signal'] != 1), 'position'] = 1  # BUY
        df.loc[(df['signal'] == -1) & (df['prev_signal'] != -1), 'position'] = -1  # SELL
        
        # Mark crossover points
        df['crossover'] = df['position']
        
        return df
    
    def get_signals_summary(self, data: pd.DataFrame) -> list:
        """Get list of all buy/sell signals with timestamps"""
        df = self.generate_signals(data)
        
        signals = []
        for idx, row in df[df['crossover'] != 0].iterrows():
            if row['crossover'] == 1:
                reason = f"Price ({row['close']:.2f}) touched lower band ({row['bb_lower']:.2f})"
            else:
                reason = f"Price ({row['close']:.2f}) touched upper band ({row['bb_upper']:.2f})"
            
            signals.append({
                'timestamp': row['timestamp'],
                'signal': 'BUY' if row['crossover'] == 1 else 'SELL',
                'price': row['close'],
                'bb_upper': row['bb_upper'],
                'bb_middle': row['bb_middle'],
                'bb_lower': row['bb_lower'],
                'reason': reason
            })
        
        return signals