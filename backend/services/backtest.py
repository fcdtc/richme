"""
Historical backtesting engine for ETF strategies.
"""
import pandas as pd
import logging
from typing import List, Dict
from .data_utils import convert_to_weekly

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Historical backtesting engine"""

    def __init__(self, strategy_engine, initial_capital: float = 100000):
        self.strategy = strategy_engine
        self.initial_capital = initial_capital

    def run(self, data: pd.DataFrame, start_date: str = None, end_date: str = None) -> Dict:
        """
        Run backtest on historical data.

        Simulates trades based on strategy signals, tracking positions,
        P&L, and drawdown.

        Args:
            data: DataFrame with columns [date, open, high, low, close, volume]
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dict with metrics, equity_curve, trades
        """
        # Filter by date range
        if start_date:
            data = data[data['date'] >= start_date]
        if end_date:
            data = data[data['date'] <= end_date]

        # Ensure data is sorted by date (oldest first)
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values('date').reset_index(drop=True)

        logger.info(f"Backtest data: {len(data)} bars, date range: {data['date'].min()} to {data['date'].max()}")

        # Convert to weekly for multi-timeframe
        weekly_data = convert_to_weekly(data)
        logger.info(f"Weekly data: {len(weekly_data)} weeks")

        # Initialize backtest state
        equity = self.initial_capital
        position = 0.0  # Position size in currency
        position_price = 0.0
        trades = []
        equity_curve = []
        current_trade = None

        # Iterate through data (rolling window for indicators)
        min_window = min(60, len(data) - 2)  # Adaptive minimum window

        for i in range(min_window, len(data)):
            current_bar = data.iloc[i]
            window_data = data.iloc[max(0, i-120):i+1]  # 120-bar window
            window_weekly = weekly_data[weekly_data['date'] <= current_bar['date']]

            # Generate signal
            signal = self.strategy.generate_signal(window_data, window_weekly, current_equity=equity)

            # Log first few signals for debugging
            if i < min_window + 5 or signal['signal_type'] != 'hold':
                logger.info(f"Bar {i} ({current_bar['date']}): signal={signal['signal_type']}, "
                           f"strength={signal['signal_strength']:.3f}, position_size={signal['position_size']:.2f}")

            # Record equity
            equity_curve.append({
                'date': str(current_bar['date'].date()) if hasattr(current_bar['date'], 'date') else str(current_bar['date']),
                'value': equity,
                'drawdown': 0.0  # Will calculate later
            })

            # Trading logic
            if signal['signal_type'] == 'buy' and position <= 0:
                # Open long position
                position_size = min(signal['position_size'], equity)
                if position_size > equity * self.strategy.configs['kelly'].get('min_position_pct', 0.05):
                    position = position_size
                    position_price = current_bar['open'] if i == 0 else current_bar['close']
                    entry_date_str = str(current_bar['date'].date()) if hasattr(current_bar['date'], 'date') else str(current_bar['date'])
                    current_trade = {
                        'entry_date': entry_date_str,
                        'entry_price': position_price,
                        'quantity': position / position_price,
                        'position_value': position,
                        'stop_loss': signal['stop_loss'],
                        'signals': signal['signals']
                    }

            elif signal['signal_type'] == 'sell' and position > 0:
                # Close long position
                exit_price = current_bar['close']
                exit_reason = 'signal'

                # Check stop loss
                if current_bar['low'] <= current_trade['stop_loss']:
                    exit_price = current_trade['stop_loss']
                    exit_reason = 'stop_loss'

                # Calculate P&L
                pnl = (exit_price - position_price) * current_trade['quantity']
                pnl_pct = (pnl / current_trade['position_value']) * 100

                exit_date_str = str(current_bar['date'].date()) if hasattr(current_bar['date'], 'date') else str(current_bar['date'])
                trades.append({
                    **current_trade,
                    'exit_date': exit_date_str,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'holding_days': i - data[data['date'] == current_trade['entry_date']].index[0] if current_trade['entry_date'] in data['date'].values else i,
                    'exit_reason': exit_reason
                })

                equity += pnl
                position = 0.0
                current_trade = None

            # Update current trade if in position
            if position > 0 and current_trade:
                # Check stop loss intraday
                if current_bar['low'] <= current_trade['stop_loss']:
                    exit_price = current_trade['stop_loss']
                    pnl = (exit_price - position_price) * current_trade['quantity']
                    pnl_pct = (pnl / current_trade['position_value']) * 100

                    exit_date_str = str(current_bar['date'].date()) if hasattr(current_bar['date'], 'date') else str(current_bar['date'])
                    trades.append({
                        **current_trade,
                        'exit_date': exit_date_str,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'holding_days': i - data[data['date'] == current_trade['entry_date']].index[0] if current_trade['entry_date'] in data['date'].values else i,
                        'exit_reason': 'stop_loss'
                    })

                    equity += pnl
                    position = 0.0
                    current_trade = None

        # Calculate metrics
        metrics = self.calculate_metrics(equity_curve, trades)

        return {
            'metrics': metrics,
            'equity_curve': self._calculate_drawdown(equity_curve),
            'trades': trades
        }

    def calculate_metrics(self, equity_curve: List[Dict], trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics.

        Returns:
            Dict with total return, annualized return, max drawdown,
            sharpe ratio, win rate, avg win/loss, profit factor
        """
        if not equity_curve:
            return {}

        final_equity = equity_curve[-1]['value']
        total_return = (final_equity - self.initial_capital) / self.initial_capital

        # Calculate drawdown
        equity_curve_with_dd = self._calculate_drawdown(equity_curve)
        max_drawdown = min([e['drawdown'] for e in equity_curve_with_dd])

        # Trade statistics
        if not trades:
            return {
                'initial_capital': self.initial_capital,
                'final_capital': final_equity,
                'total_return': total_return,
                'annualized_return': 0.0,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }

        win_trades = [t for t in trades if t['pnl'] > 0]
        loss_trades = [t for t in trades if t['pnl'] <= 0]

        win_rate = len(win_trades) / len(trades) if trades else 0
        avg_win = sum(t['pnl'] for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t['pnl'] for t in loss_trades) / len(loss_trades) if loss_trades else 0

        # Profit factor
        total_profit = sum(t['pnl'] for t in win_trades) if win_trades else 0
        total_loss = abs(sum(t['pnl'] for t in loss_trades)) if loss_trades else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Annualized return (assuming 252 trading days)
        days = len(equity_curve)
        annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0

        # Sharpe ratio (simplified)
        returns = [e['value'] / self.initial_capital - 1 for e in equity_curve[1:]]
        daily_returns = pd.Series(returns)
        sharpe = daily_returns.mean() / daily_returns.std() * (252 ** 0.5) if daily_returns.std() > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_equity,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }

    def _calculate_drawdown(self, equity_curve: List[Dict]) -> List[Dict]:
        """
        Calculate drawdown for each point in equity curve.

        Returns:
            Equity curve with drawdown values
        """
        peak = self.initial_capital
        result = []

        for point in equity_curve:
            if point['value'] > peak:
                peak = point['value']
            drawdown = (point['value'] - peak) / peak
            result.append({
                'date': point['date'],
                'value': point['value'],
                'drawdown': drawdown
            })

        return result

    def generate_signals_for_backtest(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate buy/sell signals for each bar in data.

        Each signal includes: type (buy/sell), price, position_size, stop_loss

        Returns:
            List of signal dictionaries
        """
        signals = []
        weekly_data = convert_to_weekly(data)
        min_window = 60

        for i in range(min_window, len(data)):
            window_data = data.iloc[max(0, i-120):i+1]
            window_weekly = weekly_data[weekly_data['date'] <= data.iloc[i]['date']]

            signal = self.strategy.generate_signal(window_data, window_weekly)

            if signal['signal_type'] in ['buy', 'sell']:
                signals.append({
                    'date': str(data.iloc[i]['date']),
                    'type': signal['signal_type'],
                    'price': data.iloc[i]['close'],
                    'position_size': signal.get('position_size', 0),
                    'stop_loss': signal['stop_loss'],
                    'strength': signal['signal_strength'],
                    'probability': signal['win_probability']
                })

        return signals
