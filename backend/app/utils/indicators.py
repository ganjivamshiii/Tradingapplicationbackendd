import pandas as pd
import numpy as np

def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2):
    """Calculate Bollinger Bands"""
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return {
        'sma': sma,
        'upper_band': upper_band,
        'lower_band': lower_band
    }

def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr
