import pandas as pd
from .base_strategy import BaseStrategy
from ..utils.indicators import calculate_rsi

class RSIStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Momentum Strategy
    
    Buy Signal: RSI crosses below oversold level (typically 30)
    Sell Signal: RSI crosses above overbought level (typically 70)
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI_STRATEGY")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
        self.parameters = {
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
    
    def get_strategy_name(self) -> str:
        return f"RSI_{self.period}_{self.oversold}_{self.overbought}"
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on RSI
        
        Returns:
            DataFrame with additional columns: rsi, signal, position
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
        
        df = data.copy()
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], self.period)
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate signals
        # Buy signal: RSI < oversold (stock is oversold, expect reversal)
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1
        
        # Sell signal: RSI > overbought (stock is overbought, expect reversal)
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1
        
        # Detect signal changes
        df['prev_signal'] = df['signal'].shift(1)
        df['position'] = 0
        
        # Mark entry points (signal changes from 0 or opposite)
        df.loc[(df['signal'] == 1) & (df['prev_signal'] != 1), 'position'] = 1  # BUY
        df.loc[(df['signal'] == -1) & (df['prev_signal'] != -1), 'position'] = -1  # SELL
        
        # Mark crossover points for clarity
        df['crossover'] = df['position']
        
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
                'rsi': row['rsi'],
                'reason': f"RSI crossed {'oversold' if row['crossover'] == 1 else 'overbought'} level"
            })
        
        return signals
    
    def get_current_rsi(self, data: pd.DataFrame) -> float:
        """Get the most recent RSI value"""
        df = self.generate_signals(data)
        return df['rsi'].iloc[-1]