import pandas as pd
import numpy as np
from typing import Dict
from ..strategies.base_strategy import BaseStrategy
from ..core.config import settings


class BacktestingEngine:
    """
    Backtesting engine to test trading strategies on historical data
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = None,
        commission: float = None
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital or settings.INITIAL_CAPITAL
        self.commission_rate = commission or settings.COMMISSION

        self.trades = []
        self.equity_curve = []
        self.portfolio_value = self.initial_capital
        self.cash = self.initial_capital
        self.positions = {}

    def run(self, data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data
        """
        self.trades = []
        self.equity_curve = []
        self.portfolio_value = self.initial_capital
        self.cash = self.initial_capital
        self.positions = {}

        df = self.strategy.generate_signals(data)

        for idx, row in df.iterrows():
            timestamp = row['timestamp']
            price = row['close']
            signal = row.get('crossover', 0)

            if signal == 1:
                self._execute_trade(timestamp, price, row)
            elif signal == -1:
                self._execute_sell(timestamp, price, row)

            portfolio_value = self._calculate_portfolio_value(price)
            self.equity_curve.append({
                'timestamp': pd.to_datetime(timestamp),
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'returns': (portfolio_value - self.initial_capital) / self.initial_capital * 100
            })

        metrics = self._calculate_metrics()

        # Return all fields at top level to match BacktestResponse
        return {
            'strategy': self.strategy.get_strategy_name(),
            'initial_capital': self.initial_capital,
            'final_portfolio_value': self.portfolio_value,
            'total_return': metrics.get('total_return', 0),
            'total_return_percent': metrics.get('total_return_percent', 0),
            'trades': self.trades,
            'total_trades': len(self.trades),
            'winning_trades': metrics.get('winning_trades', 0),
            'losing_trades': metrics.get('losing_trades', 0),
            'win_rate': metrics.get('win_rate', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'equity_curve': self.equity_curve,
            'metrics': metrics  # optional, keep for extra info
        }

    def _execute_trade(self, timestamp: str, price: float, row: pd.Series):
        symbol = 'STOCK'
        investment = self.cash * 0.9
        commission = investment * self.commission_rate
        quantity = (investment - commission) / price
        if quantity <= 0:
            return
        total_cost = (price * quantity) + commission
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity

            trade = {
                'timestamp': timestamp,
                'symbol': symbol,
                'type': 'BUY',               # required by model
                'order_type': 'BUY',
                'price': price,
                'quantity': quantity,
                'commission': commission,
                'total': total_cost,
                'cash_after': self.cash,
                'pnl': 0                     # pnl is 0 on buy
            }
            self.trades.append(trade)

    def _execute_sell(self, timestamp: str, price: float, row: pd.Series):
        symbol = 'STOCK'
        quantity = self.positions.get(symbol, 0)
        if quantity <= 0:
            return
        commission = (price * quantity) * self.commission_rate
        total_proceed = (price * quantity) - commission
        self.cash += total_proceed
        self.positions[symbol] = 0

        # Calculate pnl for this trade
        last_buy = next((t for t in reversed(self.trades) if t['symbol'] == symbol and t['order_type'] == 'BUY'), None)
        buy_price = last_buy['price'] if last_buy else price
        pnl = (price - buy_price) * quantity - commission

        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': 'SELL',              # required by model
            'order_type': 'SELL',
            'price': price,
            'quantity': quantity,
            'commission': commission,
            'total': total_proceed,
            'cash_after': self.cash,
            'pnl': pnl                   # profit/loss of this trade
        }
        self.trades.append(trade)


    def _calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate current portfolio value"""
        symbol = 'STOCK'
        position_value = self.positions.get(symbol, 0) * current_price
        total_value = self.cash + position_value
        self.portfolio_value = total_value
        return total_value

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.equity_curve:
            return {}

        equity_df = pd.DataFrame(self.equity_curve)

        total_return = self.portfolio_value - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100

        winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
        total_trades = len([t for t in self.trades if 'pnl' in t])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        equity_df['daily_returns'] = equity_df['portfolio_value'].pct_change()

        if len(equity_df) > 1:
            mean_return = equity_df['daily_returns'].mean()
            std_return = equity_df['daily_returns'].std()
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return != 0 else 0
        else:
            sharpe_ratio = 0

        equity_df['cummax'] = equity_df['portfolio_value'].cummax()
        equity_df['drawdown'] = (equity_df['portfolio_value'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min() * 100

        trade_pnls = [t.get('pnl', 0) for t in self.trades if 'pnl' in t]
        avg_trade_pnl = sum(trade_pnls) / len(trade_pnls) if trade_pnls else 0

        winning_pnls = [p for p in trade_pnls if p > 0]
        losing_pnls = [p for p in trade_pnls if p < 0]
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0

        total_wins = sum(winning_pnls) if winning_pnls else 0
        total_losses = abs(sum(losing_pnls)) if losing_pnls else 1
        profit_factor = total_wins / total_losses if total_losses != 0 else 0

        return {
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_trade_pnl': avg_trade_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
