import pandas as pd
from .base_strategy import BaseStrategy
from ..utils.indicators import calculate_sma, calculate_ema

class MACrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy
    
    Buy Signal: When short MA crosses above long MA
    Sell Signal: When short MA crosses below long MA
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50, ma_type: str = "SMA"):
        super().__init__("MA_CROSSOVER")
        self.short_window = short_window
        self.long_window = long_window
        self.ma_type = ma_type.upper()
        
        self.parameters = {
            'short_window': short_window,
            'long_window': long_window,
            'ma_type': ma_type
        }
    
    def get_strategy_name(self) -> str:
        return f"{self.ma_type}_CROSSOVER_{self.short_window}_{self.long_window}"
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on MA crossover
        
        Returns:
            DataFrame with additional columns: short_ma, long_ma, signal, position
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
        
        df = data.copy()
        
        # Calculate moving averages
        if self.ma_type == "SMA":
            df['short_ma'] = calculate_sma(df['close'], self.short_window)
            df['long_ma'] = calculate_sma(df['close'], self.long_window)
        else:  # EMA
            df['short_ma'] = calculate_ema(df['close'], self.short_window)
            df['long_ma'] = calculate_ema(df['close'], self.long_window)
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate signals
        # Buy signal: short MA crosses above long MA
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
        
        # Sell signal: short MA crosses below long MA
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
        
        # Detect actual crossovers (change in signal)
        df['position'] = df['signal'].diff()
        
        # Mark crossover points
        df['crossover'] = 0
        df.loc[df['position'] == 2, 'crossover'] = 1  # Bullish crossover (BUY)
        df.loc[df['position'] == -2, 'crossover'] = -1  # Bearish crossover (SELL)
        
        return df
    
    def get_signals_summary(self, data: pd.DataFrame) -> list:
        """Get list of all buy/sell signals with timestamps"""
        df = self.generate_signals(data)
        
        signals = []
        for idx, row in df[df['crossover'] != 0].iterrows():
            signals.append({
                'timestamp': row['timestamp'],
                'signal': 'BUY' if row['crossover'] == 1 else 'SELL',
                'price': row['close'],
                'short_ma': row['short_ma'],
                'long_ma': row['long_ma']
            })
        
        return signals