from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json
from ...services.data_feed import data_feed


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for live price updates
    Usage: ws://localhost:8000/ws/price/{symbol}
    """
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to live feed for {symbol}",
            "symbol": symbol
        })

        # Stream price updates
        async for price_data in data_feed.stream_price_updates(symbol, interval=5):
            await websocket.send_json({
                "type": "price_update",
                "data": price_data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket disconnected from {symbol} feed")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")


async def websocket_portfolio_endpoint(websocket: WebSocket, strategy: str):
    """
    WebSocket endpoint for portfolio updates
    Usage: ws://localhost:8000/ws/portfolio/{strategy}
    """
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to portfolio feed for {strategy}",
            "strategy": strategy
        })
        while True:
            await asyncio.sleep(10)
            await websocket.send_json({
                "type": "heartBeat",
                "timestamp": str(asyncio.get_event_loop().time())
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected from portfolio feed")
    except Exception as e:
        print(f"WebSocket error in portfolio feed: {str(e)}")
        manager.disconnect(websocket)
