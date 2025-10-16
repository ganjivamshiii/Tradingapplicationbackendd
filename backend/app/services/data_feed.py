import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict
import asyncio

class DataFeed:
    """Service to fetch market data from Yahoo Finance and other sources."""

    def __init__(self):
        self.cache = {}

    def _normalize_symbol(self, symbol: str) -> str:
        """Fix common symbol mistakes like BTCUSD → BTC-USD"""
        mapping = {
            "BTCUSD": "BTC-USD",
            "ETHUSD": "ETH-USD",
            "DOGEUSD": "DOGE-USD",
        }
        return mapping.get(symbol.upper(), symbol.upper())

    def get_historical_data(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        symbol = self._normalize_symbol(symbol)  # Normalize early
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                print(f"No historical data found for {symbol}")
                return pd.DataFrame()

            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]

            if 'date' in df.columns:
                df.rename(columns={'date': 'timestamp'}, inplace=True)
            elif 'datetime' in df.columns:
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)

            return df

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Fetch latest price for a symbol."""
        symbol = self._normalize_symbol(symbol)  # Normalize early
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                data = ticker.history(period="1d")

            if data.empty:
                print(f"No price data available for {symbol}")
                return None

            return float(data['Close'].iloc[-1])

        except Exception as e:
            print(f"Error fetching latest price for {symbol}: {e}")
            return None

    def get_realtime_data(self, symbol: str) -> Optional[Dict]:
        """Get latest real-time data."""
        symbol = self._normalize_symbol(symbol)  # Normalize early
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                hist = ticker.history(period="1d")

            if hist.empty:
                print(f"No real-time data available for {symbol}")
                return None

            latest = hist.iloc[-1]

            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'timestamp': latest.name.isoformat() if hasattr(latest.name, "isoformat") else str(latest.name),
                'change': float(latest['Close'] - latest['Open']),
                'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100)
            }

        except Exception as e:
            print(f"Error fetching realtime data for {symbol}: {e}")
            return None

    async def stream_price_updates(self, symbol: str, interval: int = 5):
        """Async generator to stream real-time price updates."""
        symbol = self._normalize_symbol(symbol)  # Already normalized
        while True:
            try:
                data = self.get_realtime_data(symbol)
                if data:
                    yield data
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Error in price stream for {symbol}: {e}")
                await asyncio.sleep(interval)

    def get_multiple_symbols(
        self, symbols: List[str], period: str = "1mo", interval: str = "1d"
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """Fetch historical data for multiple symbols."""
        result = {}
        for symbol in symbols:
            df = self.get_historical_data(symbol, period, interval)
            result[symbol] = df if not df.empty else None
        return result

# Singleton instance
data_feed = DataFeed()