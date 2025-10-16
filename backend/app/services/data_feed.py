import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict
import asyncio
import requests
import time

class DataFeed:
    """Service to fetch market data from Yahoo Finance and other sources."""

    def __init__(self):
        self.cache = {}
        
        # Create a custom session with headers to bypass Yahoo Finance blocking
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

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
        """Fetch historical OHLCV data with retry logic."""
        symbol = self._normalize_symbol(symbol)
        
        print(f"📊 [DataFeed] Fetching historical data for {symbol} (period={period}, interval={interval})")
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create ticker with custom session to avoid blocking
                ticker = yf.Ticker(symbol, session=self.session)
                
                # Fetch historical data with timeout
                df = ticker.history(
                    period=period, 
                    interval=interval,
                    timeout=20,
                    raise_errors=True
                )

                if df.empty:
                    print(f"⚠️ [DataFeed] Attempt {attempt + 1}/{max_retries}: No data returned for {symbol}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ [DataFeed] No historical data found for {symbol} after {max_retries} attempts")
                        return pd.DataFrame()

                # Data found, process it
                print(f"✅ [DataFeed] Raw data received: {len(df)} rows for {symbol}")
                
                # Reset index to make date/datetime a column
                df = df.reset_index()
                
                # Remove any rows with NaN values
                rows_before = len(df)
                df = df.dropna()
                if len(df) < rows_before:
                    print(f"🧹 [DataFeed] Removed {rows_before - len(df)} rows with NaN values")
                
                # Replace infinity values with 0
                df = df.replace([float('inf'), float('-inf')], 0)
                
                # Normalize column names to lowercase
                df.columns = [col.lower() for col in df.columns]
                
                # Rename date/datetime column to timestamp
                if 'date' in df.columns:
                    df.rename(columns={'date': 'timestamp'}, inplace=True)
                elif 'datetime' in df.columns:
                    df.rename(columns={'datetime': 'timestamp'}, inplace=True)
                
                print(f"✅ [DataFeed] Successfully processed {len(df)} rows for {symbol}")
                print(f"📋 [DataFeed] Columns: {df.columns.tolist()}")
                
                return df

            except Exception as e:
                error_msg = str(e)
                print(f"❌ [DataFeed] Attempt {attempt + 1}/{max_retries} failed for {symbol}: {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"⏳ [DataFeed] Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ [DataFeed] All attempts failed for {symbol}")
                    import traceback
                    print(f"📋 [DataFeed] Full traceback:\n{traceback.format_exc()}")
                    return pd.DataFrame()
        
        return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Fetch latest price for a symbol."""
        symbol = self._normalize_symbol(symbol)
        
        print(f"💰 [DataFeed] Fetching latest price for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            
            # Try to get intraday data first
            data = ticker.history(period="1d", interval="1m", timeout=15)

            if data.empty:
                # Fallback to daily data
                print(f"⚠️ [DataFeed] No intraday data, trying daily data for {symbol}")
                data = ticker.history(period="5d", timeout=15)

            if data.empty:
                print(f"❌ [DataFeed] No price data available for {symbol}")
                return None

            price = float(data['Close'].iloc[-1])
            print(f"✅ [DataFeed] Latest price for {symbol}: ${price:.2f}")
            return price

        except Exception as e:
            print(f"❌ [DataFeed] Error fetching latest price for {symbol}: {e}")
            return None

    def get_realtime_data(self, symbol: str) -> Optional[Dict]:
        """Get latest real-time data."""
        symbol = self._normalize_symbol(symbol)
        
        print(f"📡 [DataFeed] Fetching real-time data for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            
            # Try intraday data
            hist = ticker.history(period="1d", interval="1m", timeout=15)

            if hist.empty:
                # Fallback to daily data
                print(f"⚠️ [DataFeed] No intraday data, using daily for {symbol}")
                hist = ticker.history(period="5d", timeout=15)

            if hist.empty:
                print(f"❌ [DataFeed] No real-time data available for {symbol}")
                return None

            latest = hist.iloc[-1]
            
            # Calculate change safely
            change = float(latest['Close'] - latest['Open'])
            change_percent = 0.0
            if latest['Open'] != 0:
                change_percent = float((latest['Close'] - latest['Open']) / latest['Open'] * 100)

            result = {
                'symbol': symbol,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'timestamp': latest.name.isoformat() if hasattr(latest.name, "isoformat") else str(latest.name),
                'change': change,
                'change_percent': change_percent
            }
            
            print(f"✅ [DataFeed] Real-time data for {symbol}: ${result['price']:.2f} ({result['change_percent']:+.2f}%)")
            return result

        except Exception as e:
            print(f"❌ [DataFeed] Error fetching realtime data for {symbol}: {e}")
            import traceback
            print(f"📋 [DataFeed] Traceback:\n{traceback.format_exc()}")
            return None

    async def stream_price_updates(self, symbol: str, interval: int = 5):
        """Async generator to stream real-time price updates."""
        symbol = self._normalize_symbol(symbol)
        
        print(f"🔄 [DataFeed] Starting price stream for {symbol} (interval={interval}s)")
        
        while True:
            try:
                data = self.get_realtime_data(symbol)
                if data:
                    yield data
                else:
                    print(f"⚠️ [DataFeed] No data in stream for {symbol}, will retry...")
                    
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"❌ [DataFeed] Error in price stream for {symbol}: {e}")
                await asyncio.sleep(interval)

    def get_multiple_symbols(
        self, symbols: List[str], period: str = "1mo", interval: str = "1d"
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """Fetch historical data for multiple symbols."""
        print(f"📊 [DataFeed] Fetching data for {len(symbols)} symbols: {symbols}")
        
        result = {}
        
        for idx, symbol in enumerate(symbols, 1):
            print(f"🔄 [DataFeed] Processing {idx}/{len(symbols)}: {symbol}")
            
            df = self.get_historical_data(symbol, period, interval)
            result[symbol] = df if not df.empty else None
            
            # Small delay between requests to avoid rate limiting
            if idx < len(symbols):
                time.sleep(0.5)
        
        successful = sum(1 for v in result.values() if v is not None)
        print(f"✅ [DataFeed] Successfully fetched {successful}/{len(symbols)} symbols")
        
        return result

# Singleton instance
data_feed = DataFeed()